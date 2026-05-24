"""内容校验 Agent：对照知识库片段做一致性检查（fail-closed）。"""

from __future__ import annotations

import json
import re

from services.knowledge.retriever import KnowledgeChunk, format_context_block
from services.llm import chat_completion

# 教材/算法名白名单（教学常用表述）
_ALGORITHM_WHITELIST = re.compile(
    r"数组|链表|哈希|栈|队列|二叉树|BST|回溯|贪心|动态规划|DP|双指针|单调栈|BFS|DFS|图论|分治|排序|二分",
    re.I,
)
_COMPLEXITY_PATTERN = re.compile(
    r"O\s*\(\s*[\dn\s\*\^log\.]+\s*\)",
    re.I,
)

_VERIFY_SYSTEM = """你是「内容校验 Agent」。根据「知识库片段」检查「待发布内容」是否存在明显事实错误或编造题号/外链。
输出 JSON（不要 markdown 代码块）：
{"passed": true/false, "issues": ["问题1"], "revised_hint": "若未通过，给生成 Agent 一句修改建议，无则空字符串"}
标准：允许教学性简化；不允许编造知识库外的具体力扣/LeetCode 四位题号、虚假 URL、与片段矛盾的复杂度结论。"""


class ContentVerifierAgent:
    name = "ContentVerifierAgent"
    role = "生成内容校验"

    async def verify(
        self,
        content: str,
        chunks: list[KnowledgeChunk],
        *,
        topic: str,
    ) -> tuple[bool, str, list[str], str]:
        """返回 (passed, final_content, citation_ids, revised_hint)。"""
        citation_ids = [c["id"] for c in chunks]
        footer = ""
        if citation_ids:
            footer = "\n\n---\n**依据知识库**：" + "、".join(citation_ids)

        warnings = _rule_warnings(content, chunks, topic=topic)
        if warnings:
            hint = "；".join(warnings)
            note = "\n\n> ⚠️ 内容校验提示：" + hint
            return False, content + note + footer, citation_ids, hint

        if not chunks:
            return True, content + footer, citation_ids, ""

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
            issues = data.get("issues") or []
            hint = str(data.get("revised_hint", "")).strip()
            if passed:
                return True, content + footer, citation_ids, ""
            note = "\n\n> ⚠️ 内容校验提示：" + ("；".join(issues) if issues else hint or "请对照知识库修订")
            return False, content + note + footer, citation_ids, hint or "；".join(issues)
        except Exception:
            return False, content + "\n\n> ⚠️ 校验服务暂不可用，内容标记为待校验。" + footer, citation_ids, "校验异常，请对照知识库人工核对"


def _rule_warnings(content: str, chunks: list[KnowledgeChunk], *, topic: str) -> list[str]:
    warnings: list[str] = []
    if re.search(r"https?://[^\s\]]+\b", content) and not any("http" in c["content"] for c in chunks):
        warnings.append("含外链但知识库未提供链接")
    if re.search(r"力扣\s*\d{4,}|leetcode\s*#?\s*\d{4,}", content, re.I):
        warnings.append("含可疑高编号力扣题引用")

    kb_text = " ".join(c["content"] + c["title"] for c in chunks)
    for m in _COMPLEXITY_PATTERN.finditer(content):
        claim = m.group(0)
        if claim.lower() not in kb_text.lower() and "O(" in claim:
            if "O(1)" in claim and "哈希" in content and "最坏" not in content and "均摊" not in content:
                warnings.append(f"复杂度声明 {claim} 可能未说明前提（哈希/均摊）")

    if topic and not _ALGORITHM_WHITELIST.search(content) and len(content) > 200:
        if not any(k in content for k in ("数组", "链表", "树", "栈", "队列", "哈希", "指针", "规划", "贪心")):
            warnings.append("正文缺少与算法课程相关的明确术语")

    allowed_chapters = re.findall(r"第\s*\d+\s*章", kb_text)
    for ch in re.findall(r"第\s*\d+\s*章", content):
        if allowed_chapters and ch not in allowed_chapters:
            warnings.append(f"章节引用 {ch} 未在知识库中出现")

    return warnings


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
