"""内容校验 Agent：对照知识库片段做一致性检查（fail-closed）。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from services.knowledge.retriever import KnowledgeChunk, format_context_block
from services.llm import chat_completion

_ALGORITHM_WHITELIST = re.compile(
    r"数组|链表|哈希|栈|队列|二叉树|BST|回溯|贪心|动态规划|DP|双指针|单调栈|BFS|DFS|图论|分治|排序|二分",
    re.I,
)
_COMPLEXITY_PATTERN = re.compile(
    r"O\s*\(\s*[\dn\s\*\^log\.]+\s*\)",
    re.I,
)
_LC_FAKE_PATTERN = re.compile(r"力扣\s*\d{4,}|leetcode\s*#?\s*\d{4,}", re.I)

_VERIFY_SYSTEM = """你是「内容校验 Agent」。根据「知识库片段」检查「待发布内容」是否存在明显事实错误或编造题号/外链。
输出 JSON（不要 markdown 代码块）：
{"passed": true/false, "issues": ["问题1"], "warnings": ["提醒1"], "grounded_terms": ["有知识库依据的术语"], "unsupported_claims": ["缺少依据的表述"], "revised_hint": "若未通过，给生成 Agent 一句修改建议，无则空字符串"}
标准：允许教学性简化；不允许编造知识库外的具体力扣/LeetCode 四位题号、虚假 URL、与片段矛盾的复杂度结论。"""


@dataclass
class VerifierStructuredResult:
    status: str
    passed: bool
    grounded_chunk_ids: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    grounded_terms: list[str] = field(default_factory=list)
    hallucination_risks: list[str] = field(default_factory=list)
    unsupported_claims: list[str] = field(default_factory=list)
    revised_hint: str = ""

    def to_display_dict(self) -> dict:
        warnings = list(
            dict.fromkeys(self.warnings + self.hallucination_risks)
        )
        return {
            "passed": self.passed,
            "warnings": warnings,
            "grounded_terms": list(dict.fromkeys(self.grounded_terms)),
            "unsupported_claims": list(dict.fromkeys(self.unsupported_claims)),
        }


class ContentVerifierAgent:
    name = "ContentVerifierAgent"
    role = "生成内容校验"

    async def verify(
        self,
        content: str,
        chunks: list[KnowledgeChunk],
        *,
        topic: str,
    ) -> tuple[bool, str, list[str], str, VerifierStructuredResult]:
        structured, rule_failed = _rule_check_structured(content, chunks, topic=topic)
        citation_ids = structured.grounded_chunk_ids

        footer = ""
        if citation_ids:
            footer = "\n\n---\n**依据知识库**：" + "、".join(citation_ids)

        if rule_failed:
            hint = structured.revised_hint or "；".join(
                structured.hallucination_risks + structured.unsupported_claims
            )
            note = "\n\n> ⚠️ 内容校验提示：" + hint
            return False, content + note + footer, citation_ids, hint, structured

        if not chunks:
            structured.status = "warning"
            structured.unsupported_claims.append("未检索到知识库片段，仅做规则快检")
            return True, content + footer, citation_ids, "", structured

        ctx = format_context_block(chunks)
        user = f"主题：{topic}\n\n知识库片段：\n{ctx}\n\n待发布内容（节选）：\n{content[:3500]}"
        try:
            raw = await chat_completion(
                [{"role": "system", "content": _VERIFY_SYSTEM}, {"role": "user", "content": user}],
                temperature=0.1,
                max_tokens=600,
            )
            data = _parse_json(raw)
            passed = bool(data.get("passed", False))
            issues = [str(x) for x in (data.get("issues") or [])]
            structured.warnings.extend(str(x) for x in (data.get("warnings") or []))
            structured.grounded_terms.extend(
                str(x) for x in (data.get("grounded_terms") or [])
            )
            structured.unsupported_claims.extend(
                str(x) for x in (data.get("unsupported_claims") or [])
            )
            if structured.unsupported_claims:
                passed = False
            hint = str(data.get("revised_hint", "")).strip()
            if passed:
                structured.status = "passed"
                structured.passed = True
                return True, content + footer, citation_ids, "", structured
            structured.status = "failed"
            structured.passed = False
            structured.hallucination_risks.extend(issues)
            structured.revised_hint = hint or "；".join(issues)
            note = "\n\n> ⚠️ 内容校验提示：" + (hint or "；".join(issues) or "请对照知识库修订")
            return False, content + note + footer, citation_ids, structured.revised_hint, structured
        except Exception:
            structured.status = "warning"
            structured.passed = False
            structured.unsupported_claims.append("校验服务暂不可用，标记为待人工复核")
            structured.revised_hint = "校验异常，请对照知识库人工核对"
            return (
                False,
                content + "\n\n> ⚠️ 校验服务暂不可用，内容标记为待校验。" + footer,
                citation_ids,
                structured.revised_hint,
                structured,
            )


def _rule_check_structured(
    content: str,
    chunks: list[KnowledgeChunk],
    *,
    topic: str,
) -> tuple[VerifierStructuredResult, bool]:
    citation_ids = [c["id"] for c in chunks]
    structured = VerifierStructuredResult(
        status="passed",
        passed=True,
        grounded_chunk_ids=citation_ids,
        grounded_terms=_find_grounded_terms(content, chunks),
    )
    failed = False

    if re.search(r"https?://[^\s\]]+\b", content) and not any("http" in c["content"] for c in chunks):
        structured.unsupported_claims.append("含外链但知识库未提供链接")
        failed = True

    for m in _LC_FAKE_PATTERN.finditer(content):
        structured.hallucination_risks.append(f"含可疑高编号力扣题引用：{m.group(0)}")

    kb_text = " ".join(c["content"] + c["title"] for c in chunks)
    for m in _COMPLEXITY_PATTERN.finditer(content):
        claim = m.group(0)
        if claim.lower() not in kb_text.lower() and "O(" in claim:
            if "O(1)" in claim and "哈希" in content and "最坏" not in content and "均摊" not in content:
                structured.hallucination_risks.append(
                    f"复杂度声明 {claim} 可能未说明前提（哈希/均摊）"
                )

    if topic and not _ALGORITHM_WHITELIST.search(content) and len(content) > 200:
        if not any(k in content for k in ("数组", "链表", "树", "栈", "队列", "哈希", "指针", "规划", "贪心")):
            structured.unsupported_claims.append("正文缺少与算法课程相关的明确术语")

    allowed_chapters = re.findall(r"第\s*\d+\s*章", kb_text)
    for ch in re.findall(r"第\s*\d+\s*章", content):
        if allowed_chapters and ch not in allowed_chapters:
            structured.hallucination_risks.append(f"章节引用 {ch} 未在知识库中出现")

    if structured.hallucination_risks or structured.unsupported_claims:
        structured.status = "warning" if not failed else "failed"
        structured.passed = False
        structured.revised_hint = "；".join(
            structured.hallucination_risks + structured.unsupported_claims
        )
        return structured, True

    return structured, failed


def _find_grounded_terms(
    content: str,
    chunks: list[KnowledgeChunk],
    *,
    limit: int = 12,
) -> list[str]:
    candidates: list[str] = []
    for chunk in chunks:
        candidates.extend(str(x) for x in (chunk.get("keywords") or []))
        candidates.extend(
            [
                str(chunk.get("section_title") or chunk.get("section") or ""),
                str(chunk.get("chapter_title") or ""),
            ]
        )
    grounded: list[str] = []
    content_lower = content.lower()
    for term in candidates:
        cleaned = term.strip()
        if len(cleaned) < 2 or cleaned in grounded:
            continue
        if cleaned.lower() in content_lower:
            grounded.append(cleaned)
        if len(grounded) >= limit:
            break
    return grounded


def _parse_json(raw: str) -> dict:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])
    return json.loads(text)


verifier_agent = ContentVerifierAgent()
