"""随学随新：根据学习行为轻量更新六维画像。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models.db_models import StudentProfile
from schemas.evaluation import PersonaLearningPatchRequest
from schemas.persona import PersonaDimensions, PROFILE_DIMENSION_KEYS
from services.agents.learning_path_catalog import MODULE_CATALOG
from services.oj.error_patterns import ERROR_TYPE_LABELS

_MODULE_LABELS = {m["key"]: m["label"] for m in MODULE_CATALOG}

# 错因类型 → 主要影响维度（赛题随学随新映射）
ERROR_TO_PERSONA_DIMENSIONS: dict[str, list[str]] = {
    "initialization_error": ["coding_ability", "error_preference"],
    "boundary_condition_error": ["coding_ability", "error_preference"],
    "pointer_update_error": ["coding_ability", "knowledge_base"],
    "recursion_base_case_error": ["knowledge_base", "cognitive_style"],
    "state_transition_error": ["knowledge_base", "cognitive_style"],
    "time_complexity_issue": ["knowledge_base", "coding_ability"],
    "loop_condition_error": ["coding_ability", "error_preference"],
    "data_structure_misuse": ["knowledge_base", "error_preference"],
    "unknown": ["error_preference", "coding_ability"],
}

_DIMENSION_LABELS: dict[str, str] = {
    "knowledge_base": "知识基础",
    "cognitive_style": "认知风格",
    "coding_ability": "代码实操能力",
    "learning_goals": "学习目标",
    "error_preference": "易错点偏好",
    "grit_level": "抗挫折心理",
}


@dataclass
class OjPersonaPatchResult:
    updated: bool
    summary: str = ""
    warning: str = ""


def dimensions_for_error_type(error_type: str, *, repeated_failure: bool = False) -> list[str]:
    keys = list(ERROR_TO_PERSONA_DIMENSIONS.get(error_type, ["error_preference"]))
    if repeated_failure:
        for k in ("grit_level", "error_preference"):
            if k not in keys:
                keys.append(k)
    return [k for k in keys if k in PROFILE_DIMENSION_KEYS]


def apply_learning_patch(
    summary: str,
    dimensions: PersonaDimensions,
    body: PersonaLearningPatchRequest,
) -> tuple[str, PersonaDimensions]:
    dims = dimensions.model_dump()
    weak_keys = list(dict.fromkeys(body.weak_module_keys))[:8]
    weak_labels = [_MODULE_LABELS.get(k, k) for k in weak_keys if k]

    if weak_labels:
        dims["error_preference"] = f"近期易错/待加强：{'、'.join(weak_labels)}"
    elif body.signals:
        visited = list(dict.fromkeys(s.module_key for s in body.signals if s.module_key))[:5]
        if visited:
            prev = dims.get("error_preference") or "待补充"
            suffix = f"近期学习模块：{'、'.join(_MODULE_LABELS.get(k, k) for k in visited)}"
            dims["error_preference"] = suffix if _is_pending(prev) else f"{prev}；{suffix}"

    done_modules = [s for s in body.signals if s.event_type == "section_done" and s.module_key]
    if done_modules:
        labels = [_MODULE_LABELS.get(s.module_key, s.module_key) for s in done_modules[-5:]]
        prev = dims.get("knowledge_base") or "待补充"
        if _is_pending(prev):
            dims["knowledge_base"] = f"已完成小节：{'、'.join(labels)}"
        elif not any(lbl in prev for lbl in labels):
            dims["knowledge_base"] = f"{prev}；近期完成：{'、'.join(labels[-3:])}"

    oj_events = [s for s in body.signals if s.event_type == "oj_submit"]
    if oj_events:
        prev = dims.get("coding_ability") or "待补充"
        patch = "含 OJ 刷题实践，代码实操能力随练习提升"
        dims["coding_ability"] = patch if _is_pending(prev) else f"{prev}；{patch}"
        wa_count = sum(1 for e in oj_events if getattr(e, "verdict", "") in ("WA", "RE", "TLE"))
        if wa_count >= 2:
            grit_prev = dims.get("grit_level") or "待补充"
            grit_patch = "多次提交未过仍继续尝试，抗挫折能力中等偏上"
            dims["grit_level"] = grit_patch if _is_pending(grit_prev) else f"{grit_prev}；{grit_patch}"

    new_summary = summary
    if weak_labels:
        new_summary = f"计科算法学习者，当前需加强 {'、'.join(weak_labels[:3])}。"
    elif done_modules and (not summary or summary == "画像待完善"):
        new_summary = "已通过平台学习数据结构与算法相关模块，画像随学更新中。"

    return new_summary.strip() or summary, PersonaDimensions.model_validate(dims)


def _is_pending(val: str) -> bool:
    v = (val or "").strip()
    return not v or v in ("待补充", "暂无", "未知")


def _merge_text(prev: str, patch: str, *, max_len: int = 480) -> str:
    p = (patch or "").strip()
    if not p:
        return prev
    if _is_pending(prev):
        return p[:max_len]
    if p in prev:
        return prev[:max_len]
    merged = f"{prev}；{p}"
    return merged[:max_len]


def _patch_text_for_dimension(
    dim_key: str,
    *,
    error_type: str,
    error_label: str,
    problem_slug: str,
    trace_summary: str,
    hint_level: int,
    repeated_failure: bool,
) -> str:
    slug = problem_slug or "OJ 题目"
    label = error_label or ERROR_TYPE_LABELS.get(error_type, error_type)
    trace_hint = (trace_summary or "")[:80]

    if dim_key == "coding_ability":
        return f"OJ Trace 诊断：{label}（{slug}）"
    if dim_key == "error_preference":
        base = f"近期错因模式：{label}"
        if trace_hint:
            return f"{base} · {trace_hint}"
        return base
    if dim_key == "knowledge_base":
        if error_type in ("state_transition_error", "recursion_base_case_error"):
            return f"状态/递推理解待加强：{label}（{slug}）"
        if error_type == "pointer_update_error":
            return f"指针/链表操作需巩固：{slug}"
        return f"知识点待加强：{label}（{slug}）"
    if dim_key == "cognitive_style":
        if error_type in ("state_transition_error", "recursion_base_case_error"):
            return "建议先纸笔推演状态转移/递归基线，再写代码（Trace 诊断反馈）"
        return "偏好分步 Trace 调试后再提交（诊断建议）"
    if dim_key == "grit_level" and repeated_failure:
        return f"连续 {hint_level}+ 次诊断/提交未过仍坚持调试，抗挫折能力待观察"
    return ""


def apply_oj_diagnosis_patch(
    db: Session,
    user_id: int,
    *,
    course_id: str = "data_structures_algorithms",
    chapter_id: str = "",
    skill_id: str = "",
    problem_slug: str = "",
    error_type: str = "unknown",
    error_pattern_label: str = "",
    trace_summary: str = "",
    hint_level: int = 1,
    module_key: str = "",
    repeated_failure: bool = False,
    mastery_delta: int = 0,
) -> OjPersonaPatchResult:
    """OJ / Trace 诊断完成后更新六维画像；失败时不抛出异常。"""
    try:
        row = db.get(StudentProfile, user_id)
        if row is None:
            row = StudentProfile(user_id=user_id, dimensions={}, summary="")
            db.add(row)

        dims = PersonaDimensions.from_storage(row.dimensions or {})
        payload = dims.model_dump()
        affected: list[str] = []

        for dim_key in dimensions_for_error_type(error_type, repeated_failure=repeated_failure):
            patch = _patch_text_for_dimension(
                dim_key,
                error_type=error_type,
                error_label=error_pattern_label,
                problem_slug=problem_slug,
                trace_summary=trace_summary,
                hint_level=hint_level,
                repeated_failure=repeated_failure,
            )
            if not patch:
                continue
            payload[dim_key] = _merge_text(payload.get(dim_key, ""), patch)
            affected.append(dim_key)

        if not affected:
            return OjPersonaPatchResult(
                updated=False,
                summary="",
                warning="未识别可更新的画像维度",
            )

        error_label = error_pattern_label or ERROR_TYPE_LABELS.get(error_type, error_type)
        dim_labels = "、".join(_DIMENSION_LABELS.get(k, k) for k in affected[:4])
        summary_line = (
            f"六维画像已更新：{dim_labels}（OJ 诊断：{error_label}"
            f"{f' · {problem_slug}' if problem_slug else ''}）"
        )

        if _is_pending(row.summary or ""):
            row.summary = f"算法学习者，画像随 OJ Trace 诊断更新（{error_label}）。"
        elif error_label not in (row.summary or ""):
            row.summary = _merge_text(row.summary or "", f"近期 OJ 错因：{error_label}", max_len=600)

        try:
            from services.memory.memory_summarizer import (
                build_dimension_evidence,
                build_recent_evidence_items,
                build_update_reason,
            )

            payload["_dimension_evidence"] = build_dimension_evidence(db, user_id, course_id=course_id)
            payload["_update_reason"] = (
                build_update_reason(db, user_id, course_id=course_id)
                or f"OJ 诊断随学随新：{error_label}"
            )
            payload["_recent_evidence"] = build_recent_evidence_items(
                db, user_id, course_id=course_id, limit=3
            )
        except Exception:
            payload["_update_reason"] = f"OJ 诊断随学随新：{error_label}"

        payload["_last_oj_patch"] = {
            "error_type": error_type,
            "problem_slug": problem_slug,
            "skill_id": skill_id,
            "chapter_id": chapter_id,
            "module_key": module_key,
            "mastery_delta": mastery_delta,
            "affected_dimensions": affected,
            "at": datetime.now(timezone.utc).isoformat(),
        }

        row.dimensions = payload
        row.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(row)
        return OjPersonaPatchResult(updated=True, summary=summary_line)
    except Exception as exc:
        db.rollback()
        return OjPersonaPatchResult(
            updated=False,
            summary="",
            warning=f"画像 patch 失败：{exc}",
        )
