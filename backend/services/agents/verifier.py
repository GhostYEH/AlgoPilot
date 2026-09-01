"""内容校验 Agent：对照知识库片段做一致性检查（fail-closed）。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from services.knowledge.retriever import KnowledgeChunk, format_context_block
from services.llm.validator import (
    DEFAULT_MAX_RETRIES,
    chat_completion_validated,
    json_object_validator,
)

_ALGORITHM_WHITELIST = re.compile(
    r"数组|链表|哈希|栈|队列|二叉树|BST|回溯|贪心|动态规划|DP|双指针|单调栈|BFS|DFS|图论|分治|排序|二分",
    re.I,
)
_COMPLEXITY_PATTERN = re.compile(
    r"O\s*\(\s*[\dnmkve\s\*\^\+\-/log\.]+\s*\)",
    re.I,
)
_LC_FAKE_PATTERN = re.compile(r"力扣\s*\d{4,}|leetcode\s*#?\s*\d{4,}", re.I)

_TOPIC_ALIASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("数组", ("数组", "下标")),
    ("链表", ("链表", "指针", "节点")),
    ("哈希", ("哈希", "散列", "键值")),
    ("字符串", ("字符串", "字符")),
    ("双指针", ("双指针", "左右指针", "快慢指针")),
    ("栈", ("栈", "LIFO", "后进先出")),
    ("队列", ("队列", "FIFO", "先进先出")),
    ("排序", ("排序", "稳定性", "比较")),
    ("二叉树", ("二叉树", "树", "节点", "遍历")),
    ("回溯", ("回溯", "撤销", "剪枝")),
    ("贪心", ("贪心", "局部最优")),
    ("动态规划", ("动态规划", "DP", "状态转移")),
    ("单调栈", ("单调栈", "单调性", "出栈")),
    ("图", ("图论", "图", "BFS", "DFS", "顶点", "边")),
)

_VERIFY_SYSTEM = """你是「内容质量校验 Agent」。根据「知识库片段」检查「待发布内容」的正确性与教学价值。
输出 JSON（不要 markdown 代码块）：
{"passed": true/false, "issues": ["问题1"], "warnings": ["提醒1"], "grounded_terms": ["有知识库依据的术语"], "unsupported_claims": ["缺少依据的表述"], "revised_hint": "若未通过，给生成 Agent 一句修改建议，无则空字符串"}
必须同时检查：
1. 核心定义、操作顺序、复杂度、边界条件是否与知识库一致；
2. 是否紧扣指定主题，避免把别的算法内容换标题后混入；
3. 是否具体、可执行、能帮助学生形成理解或完成练习，拒绝空泛套话和同义反复；
4. 讲解是否给出模型、步骤、成立前提与易错点；沙盒是否形成可练习任务；阅读是否有清晰梯度和读后产出；
5. 不允许编造题号、出版物、论文、课程、URL 或知识库没有支持的事实。
允许教学性简化，但简化不能改变结论或省略关键前提。只要存在实质性错误、离题、空泛或不可执行内容，passed 必须为 false。"""


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
        resource_type: str = "",
    ) -> tuple[bool, str, list[str], str, VerifierStructuredResult]:
        structured, rule_failed = _rule_check_structured(
            content, chunks, topic=topic, resource_type=resource_type
        )
        citation_ids = structured.grounded_chunk_ids

        is_structured_payload = _is_json_payload(content)
        footer = ""
        if citation_ids and not is_structured_payload:
            footer = "\n\n---\n**依据知识库**：" + "、".join(citation_ids)

        if rule_failed:
            hint = structured.revised_hint or "；".join(
                structured.hallucination_risks + structured.unsupported_claims
            )
            note = "\n\n> ⚠️ 内容校验提示：" + hint
            checked_content = content if is_structured_payload else content + note + footer
            return False, checked_content, citation_ids, hint, structured

        if not chunks:
            structured.status = "warning"
            structured.unsupported_claims.append("未检索到知识库片段，仅做规则快检")
            return True, content if is_structured_payload else content + footer, citation_ids, "", structured

        ctx = format_context_block(chunks)
        user = (
            f"资源类型：{resource_type or '通用内容'}\n主题：{topic}\n\n"
            f"知识库片段：\n{ctx}\n\n待发布内容（节选）：\n{content[:5000]}"
        )
        try:
            raw, _ = await chat_completion_validated(
                [{"role": "system", "content": _VERIFY_SYSTEM}, {"role": "user", "content": user}],
                validator=json_object_validator(),
                max_retries=DEFAULT_MAX_RETRIES,
                temperature=0.1,
                max_tokens=600,
                retry_temperature=0.25,
                context_label="verifier",
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
                checked_content = content if is_structured_payload else content + footer
                return True, checked_content, citation_ids, "", structured
            structured.status = "failed"
            structured.passed = False
            structured.hallucination_risks.extend(issues)
            structured.revised_hint = hint or "；".join(issues)
            note = "\n\n> ⚠️ 内容校验提示：" + (hint or "；".join(issues) or "请对照知识库修订")
            checked_content = content if is_structured_payload else content + note + footer
            return False, checked_content, citation_ids, structured.revised_hint, structured
        except Exception:
            structured.status = "warning"
            structured.passed = False
            structured.unsupported_claims.append("校验服务暂不可用，标记为待人工复核")
            structured.revised_hint = "校验异常，请对照知识库人工核对"
            return (
                False,
                content if is_structured_payload else content + "\n\n> ⚠️ 校验服务暂不可用，内容标记为待校验。" + footer,
                citation_ids,
                structured.revised_hint,
                structured,
            )


def _rule_check_structured(
    content: str,
    chunks: list[KnowledgeChunk],
    *,
    topic: str,
    resource_type: str = "",
) -> tuple[VerifierStructuredResult, bool]:
    citation_ids = [c["id"] for c in chunks]
    structured = VerifierStructuredResult(
        status="passed",
        passed=True,
        grounded_chunk_ids=citation_ids,
        grounded_terms=_find_grounded_terms(content, chunks),
    )
    failed = False

    topic_terms = _topic_relevance_terms(topic)
    if topic_terms and not any(term.lower() in content.lower() for term in topic_terms):
        structured.unsupported_claims.append(
            f"生成内容未体现课程主题“{topic}”的核心概念"
        )
        failed = True

    quality_issues = _structured_quality_issues(
        content,
        resource_type=resource_type,
        topic=topic,
        chunks=chunks,
    )
    if quality_issues:
        structured.unsupported_claims.extend(quality_issues)
        failed = True

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


def _topic_relevance_terms(topic: str) -> tuple[str, ...]:
    normalized = re.sub(r"\s+", "", topic or "")
    if not normalized or normalized in {"数据结构与算法", "算法", "数据结构"}:
        return ()
    matches = [(marker, aliases) for marker, aliases in _TOPIC_ALIASES if marker in normalized]
    if matches:
        longest = max(len(marker) for marker, _ in matches)
        matched = [alias for marker, aliases in matches if len(marker) == longest for alias in aliases]
        return tuple(dict.fromkeys(matched))
    cleaned = re.sub(r"入门|基础|详解|学习|课程|专题", "", normalized)
    return (cleaned,) if len(cleaned) >= 2 else ()


def _is_json_payload(content: str) -> bool:
    text = content.strip()
    if not (text.startswith("{") or text.startswith("[") or text.startswith("```json")):
        return False
    try:
        _parse_json(text)
        return True
    except (json.JSONDecodeError, TypeError, ValueError):
        return False


def _structured_quality_issues(
    content: str,
    *,
    resource_type: str = "",
    topic: str = "",
    chunks: list[KnowledgeChunk] | None = None,
) -> list[str]:
    """Deterministic publication checks for structured teaching resources."""
    structured_types = {"document", "exercises", "code_case", "reading", "ppt", "video_script"}
    if resource_type in structured_types and not _is_json_payload(content):
        return [f"{resource_type} 必须输出可解析的结构化 JSON，当前内容格式无效"]
    if resource_type == "mindmap":
        lines = [line for line in content.splitlines() if line.strip()]
        if not lines or lines[0].strip() != "mindmap":
            return ["mindmap 必须输出 Mermaid mindmap 源码"]
        issues: list[str] = []
        node_lines = lines[1:]
        if len(node_lines) < 15:
            issues.append("mindmap 节点不足 15 个，知识拓扑不完整")
        if len(node_lines) > 30:
            issues.append("mindmap 节点超过 30 个，缺少重点")
        indents = [len(line) - len(line.lstrip()) for line in node_lines]
        if indents and max(indents) < 6:
            issues.append("mindmap 缺少至少三层的知识展开")
        branch_count = sum(indent == 4 for indent in indents)
        if branch_count < 4:
            issues.append("mindmap 一级知识分支不足 4 个")
        labels = [
            re.sub(r"^root\(\((.*?)\)\)$", r"\1", line.strip())
            for line in node_lines
        ]
        normalized_labels = [re.sub(r"\s+", "", label) for label in labels]
        if len(set(normalized_labels)) != len(normalized_labels):
            issues.append("mindmap 存在重复节点，知识信息密度不足")
        vague = {
            "基本定义", "关键术语", "核心步骤", "操作流程", "适用条件",
            "典型应用", "扩展场景", "常见错误", "边界条件", "复杂度分析",
        }
        if sum(label in vague for label in labels) > 3:
            issues.append("mindmap 通用占位节点过多，未提炼当前主题的具体知识")
        return issues
    if not _is_json_payload(content):
        return []
    data = _parse_json(content)
    issues: list[str] = []

    required_key = {
        "document": "domain_narrative",
        "code_case": "domain_narrative",
        "exercises": "questions",
        "reading": "levels",
    }.get(resource_type)
    if required_key and required_key not in data:
        issues.append(f"{resource_type} 缺少必需字段 {required_key}")

    questions = data.get("questions")
    if isinstance(questions, list):
        if len(questions) != 5:
            issues.append("练习题必须恰好包含 5 题")
        stems: list[str] = []
        expected_types = ["choice", "choice", "choice", "fill", "fill"]
        for index, raw in enumerate(questions[:5]):
            if not isinstance(raw, dict):
                issues.append(f"第 {index + 1} 题结构无效")
                continue
            stem = str(raw.get("stem") or "").strip()
            stems.append(stem)
            if index < len(expected_types) and raw.get("type") != expected_types[index]:
                issues.append(f"第 {index + 1} 题题型不符合 3 道选择 + 2 道填空的顺序")
            answer = str(raw.get("answer") or "").strip()
            explanation = str(raw.get("explanation") or "").strip()
            if not answer:
                issues.append(f"第 {index + 1} 题缺少参考答案")
            if len(explanation) < 8:
                issues.append(f"第 {index + 1} 题缺少有意义的答案解析")
            if raw.get("type") == "choice":
                options = [str(x).strip() for x in (raw.get("options") or [])]
                if len(options) != 4 or len(set(options)) != 4:
                    issues.append(f"第 {index + 1} 题必须有 4 个互不重复的选项")
                elif answer not in options:
                    issues.append(f"第 {index + 1} 题答案必须与一个选项完全一致")
        nonempty_stems = [stem for stem in stems if stem]
        if len(set(nonempty_stems)) != len(nonempty_stems):
            issues.append("练习题题干存在重复，缺少知识点区分度")

    domain = data.get("domain_narrative")
    structure = data.get("structure_logic")
    if isinstance(domain, dict) or isinstance(structure, dict):
        if not isinstance(domain, dict) or not isinstance(structure, dict):
            issues.append("讲解/代码案例必须同时包含 domain_narrative 与 structure_logic")
        else:
            domain_required = ("headline", "story")
            for key in domain_required:
                minimum = 4 if key == "headline" else 8
                if len(str(domain.get(key) or "").strip()) < minimum:
                    issues.append(f"domain_narrative.{key} 内容不足")
            required = (
                ("problem_formalization", "code_framework", "step_hints")
                if resource_type == "code_case"
                else ("learning_objectives", "abstract_model", "algorithm_outline", "pitfalls")
            )
            for key in (*required, "data_structures", "time_complexity", "space_complexity", "correctness_proof"):
                value = structure.get(key)
                if value in (None, "", []):
                    issues.append(f"structure_logic.{key} 缺失")
            placeholder_text = json.dumps(structure, ensure_ascii=False)
            for placeholder in ("待分析", "待补全", "建议重新生成", "由旧版"):
                if placeholder in placeholder_text:
                    issues.append(f"结构化内容仍含占位语句“{placeholder}”")

            domain_text = " ".join(
                str(domain.get(key) or "") for key in ("headline", "story", "mission")
            )
            forbidden_domain = re.compile(
                r"Python|C\+\+|Java|TODO|O\s*\(|数组|链表|栈|队列|哈希|二叉树|图论|"
                r"指针|节点|动态规划|贪心|回溯|排序|算法|BFS|DFS|变量|代码|循环",
                re.I,
            )
            if forbidden_domain.search(domain_text):
                issues.append("domain_narrative 混入代码或算法术语，未做到业务叙事与结构讲解分离")

            data_structures = structure.get("data_structures")
            if not isinstance(data_structures, list) or not data_structures:
                issues.append("structure_logic.data_structures 必须给出具体数据结构")
            elif len({str(item).strip() for item in data_structures}) != len(data_structures):
                issues.append("structure_logic.data_structures 存在重复项")

            for key in ("time_complexity", "space_complexity"):
                value = str(structure.get(key) or "")
                if not _COMPLEXITY_PATTERN.search(value):
                    issues.append(f"structure_logic.{key} 缺少明确的大 O 复杂度及说明")
            if len(str(structure.get("correctness_proof") or "").strip()) < 24:
                issues.append("structure_logic.correctness_proof 过短，未说明算法为何正确")

            is_scenario = resource_type == "code_case"
            if is_scenario:
                story = str(domain.get("story") or "").strip()
                mission = str(domain.get("mission") or "").strip()
                if len(story) + len(mission) < 80:
                    issues.append("剧情沙盒的背景与任务过短，缺少角色、冲突和可执行目标")
                formalization = str(structure.get("problem_formalization") or "")
                has_input = any(word in formalization for word in ("输入", "给定", "接收"))
                has_output = any(word in formalization for word in ("输出", "返回", "求出"))
                if len(formalization) < 30 or not (has_input and has_output):
                    issues.append("剧情沙盒的形式化题意必须明确输入与输出")
                framework = str(structure.get("code_framework") or "")
                code_lines = [line for line in framework.splitlines() if line.strip()]
                if not 8 <= len(code_lines) <= 60:
                    issues.append("代码框架应为 8～60 行的可练习骨架")
                if "TODO" not in framework:
                    issues.append("代码框架缺少明确 TODO 练习点")
                try:
                    compile(framework, "<scenario>", "exec")
                except (SyntaxError, ValueError):
                    issues.append("代码框架不是可解析的 Python 程序")
                implementation_terms = _implementation_relevance_terms(topic)
                if implementation_terms and not any(
                    term.lower() in framework.lower() for term in implementation_terms
                ):
                    issues.append("代码框架未体现当前课程主题的核心结构或操作")
                hints = structure.get("step_hints")
                if not isinstance(hints, list) or len(hints) < 3:
                    issues.append("剧情沙盒至少需要 3 条递进提示")
                else:
                    clean_hints = [str(item).strip() for item in hints]
                    if len(set(clean_hints)) != len(clean_hints) or any(len(item) < 6 for item in clean_hints):
                        issues.append("剧情沙盒提示重复或过于空泛")
            else:
                story = str(domain.get("story") or "").strip()
                if len(story) < 100:
                    issues.append("概念学案的业务故事过短，未形成清晰的问题动机")
                objectives = structure.get("learning_objectives")
                if not isinstance(objectives, list) or len(objectives) < 2:
                    issues.append("概念学案至少需要 2 个具体学习目标")
                abstract_model = str(structure.get("abstract_model") or "").strip()
                outline = str(structure.get("algorithm_outline") or "").strip()
                if len(abstract_model) < 30:
                    issues.append("概念学案的抽象模型过短，未明确输入、输出或不变量")
                if len(outline) < 60:
                    issues.append("概念学案的算法步骤过短，学生无法据此复现过程")
                pitfalls = structure.get("pitfalls")
                if not isinstance(pitfalls, list) or len(pitfalls) < 2:
                    issues.append("概念学案至少需要 2 个具体易错点")

    levels = data.get("levels")
    if isinstance(levels, list):
        goal = str(data.get("reading_goal") or "").strip()
        if len(goal) < 14:
            issues.append("拓展阅读目标过短，未说明阅读后应获得什么能力")
        names = {str(level.get("level") or "") for level in levels if isinstance(level, dict)}
        if not {"基础", "进阶", "挑战"}.issubset(names):
            issues.append("拓展阅读必须包含基础、进阶、挑战三层")
        all_titles: list[str] = []
        kb_text = " ".join(
            f"{chunk.get('title', '')} {chunk.get('content', '')}"
            for chunk in (chunks or [])
        ).lower()
        for level in levels:
            if not isinstance(level, dict):
                continue
            items = level.get("items")
            if not isinstance(items, list) or len(items) < 2:
                issues.append(f"{level.get('level', '未知')}层至少需要 2 条阅读材料")
                continue
            for item in items:
                if not isinstance(item, dict) or not all(str(item.get(k) or "").strip() for k in ("title", "why", "task")):
                    issues.append(f"{level.get('level', '未知')}层阅读条目缺少标题、理由或读后任务")
                    break
                title = str(item.get("title") or "").strip()
                all_titles.append(title)
                if len(str(item.get("why") or "").strip()) < 12:
                    issues.append(f"{level.get('level', '未知')}层阅读理由过于空泛")
                if len(str(item.get("task") or "").strip()) < 8:
                    issues.append(f"{level.get('level', '未知')}层读后任务不可执行或过于空泛")
                if chunks is not None and ("《" in title or "》" in title) and title.lower() not in kb_text:
                    issues.append(f"阅读材料“{title}”未得到知识库支持")
        if len(set(all_titles)) != len(all_titles):
            issues.append("拓展阅读存在重复材料，未形成基础到挑战的梯度")

    # 教学短视频脚本校验：shots 数量、字段完整性、字幕/旁白长度与互补
    shots = data.get("shots")
    if isinstance(shots, list):
        if not (6 <= len(shots) <= 10):
            issues.append("教学短视频分镜数量应为 6～10 个")
        subtitles: list[str] = []
        for index, shot in enumerate(shots, start=1):
            if not isinstance(shot, dict):
                issues.append(f"第 {index} 镜结构无效")
                continue
            for key in ("scene", "visual_hint", "subtitle", "voiceover"):
                value = str(shot.get(key) or "").strip()
                if not value:
                    issues.append(f"第 {index} 镜缺少 {key} 字段")
            subtitle = str(shot.get("subtitle") or "").strip()
            voiceover = str(shot.get("voiceover") or "").strip()
            subtitles.append(subtitle)
            if len(subtitle) > 30:
                issues.append(f"第 {index} 镜字幕超过 30 字，应精炼为关键词")
            if len(voiceover) > 200:
                issues.append(f"第 {index} 镜旁白文案过长，单镜不宜超过 200 字")
            if subtitle and voiceover and subtitle == voiceover:
                issues.append(f"第 {index} 镜字幕与旁白文案完全重复，字幕应为关键词提炼")
            duration = shot.get("duration_sec")
            if duration is not None:
                try:
                    dur_val = int(duration)
                    if not (3 <= dur_val <= 20):
                        issues.append(f"第 {index} 镜时长 {dur_val} 秒不在 3～20 秒范围")
                except (TypeError, ValueError):
                    issues.append(f"第 {index} 镜 duration_sec 必须为整数")
        if len(set(subtitles)) != len(subtitles):
            issues.append("分镜字幕存在重复，缺少知识点区分度")

    # PPT 大纲校验：与 PptAgent 的 8～12 页质量约束保持一致，并拒绝提示词回声。
    slides = data.get("slides")
    if isinstance(slides, list):
        if not (8 <= len(slides) <= 12):
            issues.append("PPT 大纲页数应为 8～12 页")
        layouts = [str(s.get("layout") or "").strip() for s in slides if isinstance(s, dict)]
        if layouts.count("cover") != 1 or (layouts and layouts[0] != "cover"):
            issues.append("PPT 必须以唯一的 cover 封面页开场")
        if "agenda" not in layouts:
            issues.append("PPT 大纲缺少学习路径页（layout=agenda）")
        if layouts.count("closing") != 1 or (layouts and layouts[-1] != "closing"):
            issues.append("PPT 必须以唯一的 closing 总结页收尾")
        placeholder_tokens = (
            "封面标题", "页面标题", "代码页", "要点1", "要点2", "要点3",
            "章节1", "章节2", "关键伪代码或代码片段", "副标题（可空）",
            "讲者备注", "逐行解释",
        )
        titles: list[str] = []
        for index, slide in enumerate(slides, start=1):
            if not isinstance(slide, dict):
                issues.append(f"第 {index} 页结构无效")
                continue
            layout = str(slide.get("layout") or "").strip()
            title = str(slide.get("title") or "").strip()
            if not title:
                issues.append(f"第 {index} 页缺少标题")
            titles.append(title)
            notes = str(slide.get("notes") or "").strip()
            if len(notes) < 10:
                issues.append(f"第 {index} 页讲者备注过短，应说明讲解重点")
            flattened = json.dumps(slide, ensure_ascii=False)
            if any(token in flattened for token in placeholder_tokens):
                issues.append(f"第 {index} 页仍含提示词示意文字，必须替换为真实课程内容")
            bullets_raw = slide.get("bullets")
            if layout in {"agenda", "content", "closing"}:
                if not isinstance(bullets_raw, list) or not (3 <= len(bullets_raw) <= 5):
                    issues.append(f"第 {index} 页应包含 3～5 条精炼要点")
                elif len({str(item).strip() for item in bullets_raw}) != len(bullets_raw):
                    issues.append(f"第 {index} 页存在重复要点")
            if layout == "code":
                code_lines = [line for line in str(slide.get("code") or "").splitlines() if line.strip()]
                if not (3 <= len(code_lines) <= 12):
                    issues.append(f"第 {index} 页代码应为 3～12 行可讲解片段")
        if len(set(titles)) != len(titles):
            issues.append("PPT 页面标题存在重复，叙事层次不足")

    return list(dict.fromkeys(issues))


def _implementation_relevance_terms(topic: str) -> tuple[str, ...]:
    normalized = re.sub(r"\s+", "", topic or "")
    mappings: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("链表", ("ListNode", "next", "head", "current")),
        ("动态规划", ("dp", "state", "状态")),
        ("双指针", ("left", "right", "slow", "fast", "指针")),
        ("栈", ("stack", "push", "pop", "append")),
        ("队列", ("queue", "deque", "popleft", "enqueue")),
        ("二叉树", ("TreeNode", "root", "left", "right")),
        ("图", ("graph", "adj", "visited", "bfs", "dfs")),
        ("排序", ("sort", "merge", "pivot", "swapped", "排序")),
        ("哈希", ("dict", "set", "hash", "哈希")),
        ("回溯", ("backtrack", "path", "撤销", "剪枝")),
        ("字符串", ("str", "string", "char", "字符")),
    )
    for marker, terms in mappings:
        if marker in normalized:
            return terms
    return ()


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
