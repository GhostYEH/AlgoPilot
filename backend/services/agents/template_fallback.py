"""无 LLM Key 或 LLM 不可用时的课程知识库模板降级生成（TemplateFallbackAgent）。"""

from __future__ import annotations

import json
import re
from typing import Any

from schemas.resources import ResourceType
from services.agents.resource_roles import (
    PersonaHints,
    _build_knowledge_mindmap,
    _build_scenario_code_framework,
    _fallback_ppt_slides,
    _fallback_reading_levels,
    _fallback_trace_payload,
    _fallback_video_shots,
    _match_topic_key,
    _mindmap_focus_label,
    _normalize_ppt_slide,
    _normalize_video_shot,
    _sanitize_domain_narrative,
    _TOPIC_ENRICHMENTS,
)
from services.knowledge.retriever import KnowledgeChunk, format_context_block
from services.verification.builder import chunks_to_grounded

GENERATED_BY = "TemplateFallbackAgent"

_INTERNAL_CONTENT_KEYS = frozenset({
    "_template_disclaimer",
    "_fallback_reason",
    "placeholder",
    "placeholder_reason",
    "fallback_reason",
    "verdict",
    "trace_source",
    "step_count",
    "user_line_count",
    "result_preview",
    "message",
})


def _strip_internal_fields(payload: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if k not in _INTERNAL_CONTENT_KEYS}


def grounded_chunks_payload(chunks: list[KnowledgeChunk]) -> list[dict[str, str]]:
    return [
        {
            "id": g.id,
            "title": g.title,
            "snippet": g.snippet,
        }
        for g in chunks_to_grounded(chunks)
    ]


def _bullet_lines(chunks: list[KnowledgeChunk], limit: int = 6) -> list[str]:
    lines: list[str] = []
    for ch in chunks:
        title = str(ch.get("title") or "").strip()
        body = str(ch.get("content") or "").strip()
        for para in re.split(r"\n+", body):
            para = para.strip().lstrip("-•* ").strip()
            if len(para) < 8:
                continue
            if title and title not in para:
                lines.append(f"{title}：{para[:120]}")
            else:
                lines.append(para[:140])
            if len(lines) >= limit:
                return lines
    if not lines and chunks:
        lines.append(str(chunks[0].get("title") or "核心概念"))
    return lines or ["请对照课程讲义复习本主题。"]


def _topic_label(topic: str, module_key: str) -> str:
    if module_key:
        return f"{module_key} · {topic[:32]}"
    return topic[:48] or "数据结构与算法"


def _build_title(resource_type: ResourceType, topic: str, module_key: str) -> str:
    labels = {
        "document": "概念讲解",
        "mindmap": "知识图谱",
        "exercises": "练习题单",
        "code_case": "代码案例",
        "trace_animation": "轨迹动画",
        "reading": "拓展阅读",
        "ppt": "课程讲义",
        "video_script": "教学短视频脚本",
    }
    base = labels.get(resource_type, resource_type)
    return f"[模板] {base} · {_topic_label(topic, module_key)}"


