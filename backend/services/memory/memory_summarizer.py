"""将最近学习记忆压缩为 Agent / 画像可用的摘要。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from schemas.persona import PROFILE_DIMENSION_KEYS
from services.memory.memory_service import MemoryService, _EVENT_LABELS

_DIMENSION_FOR_EVENT: dict[str, str] = {
    "oj_submit_fail": "coding_ability",
    "oj_diagnosis": "error_preference",
    "trace_diagnosis": "error_preference",
    "evaluation_struggle": "grit_level",
    "resource_complete": "knowledge_base",
    "quiz_complete": "knowledge_base",
    "section_done": "knowledge_base",
    "skill_recommended": "learning_goals",
    "gamified_practice_complete": "knowledge_base",
}


def build_learning_memory_summary(
    db: Session,
    user_id: int,
    *,
    course_id: str = "data_structures_algorithms",
    chapter_id: str = "",
    skill_id: str = "",
    limit: int = 12,
) -> str:
    svc = MemoryService(db)
    rows = svc.list_recent(
        user_id,
        course_id=course_id,
        chapter_id=chapter_id,
        skill_id=skill_id,
        limit=limit,
    )
    if not rows:
        return ""

    lines = ["【学生学习记忆摘要 · 最近错因与实践证据】"]
    for r in rows[:limit]:
        label = _EVENT_LABELS.get(r.event_type, r.event_type)
        parts = [f"- [{r.created_at.isoformat()[:16] if r.created_at else ''}] {label}"]
        if r.problem_slug:
            parts.append(f"题={r.problem_slug}")
        if r.skill_id:
            parts.append(f"技能卡={r.skill_id}")
        if r.observed_error_pattern:
            parts.append(f"错因={r.observed_error_pattern[:120]}")
        if r.trace_summary:
            parts.append(f"Trace={r.trace_summary[:100]}")
        if r.successful_hint:
            parts.append(f"有效提示={r.successful_hint[:80]}")
        lines.append(" ".join(parts))

    weak = svc.aggregate_weak_patterns(user_id, course_id=course_id, limit=5)
    if weak:
        lines.append("高频错因：" + "；".join(weak))

    return "\n".join(lines)


def build_dimension_evidence(
    db: Session,
    user_id: int,
    *,
    course_id: str = "data_structures_algorithms",
    per_dimension: int = 3,
) -> dict[str, list[str]]:
    svc = MemoryService(db)
    rows = svc.list_recent(user_id, course_id=course_id, limit=40)
    bucket: dict[str, list[str]] = {k: [] for k in PROFILE_DIMENSION_KEYS}

    for r in rows:
        dim = _dimension_for_memory(r)
        if dim not in bucket or len(bucket[dim]) >= per_dimension:
            continue
        snippet = _evidence_snippet(r)
        if snippet and snippet not in bucket[dim]:
            bucket[dim].append(snippet)

    return {k: v for k, v in bucket.items() if v}


def build_recent_evidence_items(
    db: Session,
    user_id: int,
    *,
    course_id: str = "data_structures_algorithms",
    limit: int = 3,
) -> list[dict]:
    svc = MemoryService(db)
    rows = svc.list_recent(user_id, course_id=course_id, limit=limit)
    out: list[dict] = []
    for r in rows:
        out.append(
            {
                "id": r.id,
                "event_type": r.event_type,
                "event_label": _EVENT_LABELS.get(r.event_type, r.event_type),
                "problem_slug": r.problem_slug,
                "skill_id": r.skill_id,
                "chapter_id": r.chapter_id,
                "summary": _evidence_snippet(r),
                "at": r.created_at.isoformat() if r.created_at else None,
            }
        )
    return out


def build_update_reason(
    db: Session,
    user_id: int,
    *,
    course_id: str = "data_structures_algorithms",
) -> str:
    svc = MemoryService(db)
    latest = svc.list_recent(user_id, course_id=course_id, limit=1)
    if not latest:
        return ""
    r = latest[0]
    label = _EVENT_LABELS.get(r.event_type, r.event_type)
    if r.observed_error_pattern:
        return f"最近{label}：{r.observed_error_pattern[:80]}"
    if r.trace_summary:
        return f"最近{label}：{r.trace_summary[:80]}"
    return f"最近{label}" + (f"（{r.problem_slug}）" if r.problem_slug else "")


def get_summary_payload(
    db: Session,
    user_id: int,
    *,
    course_id: str = "data_structures_algorithms",
    chapter_id: str = "",
    skill_id: str = "",
    limit: int = 12,
) -> dict:
    from datetime import datetime, timezone

    svc = MemoryService(db)
    return {
        "course_id": course_id,
        "learning_memory_summary": build_learning_memory_summary(
            db,
            user_id,
            course_id=course_id,
            chapter_id=chapter_id,
            skill_id=skill_id,
            limit=limit,
        ),
        "weak_patterns": svc.aggregate_weak_patterns(user_id, course_id=course_id),
        "recent_count": len(
            svc.list_recent(
                user_id,
                course_id=course_id,
                chapter_id=chapter_id,
                skill_id=skill_id,
                limit=limit,
            )
        ),
        "dimension_evidence": build_dimension_evidence(db, user_id, course_id=course_id),
        "update_reason": build_update_reason(db, user_id, course_id=course_id),
        "recent_evidence": build_recent_evidence_items(db, user_id, course_id=course_id, limit=3),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def append_memory_to_profile_block(
    db: Session,
    user_id: int,
    profile_block: str,
    *,
    course_id: str = "data_structures_algorithms",
) -> str:
    summary = build_learning_memory_summary(db, user_id, course_id=course_id)
    if not summary:
        return profile_block
    return f"{profile_block}\n\n{summary}"


def _dimension_for_memory(record) -> str:
    ev = record.evidence_json or {}
    if dim := ev.get("persona_dimension"):
        if dim in PROFILE_DIMENSION_KEYS:
            return str(dim)
    return _DIMENSION_FOR_EVENT.get(record.event_type, "error_preference")


def _evidence_snippet(record) -> str:
    parts: list[str] = []
    if record.observed_error_pattern:
        parts.append(record.observed_error_pattern[:160])
    elif record.trace_summary:
        parts.append(record.trace_summary[:160])
    elif record.failed_strategy:
        parts.append(f"失败策略：{record.failed_strategy[:80]}")
    if record.problem_slug and parts:
        return f"{record.problem_slug}：{parts[0]}"
    return parts[0] if parts else _EVENT_LABELS.get(record.event_type, record.event_type)
