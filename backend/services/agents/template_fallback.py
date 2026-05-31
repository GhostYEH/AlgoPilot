"""无 LLM Key 或 LLM 不可用时的课程知识库模板降级生成（TemplateFallbackAgent）。"""

from __future__ import annotations

import json
import re
from typing import Any

from schemas.resources import ResourceType
from services.agents.resource_roles import (
    PersonaHints,
    PptAgent,
    VideoScriptAgent,
    _fallback_reading_levels,
    _fallback_trace_payload,
)
from services.knowledge.retriever import KnowledgeChunk, format_context_block
from services.verification.builder import chunks_to_grounded

GENERATED_BY = "TemplateFallbackAgent"

_DISCLAIMER = (
    "> ⚠️ **模板降级资源**（{agent}）\n"
    "> 原因：{reason}\n"
    "> 本内容由课程知识库片段与固定模板拼装，**非大模型生成**。配置 SPARK_API_PASSWORD 后可启用多智能体高质量生成。\n\n"
)


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
        "ppt": "PPT 预览",
        "video_script": "短视频脚本",
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
    excerpt = format_context_block(chunks) if chunks else "（未命中知识库片段，仅提供主题提纲）"
    body = "\n".join(f"- {b}" for b in bullets)
    content = (
        _DISCLAIMER.format(agent=GENERATED_BY, reason=fallback_reason)
        + f"## {_topic_label(topic, module_key)}\n\n"
        + "### 知识库要点\n\n"
        + body
        + "\n\n### 检索片段摘要\n\n"
        + excerpt[:2400]
    )
    meta = {
        "format": "markdown",
        "template": "document_from_chunks",
    }
    return _build_title("document", topic, module_key), content, meta


