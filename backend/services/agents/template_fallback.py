"""无 LLM Key 或 LLM 不可用时的课程知识库模板降级生成（TemplateFallbackAgent）。"""

from __future__ import annotations

import json
import re
from typing import Any

from schemas.resources import ResourceType
from services.agents.resource_roles import (
    PersonaHints,
    _build_knowledge_mindmap,
    _fallback_reading_levels,
    _fallback_trace_payload,
    _mindmap_focus_label,
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
    }
    base = labels.get(resource_type, resource_type)
    return f"[模板] {base} · {_topic_label(topic, module_key)}"


def generate_document(
    *,
    topic: str,
    module_key: str,
    chunks: list[KnowledgeChunk],
    fallback_reason: str,
) -> tuple[str, str, dict]:
    bullets = _bullet_lines(chunks, 8)
    excerpt = format_context_block(chunks) if chunks else ""
    story_parts = []
    for b in bullets[:4]:
        story_parts.append(b)
    story = "；".join(story_parts) if story_parts else f"围绕「{topic}」的核心知识要点。"
    objectives = [b[:60] for b in bullets[:3]] or ["理解核心概念", "掌握基本操作"]
    pitfalls = ["边界条件", "复杂度误判"]
    for b in bullets:
        bl = b.lower()
        if "易错" in bl or "注意" in bl or "陷阱" in bl:
            pitfalls.insert(0, b[:40])
            break
    payload = _strip_internal_fields({
        "domain_narrative": {
            "headline": _topic_label(topic, module_key),
            "story": story,
            "illustration_hint": f"{topic} 主题场景概念图",
        },
        "structure_logic": {
            "learning_objectives": objectives,
            "abstract_model": bullets[0][:80] if bullets else topic,
            "data_structures": [module_key or "基础结构"],
            "algorithm_outline": excerpt[:800] if excerpt else "请参考课程知识库补全。",
            "time_complexity": "依具体算法而定（模板未推断）",
            "space_complexity": "依具体算法而定",
            "correctness_proof": "请对照知识库片段人工核对",
            "pitfalls": pitfalls[:3],
        },
    })
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
    focus = hints.error_preference or "边界与复杂度"
    bullets = _bullet_lines(chunks, 3)
    questions: list[dict[str, Any]] = []
    for i, stem_base in enumerate(bullets[:2]):
        questions.append(
            {
                "type": "choice",
                "stem": f"关于「{stem_base[:60]}」，下列说法更合适的是？",
                "options": [
                    "与知识库描述一致",
                    "忽略边界条件仍成立",
                    "任意输入规模都 O(1)",
                    "无需定义数据结构",
                ],
                "hint": "对照课程讲义与知识库片段",
                "focus": focus,
                "difficulty": "easy" if i == 0 else "medium",
            }
        )
    questions.append(
        {
            "type": "fill",
            "stem": f"用一句话总结「{_topic_label(topic, module_key)}」的核心思想",
            "hint": bullets[0][:80] if bullets else "参考讲解文档",
            "focus": focus,
            "difficulty": "medium",
        }
    )
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
    outline = _bullet_lines(chunks, 4)
    framework = (
        "def solve():\n"
        "    # TODO: 根据课程知识库要点实现\n"
        "    # 提示：\n"
        + "".join(f"    # - {o[:70]}\n" for o in outline)
        + "    pass\n\n"
        "if __name__ == '__main__':\n"
        "    solve()\n"
    )
    payload = _strip_internal_fields({
        "domain_narrative": {
            "headline": _topic_label(topic, module_key),
            "story": f"围绕「{topic}」的简化实操任务。",
            "mission": "补全代码框架并验证边界",
            "illustration_hint": "课堂白板 + 伪代码",
        },
        "structure_logic": {
            "problem_formalization": outline[0] if outline else topic,
            "data_structures": [module_key or "基础结构"],
            "code_framework": framework,
            "step_hints": outline[:3] or ["读题", "定义状态", "验证边界"],
            "time_complexity": "依实现而定（模板未推断）",
            "space_complexity": "依实现而定",
            "correctness_proof": "请对照知识库片段人工核对",
        },
    })
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
                items.insert(0, f"知识库：{extra}（模板摘要）")
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