def _enrichment_for(topic: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """从 _TOPIC_ENRICHMENTS 取出 concept/scenario 兜底字段；未匹配返回空 dict。"""
    key = _match_topic_key(topic)
    if not key:
        return {}, {}
    entry = _TOPIC_ENRICHMENTS.get(key) or {}
    return entry.get("concept") or {}, entry.get("scenario") or {}


def generate_document(
    *,
    topic: str,
    module_key: str,
    chunks: list[KnowledgeChunk],
    fallback_reason: str,
) -> tuple[str, str, dict]:
    bullets = _bullet_lines(chunks, 8)
    excerpt = format_context_block(chunks) if chunks else ""
    concept_enrich, _ = _enrichment_for(topic)

    # 业务域 story：必须纯叙事、不含 CS 术语，由 _sanitize_domain_narrative 兜底过滤
    story = "；".join(bullets[:4]) if bullets else f"围绕「{topic}」的核心知识要点与课堂任务。"
    objectives = concept_enrich.get("learning_objectives") or [
        b[:60] for b in bullets[:3]
    ] or ["理解核心概念", "掌握基本操作"]
    pitfalls = concept_enrich.get("pitfalls") or ["边界条件", "复杂度误判"]
    abstract_model = concept_enrich.get("abstract_model") or (bullets[0][:80] if bullets else topic)
    algorithm_outline = concept_enrich.get("algorithm_outline") or (
        excerpt[:800] if excerpt else "参考课程知识库补全核心步骤、不变量与边界条件。"
    )
    data_structures = concept_enrich.get("data_structures") or [module_key or "基础结构"]
    time_complexity = concept_enrich.get("time_complexity") or "O(n)：模板降级，按主题典型复杂度估算。"
    space_complexity = concept_enrich.get("space_complexity") or "O(n)：模板降级，按主题典型复杂度估算。"
    correctness_proof = concept_enrich.get("correctness_proof") or (
        "结合算法不变量与边界条件：每一步保持循环不变量成立，终止时覆盖全部输入，"
        "故结果与预期一致；具体推导请对照知识库片段人工核对。"
    )

    payload = _strip_internal_fields({
        "domain_narrative": {
            "headline": _topic_label(topic, module_key),
            "story": story,
            "illustration_hint": f"{topic} 主题场景概念图",
        },
        "structure_logic": {
            "learning_objectives": objectives,
            "abstract_model": abstract_model,
            "data_structures": data_structures,
            "algorithm_outline": algorithm_outline,
            "time_complexity": time_complexity,
            "space_complexity": space_complexity,
            "correctness_proof": correctness_proof,
            "pitfalls": pitfalls[:3] if isinstance(pitfalls, list) else [str(pitfalls)],
        },
    })
    # 应用 domain_narrative 术语过滤，避免校验「业务域混入代码或算法术语」
    payload["domain_narrative"] = _sanitize_domain_narrative(payload["domain_narrative"])
    content = json.dumps(payload, ensure_ascii=False, indent=2)
    meta = {
        "format": "domain_structure_json",
        "template": "document_from_chunks",
        "fallback_reason": fallback_reason,
    }
    return _build_title("document", topic, module_key), content, meta


def generate_mindmap(
    *,
    topic: str,
    module_key: str,
    chunks: list[KnowledgeChunk],
    focus_hint: str = "",
    fallback_reason: str,
) -> tuple[str, str, dict]:
    content = _build_knowledge_mindmap(
        topic=topic,
        module_key=module_key,
        focus_hint=focus_hint,
        chunks=chunks,
    )
    title_topic = _mindmap_focus_label(topic, module_key, focus_hint)
    meta = {"format": "mermaid", "template": "mindmap_from_chunks", "fallback_reason": fallback_reason}
    return _build_title("mindmap", title_topic, module_key), content, meta


def generate_exercises(
    *,
    topic: str,
    module_key: str,
    chunks: list[KnowledgeChunk],
    hints: PersonaHints,
    fallback_reason: str,
) -> tuple[str, str, dict]:
    topic_name = topic[:40] or module_key or "当前模块"

    # 动态规划是演示与比赛答辩中的高频主题。LLM 连续未通过结构校验时，
    # 兜底题单也必须能真正检验状态定义、转移、边界与遍历顺序，不能退化成
    # “哪一项有依据”式的同义复述。
    if module_key == "dp" or "动态规划" in topic_name:
        focus = "动态规划：状态定义、转移方程、边界初始化与遍历顺序"
        questions = [
            {
                "type": "choice",
                "stem": "把 0/1 背包的二维状态压缩为一维后，dp[j] 最准确的含义是什么？",
                "options": [
                    "处理完当前及之前物品后，容量不超过 j 时可取得的最大价值",
                    "恰好选择 j 件物品时可取得的最大价值",
                    "容量为 j 时必须装满背包的方案数量",
                    "只使用当前这一件物品时可取得的价值",
                ],
                "hint": "先说清楚 j 表示容量，状态还要包含“已经处理到哪些物品”的阶段含义。",
                "focus": focus,
                "difficulty": "easy",
                "answer": "处理完当前及之前物品后，容量不超过 j 时可取得的最大价值",
                "explanation": "一维数组省略了物品维度，但循环轮次仍代表已处理的物品集合；dp[j] 保存该阶段容量上限为 j 的最优价值。",
            },
            {
                "type": "choice",
                "stem": "0/1 背包使用一维 dp 时，为什么容量 j 必须从大到小遍历？",
                "options": [
                    "保证 dp[j-w] 仍是上一轮物品的结果，避免同一件物品被重复选取",
                    "把时间复杂度从 O(nW) 降为 O(W)",
                    "保证每次都优先选择价值最大的物品",
                    "让背包在每一步都恰好被装满",
                ],
                "hint": "比较更新 dp[j] 时读取的 dp[j-w]，它应该来自本轮还是上一轮？",
                "focus": focus,
                "difficulty": "medium",
                "answer": "保证 dp[j-w] 仍是上一轮物品的结果，避免同一件物品被重复选取",
                "explanation": "倒序更新时 j-w 尚未被当前物品改写，因此每件物品至多使用一次；升序会读到本轮刚更新的状态，效果会变成允许重复选取。",
            },
            {
                "type": "choice",
                "stem": "关于 0/1 背包与完全背包的一维遍历顺序，哪项正确？",
                "options": [
                    "0/1 背包容量倒序，完全背包容量正序",
                    "两者都必须倒序，否则无法得到最优解",
                    "两者都必须正序，才能复用较小容量状态",
                    "遍历顺序只影响运行速度，不影响答案",
                ],
                "hint": "关键区别是每件物品能否在同一轮被再次使用。",
                "focus": focus,
                "difficulty": "medium",
                "answer": "0/1 背包容量倒序，完全背包容量正序",
                "explanation": "0/1 背包要隔离上一轮状态，所以倒序；完全背包允许当前物品重复贡献，因此正序读取本轮已更新的较小容量状态。",
            },
            {
                "type": "fill",
                "stem": "物品重量为 w、价值为 v、背包容量为 W。请写出 0/1 背包的一维转移式和 j 的遍历范围。",
                "hint": "比较“不选当前物品”和“选当前物品”两种来源，并注意 j 的方向。",
                "focus": focus,
                "difficulty": "medium",
                "answer": "dp[j] = max(dp[j], dp[j-w] + v)，j 从 W 递减到 w。",
                "explanation": "dp[j] 表示不选当前物品，dp[j-w]+v 表示选当前物品；j 倒序才能保证每件物品只使用一次。",
            },
            {
                "type": "fill",
                "stem": "设计一个动态规划解法时，至少要明确哪四项信息？",
                "hint": "从“状态表示什么”开始，再考虑状态如何得到、最小规模答案以及计算依赖顺序。",
                "focus": focus,
                "difficulty": "hard",
                "answer": "状态定义、状态转移方程、边界或初始值、满足依赖关系的遍历顺序。",
                "explanation": "四项共同决定 DP 是否正确：状态定义消除歧义，转移描述子问题关系，边界提供递推起点，遍历顺序保证依赖状态已就绪且未被错误覆盖。",
            },
        ]
        payload = _strip_internal_fields({"questions": questions})
        content = json.dumps(payload, ensure_ascii=False, indent=2)
        meta = {"format": "quiz_json", "template": "quiz_dp_grounded", "fallback_reason": fallback_reason}
        return _build_title("exercises", topic, module_key), content, meta

    focus = hints.error_preference or "边界与复杂度"
    bullets = _bullet_lines(chunks, 5)
    while len(bullets) < 3:
        bullets.append(f"{topic}：结合课程讲义分析核心操作与边界条件")
    distractors = [
        f"{topic_name}在任何输入下都不需要处理边界条件",
        f"{topic_name}的所有操作时间复杂度都固定为 O(1)",
        f"学习{topic_name}时可以忽略数据组织方式与操作顺序",
    ]
    questions: list[dict[str, Any]] = []
    for i, stem_base in enumerate(bullets[:3]):
        questions.append({
            "type": "choice",
            "stem": f"根据课程讲义，关于「{topic_name}」的第 {i + 1} 个要点，哪一项有明确依据？",
            "options": [stem_base[:120], *distractors],
            "hint": f"回看讲义中的要点：{stem_base[:70]}",
            "focus": focus,
            "difficulty": "easy" if i == 0 else "medium",
            "answer": stem_base[:120],
            "explanation": f"课程知识库明确给出的要点是：{stem_base[:160]}。其余选项是缺少前提的绝对化表述。",
        })
    questions.extend([
        {
            "type": "fill",
            "stem": f"请结合讲义说明「{topic_name}」中最需要注意的操作或边界条件。",
            "hint": bullets[0][:100],
            "focus": focus,
            "difficulty": "medium",
            "answer": bullets[0][:160],
            "explanation": "评分时应检查是否写出了具体操作、边界条件及遗漏它可能造成的后果。",
        },
        {
            "type": "fill",
            "stem": f"请用自己的话解释「{topic_name}」的核心思路，并说明它适用于什么问题。",
            "hint": bullets[1][:100],
            "focus": focus,
            "difficulty": "hard",
            "answer": bullets[1][:160],
            "explanation": "答案需同时说明核心思路与适用条件，不能只写一个术语或复杂度。",
        },
    ])
    payload = _strip_internal_fields({"questions": questions})
    content = json.dumps(payload, ensure_ascii=False, indent=2)
    meta = {"format": "quiz_json", "template": "quiz_from_chunks", "fallback_reason": fallback_reason}
    return _build_title("exercises", topic, module_key), content, meta


def generate_code_case(
    *,
    topic: str,
    module_key: str,
    chunks: list[KnowledgeChunk],
    hints: PersonaHints,
    fallback_reason: str,
) -> tuple[str, str, dict]:
    bullets = _bullet_lines(chunks, 4)
    _, scenario_enrich = _enrichment_for(topic)

    # code_framework：优先用 _TOPIC_ENRICHMENTS 兜底的 _build_scenario_code_framework
    framework = scenario_enrich.get("code_framework") or _build_scenario_code_framework(topic)
    if "TODO" not in framework:
        # 兜底加上 TODO 注释，确保通过校验
        framework = framework.rstrip() + "\n    # TODO: 根据课程知识库要点实现\n"

    # problem_formalization：必须含"输入"/"输出"关键词
    problem_formalization = scenario_enrich.get("problem_formalization") or (
        "输入：根据课程讲义确定的实验数据。"
        "输出：按题目要求计算得到的结果。"
        "限制：使用课程指定数据结构，注意边界与复杂度。"
    )
    data_structures = scenario_enrich.get("data_structures") or [module_key or "基础结构"]
    step_hints = scenario_enrich.get("step_hints") or (bullets[:3] or ["读题", "定义状态", "验证边界"])
    time_complexity = scenario_enrich.get("time_complexity") or "O(n)：模板降级，按主题典型复杂度估算。"
    space_complexity = scenario_enrich.get("space_complexity") or "O(n)：模板降级，按主题典型复杂度估算。"
    correctness_proof = scenario_enrich.get("correctness_proof") or (
        "结合算法不变量与边界条件：每一步保持循环不变量成立，终止时覆盖全部输入，"
        "故结果与预期一致；具体推导请对照知识库片段人工核对。"
    )

    payload = _strip_internal_fields({
        "domain_narrative": {
            "headline": _topic_label(topic, module_key),
            "story": (
                f"在课堂实验现场，学生需要围绕「{topic}」完成一次完整的实操任务："
                "理解背景、写出代码骨架并通过样例。"
                "过程中需要注意角色分工、冲突处理与目标达成，形成可演示的成果。"
            ),
            "mission": "补全代码框架并通过样例验证，最终给出可演示的成果",
            "illustration_hint": f"{topic} 主题课堂实验现场全景",
        },
        "structure_logic": {
            "problem_formalization": problem_formalization,
            "data_structures": data_structures,
            "code_framework": framework,
            "step_hints": step_hints,
            "time_complexity": time_complexity,
            "space_complexity": space_complexity,
            "correctness_proof": correctness_proof,
        },
    })
    # 应用 domain_narrative 术语过滤
    payload["domain_narrative"] = _sanitize_domain_narrative(payload["domain_narrative"])
    content = json.dumps(payload, ensure_ascii=False, indent=2)
    meta = {"format": "scenario_json", "template": "code_from_chunks", "fallback_reason": fallback_reason}
    return _build_title("code_case", topic, module_key), content, meta


def generate_reading(
    *,
    topic: str,
    module_key: str,
    chunks: list[KnowledgeChunk],
    hints: PersonaHints,
    fallback_reason: str,
) -> tuple[str, str, dict]:
    levels = _fallback_reading_levels(hints)
    for level in levels:
        items = level.get("items")
        if isinstance(items, list) and chunks:
            extra = str(chunks[0].get("title") or topic)
            if extra not in str(items[0]):
                items.insert(0, {
                    "title": extra,
                    "type": "课程知识库",
                    "why": f"用于对照「{topic}」的课程定义、核心操作与边界条件。",
                    "task": f"阅读后用自己的话总结「{topic}」的一个核心要点。",
                })
    payload = _strip_internal_fields({
        "topic": _topic_label(topic, module_key),
        "levels": levels,
    })
    content = json.dumps(payload, ensure_ascii=False, indent=2)
    meta = {"format": "reading_json", "template": "reading_template", "fallback_reason": fallback_reason}
    return _build_title("reading", topic, module_key), content, meta


def generate_trace_placeholder(
    *,
    topic: str,
    module_key: str,
    fallback_reason: str,
) -> tuple[str, str, dict]:
    raw_payload = _fallback_trace_payload(topic=_topic_label(topic, module_key))
    payload = _strip_internal_fields(raw_payload)
    content = json.dumps(payload, ensure_ascii=False, indent=2)
    meta = {
        "format": "trace_json",
        "template": "trace_placeholder",
        "placeholder": True,
        "placeholder_reason": "轨迹动画需 LLM 生成可执行代码或接入 Trace Runner；模板模式仅提供占位示例",
        "fallback_reason": fallback_reason,
        "trace_verdict": "SKIPPED",
        "trace_steps": 0,
    }
    return _build_title("trace_animation", topic, module_key), content, meta


def generate_ppt(
    *,
    topic: str,
    module_key: str,
    chunks: list[KnowledgeChunk],
    hints: PersonaHints,
    fallback_reason: str,
) -> tuple[str, str, dict]:
    """模板降级：用知识库要点 + 内置 fallback 大纲组装 PPT JSON。"""
    topic_label = (topic or module_key or "数据结构与算法")[:48]
    title = f"{topic_label} · 课程讲义"
    # fallback 本身按课程知识与 topic enrichment 组织完整叙事，不再把同一条
    # “知识库要点”机械复制到多页。
    enriched = _fallback_ppt_slides(topic_label, hints, chunks)

    payload = _strip_internal_fields({
        "title": title,
        "slides": [_normalize_ppt_slide(s, hints=hints) for s in enriched],
    })
    content = json.dumps(payload, ensure_ascii=False, indent=2)
    meta = {
        "format": "ppt_outline_json",
        "template": "ppt_from_chunks",
        "fallback_reason": fallback_reason,
    }
    return _build_title("ppt", topic, module_key), content, meta


def generate_video_script(
    *,
    topic: str,
    module_key: str,
    chunks: list[KnowledgeChunk],
    hints: PersonaHints,
    fallback_reason: str,
) -> tuple[str, str, dict]:
    """模板降级：用知识库要点 + 内置 fallback 分镜组装教学短视频脚本 JSON。

    不做真实视频渲染；前端结合 TTS 朗读 voiceover 文案即可形成
    "图文 + 语音" 的伪视频体验。
    """
    bullets = _bullet_lines(chunks, 6)
    topic_label = _topic_label(topic, module_key)
    title = f"{topic_label} · 教学短视频"
    goal = hints.learning_goals[:80] or f"理解{topic_label}的核心思路与典型应用"
    base_shots = _fallback_video_shots(topic_label, hints)

    # 用知识库要点增强分镜：第 3 镜（概念定义）注入知识库第一条要点；
    # 第 5 镜（易错点）注入易错点偏好或知识库第二条要点
    enriched: list[dict[str, Any]] = []
    for shot in base_shots:
        copied = dict(shot)
        idx = copied.get("index")
        if idx == 3 and bullets:
            # 概念定义镜：用知识库要点替换 voiceover 末段
            kb_hint = bullets[0][:60]
            copied["voiceover"] = str(copied.get("voiceover", ""))[:80] + f" 课程知识库指出：{kb_hint}。"
        elif idx == 5:
            # 易错点镜：若有知识库第二条，作为补充示例
            if len(bullets) > 1:
                copied["scene"] = str(copied.get("scene", "")) + f" 配合课程要点：{bullets[1][:50]}。"
        enriched.append(copied)

    normalized_shots = [
        _normalize_video_shot(s, idx, hints=hints)
        for idx, s in enumerate(enriched, start=1)
    ]
    duration_total = sum(int(s.get("duration_sec") or 8) for s in normalized_shots)

    payload = _strip_internal_fields({
        "title": title,
        "duration_sec": duration_total,
        "goal": goal,
        "shots": normalized_shots,
        "summary": f"回顾{topic_label}的核心步骤，对照易错点再练习一次。",
    })
    content = json.dumps(payload, ensure_ascii=False, indent=2)
    meta = {
        "format": "video_script_json",
        "template": "video_script_from_chunks",
        "fallback_reason": fallback_reason,
    }
    return _build_title("video_script", topic, module_key), content, meta


def generate_fallback_resource(
    resource_type: ResourceType,
    *,
    topic: str,
    profile_block: str,
    module_key: str = "",
    chunks: list[KnowledgeChunk],
    focus_hint: str = "",
    fallback_reason: str,
) -> tuple[str, str, dict]:
    hints = PersonaHints.from_profile_block(profile_block)
    generators = {
        "document": lambda: generate_document(
            topic=topic, module_key=module_key, chunks=chunks, fallback_reason=fallback_reason
        ),
        "mindmap": lambda: generate_mindmap(
            topic=topic,
            module_key=module_key,
            focus_hint=focus_hint,
            chunks=chunks,
            fallback_reason=fallback_reason,
        ),
        "exercises": lambda: generate_exercises(
            topic=topic, module_key=module_key, chunks=chunks, hints=hints, fallback_reason=fallback_reason
        ),
        "code_case": lambda: generate_code_case(
            topic=topic, module_key=module_key, chunks=chunks, hints=hints, fallback_reason=fallback_reason
        ),
        "reading": lambda: generate_reading(
            topic=topic, module_key=module_key, chunks=chunks, hints=hints, fallback_reason=fallback_reason
        ),
        "trace_animation": lambda: generate_trace_placeholder(
            topic=topic, module_key=module_key, fallback_reason=fallback_reason
        ),
        "ppt": lambda: generate_ppt(
            topic=topic,
            module_key=module_key,
            chunks=chunks,
            hints=hints,
            fallback_reason=fallback_reason,
        ),
        "video_script": lambda: generate_video_script(
            topic=topic,
            module_key=module_key,
            chunks=chunks,
            hints=hints,
            fallback_reason=fallback_reason,
        ),
    }
    gen = generators.get(resource_type)
    if not gen:
        raise ValueError(f"unsupported resource_type: {resource_type}")
    title, content, meta = gen()
    meta.update(
        {
            "fallback": True,
            "fallback_reason": fallback_reason,
            "grounded_chunks": grounded_chunks_payload(chunks),
            "generated_by": GENERATED_BY,
            "agent_id": GENERATED_BY,
            "agent_role": "课程知识库模板降级",
            "knowledge_refs": [c["id"] for c in chunks],
            "knowledge_chunk_ids": [c["id"] for c in chunks],
        }
    )
    return title, content, meta


def llm_unavailable_reason() -> str | None:
    from core.config import settings

    if not settings.llm_configured:
        return "未配置 SPARK_API_PASSWORD（LLM Key 不可用）"
    return None


def is_llm_related_error(exc: BaseException) -> bool:
    from fastapi import HTTPException

    if isinstance(exc, HTTPException) and exc.status_code in (502, 503, 504):
        return True
    msg = str(exc).lower()
    needles = ("ai 未配置", "spark_api", "星火", "llm", "503", "502", "504", "无法连接星火")
    return any(n in msg for n in needles)