def generate_mindmap(
    *,
    topic: str,
    module_key: str,
    chunks: list[KnowledgeChunk],
    fallback_reason: str,
) -> tuple[str, str, dict]:
    root = _topic_label(topic, module_key).replace('"', "'")
    nodes = _bullet_lines(chunks, 6)
    lines = [f'flowchart TD\n  root["{root}"]']
    for i, n in enumerate(nodes):
        label = n[:36].replace('"', "'").replace("\n", " ")
        lines.append(f'  root --> n{i}["{label}"]')
    if len(lines) == 1:
        lines.append('  root --> n0["核心概念"]')
    content = _DISCLAIMER.format(agent=GENERATED_BY, reason=fallback_reason) + "\n".join(lines)
    return _build_title("mindmap", topic, module_key), content, {"format": "mermaid", "template": "mindmap_from_chunks"}


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
            "hint": bullets[0][:80] if bullets else "参考 document 模板",
            "focus": focus,
            "difficulty": "medium",
        }
    )
    payload = {
        "_template_disclaimer": fallback_reason,
        "questions": questions,
    }
    content = _DISCLAIMER.format(agent=GENERATED_BY, reason=fallback_reason) + json.dumps(
        payload, ensure_ascii=False, indent=2
    )
    return _build_title("exercises", topic, module_key), content, {"format": "quiz_json", "template": "quiz_from_chunks"}


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
    payload = {
        "domain_narrative": {
            "headline": _topic_label(topic, module_key),
            "story": f"围绕「{topic}」的简化实操任务（模板降级，非 LLM 剧本）。",
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
        "_template_disclaimer": fallback_reason,
    }
    content = _DISCLAIMER.format(agent=GENERATED_BY, reason=fallback_reason) + json.dumps(
        payload, ensure_ascii=False, indent=2
    )
    return _build_title("code_case", topic, module_key), content, {"format": "scenario_json", "template": "code_from_chunks"}


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
    payload = {
        "topic": _topic_label(topic, module_key),
        "levels": levels,
        "_template_disclaimer": fallback_reason,
    }
    content = _DISCLAIMER.format(agent=GENERATED_BY, reason=fallback_reason) + json.dumps(
        payload, ensure_ascii=False, indent=2
    )
    return _build_title("reading", topic, module_key), content, {"format": "reading_json", "template": "reading_template"}


def generate_trace_placeholder(
    *,
    topic: str,
    module_key: str,
    fallback_reason: str,
) -> tuple[str, str, dict]:
    reason = "轨迹动画需 LLM 生成可执行代码或接入 Trace Runner；模板模式仅提供占位示例"
    payload = _fallback_trace_payload(topic=_topic_label(topic, module_key))
    payload["placeholder"] = True
    payload["placeholder_reason"] = reason
    payload["fallback_reason"] = fallback_reason
    content = _DISCLAIMER.format(agent=GENERATED_BY, reason=fallback_reason) + json.dumps(
        payload, ensure_ascii=False, indent=2
    )
    meta = {
        "format": "trace_json",
        "template": "trace_placeholder",
        "placeholder": True,
        "placeholder_reason": reason,
        "trace_verdict": "SKIPPED",
        "trace_steps": 0,
    }
    return _build_title("trace_animation", topic, module_key), content, meta


def generate_ppt_placeholder(
    *,
    topic: str,
    module_key: str,
    chunks: list[KnowledgeChunk],
    hints: PersonaHints,
    fallback_reason: str,
) -> tuple[str, str, dict]:
    reason = "PPT 分镜需 LLM 润色；模板模式使用固定胶片结构 + 知识库要点"
    agent = PptAgent()
    raw = agent.normalize_output("", hints=hints)
    data = json.loads(raw)
    if chunks:
        bullets = _bullet_lines(chunks, 3)
        slides = data.get("slides") or []
        if slides and bullets:
            slides[0]["bullets"] = bullets[:3]
    data["placeholder"] = True
    data["placeholder_reason"] = reason
    content = _DISCLAIMER.format(agent=GENERATED_BY, reason=fallback_reason) + json.dumps(
        data, ensure_ascii=False, indent=2
    )
    meta = {
        "format": "ppt_preview_json",
        "template": "ppt_placeholder",
        "placeholder": True,
        "placeholder_reason": reason,
    }
    return _build_title("ppt", topic, module_key), content, meta


def generate_video_placeholder(
    *,
    topic: str,
    module_key: str,
    hints: PersonaHints,
    fallback_reason: str,
) -> tuple[str, str, dict]:
    reason = "短视频脚本需 LLM 分镜；模板模式使用固定 60 秒结构"
    agent = VideoScriptAgent()
    raw = agent.normalize_output("", hints=hints)
    data = json.loads(raw)
    data["placeholder"] = True
    data["placeholder_reason"] = reason
    content = _DISCLAIMER.format(agent=GENERATED_BY, reason=fallback_reason) + json.dumps(
        data, ensure_ascii=False, indent=2
    )
    meta = {
        "format": "video_script_json",
        "template": "video_placeholder",
        "placeholder": True,
        "placeholder_reason": reason,
    }
    return _build_title("video_script", topic, module_key), content, meta


def generate_fallback_resource(
    resource_type: ResourceType,
    *,
    topic: str,
    profile_block: str,
    module_key: str = "",
    chunks: list[KnowledgeChunk],
    fallback_reason: str,
) -> tuple[str, str, dict]:
    hints = PersonaHints.from_profile_block(profile_block)
    generators = {
        "document": lambda: generate_document(
            topic=topic, module_key=module_key, chunks=chunks, fallback_reason=fallback_reason
        ),
        "mindmap": lambda: generate_mindmap(
            topic=topic, module_key=module_key, chunks=chunks, fallback_reason=fallback_reason
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
        "ppt": lambda: generate_ppt_placeholder(
            topic=topic, module_key=module_key, chunks=chunks, hints=hints, fallback_reason=fallback_reason
        ),
        "video_script": lambda: generate_video_placeholder(
            topic=topic, module_key=module_key, hints=hints, fallback_reason=fallback_reason
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
