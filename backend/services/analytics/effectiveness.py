"""学习效果统计与导出服务：从 StudentMemory / MasteryReport / OJ 记录聚合。"""

from __future__ import annotations

from collections import defaultdict

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.db_models import StudentLearningMemory


class EffectivenessRow(BaseModel):
    user_id: int
    course_id: str = "data_structures_algorithms"
    chapter_id: str = ""
    skill_id: str = ""
    before_mastery_score: int = 0
    after_mastery_score: int = 0
    mastery_delta: int = 0
    oj_attempts: int = 0
    oj_failures: int = 0
    oj_accept_rate: float = 0.0
    trace_diagnosis_count: int = 0
    hint_count: int = 0
    resource_completion_count: int = 0
    path_adjustment_count: int = 0
    latest_error_pattern: str = ""
    improvement_summary: str = ""


class EffectivenessResponse(BaseModel):
    rows: list[EffectivenessRow] = Field(default_factory=list)
    partial: bool = False
    missing_fields: list[str] = Field(default_factory=list)


def _build_improvement_summary(row: EffectivenessRow) -> str:
    parts: list[str] = []
    if row.mastery_delta > 0:
        parts.append(f"掌握度提升 {row.mastery_delta} 分")
    elif row.mastery_delta < 0:
        parts.append(f"掌握度下降 {abs(row.mastery_delta)} 分")
    if row.oj_attempts > 0:
        parts.append(f"OJ 提交 {row.oj_attempts} 次，通过率 {row.oj_accept_rate:.0%}")
    if row.trace_diagnosis_count > 0:
        parts.append(f"Trace 诊断 {row.trace_diagnosis_count} 次")
    if row.hint_count > 0:
        parts.append(f"有效提示 {row.hint_count} 条")
    if row.resource_completion_count > 0:
        parts.append(f"完成资源 {row.resource_completion_count} 个")
    if row.path_adjustment_count > 0:
        parts.append(f"路径调整 {row.path_adjustment_count} 次")
    if row.latest_error_pattern:
        parts.append(f"最近错因: {row.latest_error_pattern}")
    if not parts:
        return "暂无足够学习行为记录"
    return "；".join(parts)


def compute_effectiveness(
    db: Session,
    user_id: int,
    *,
    course_id: str = "data_structures_algorithms",
    chapter_id: str = "",
) -> EffectivenessResponse:
    q = select(StudentLearningMemory).where(
        StudentLearningMemory.user_id == user_id,
        StudentLearningMemory.course_id == course_id,
    )
    if chapter_id:
        q = q.where(StudentLearningMemory.chapter_id == chapter_id)
    q = q.order_by(StudentLearningMemory.created_at.asc())
    rows = db.scalars(q).all()

    if not rows:
        return EffectivenessResponse(
            rows=[],
            partial=True,
            missing_fields=[
                "student_memory",
                "oj_records",
                "mastery_report",
                "resource_completion",
            ],
        )

    grouped: dict[tuple[str, str], list[StudentLearningMemory]] = defaultdict(list)
    for r in rows:
        key = (r.chapter_id or "", r.skill_id or "")
        grouped[key].append(r)

    result_rows: list[EffectivenessRow] = []
    missing_fields: list[str] = []
    has_oj = False
    has_resource = False
    has_mastery_change = False
    has_trace = False

    for (ch_id, sk_id), mems in grouped.items():
        oj_attempts = 0
        oj_failures = 0
        oj_accepts = 0
        trace_count = 0
        hint_count = 0
        resource_count = 0
        path_adj_count = 0
        latest_error_pattern = ""
        mastery_deltas: list[int] = []

        for m in mems:
            et = m.event_type or ""
            if et == "oj_submit_fail":
                oj_attempts += 1
                oj_failures += 1
                latest_error_pattern = m.observed_error_pattern or m.failed_strategy or ""
            elif et == "oj_submit_success":
                oj_attempts += 1
                oj_accepts += 1
            elif et in ("oj_diagnosis", "trace_diagnosis"):
                trace_count += 1
                if m.successful_hint:
                    hint_count += 1
            elif et == "resource_complete":
                resource_count += 1
            elif et == "section_done":
                resource_count += 1
            elif et == "quiz_complete":
                resource_count += 1
            elif et == "gamified_practice_complete":
                resource_count += 1
            elif et == "evaluation_struggle":
                pass
            if m.mastery_delta != 0:
                mastery_deltas.append(m.mastery_delta)
            ev = m.evidence_json or {}
            if ev.get("path_adjusted"):
                path_adj_count += 1

        if oj_attempts > 0 or oj_failures > 0:
            has_oj = True
        if resource_count > 0:
            has_resource = True
        if mastery_deltas:
            has_mastery_change = True
        if trace_count > 0:
            has_trace = True

        before_mastery = 50
        after_mastery = 50
        if mastery_deltas:
            neg = sum(d for d in mastery_deltas if d < 0)
            pos = sum(d for d in mastery_deltas if d > 0)
            before_mastery = max(0, min(100, 50 + neg))
            after_mastery = max(0, min(100, 50 + neg + pos))

        oj_accept_rate = 0.0
        if oj_attempts > 0:
            oj_accept_rate = oj_accepts / oj_attempts if oj_accepts else 0.0
        elif oj_failures == 0 and resource_count > 0:
            oj_accept_rate = 0.0

        er = EffectivenessRow(
            user_id=user_id,
            course_id=course_id,
            chapter_id=ch_id,
            skill_id=sk_id,
            before_mastery_score=before_mastery,
            after_mastery_score=after_mastery,
            mastery_delta=after_mastery - before_mastery,
            oj_attempts=oj_attempts,
            oj_failures=oj_failures,
            oj_accept_rate=round(oj_accept_rate, 4),
            trace_diagnosis_count=trace_count,
            hint_count=hint_count,
            resource_completion_count=resource_count,
            path_adjustment_count=path_adj_count,
            latest_error_pattern=latest_error_pattern,
        )
        er.improvement_summary = _build_improvement_summary(er)
        result_rows.append(er)

    if not has_oj:
        missing_fields.append("oj_records")
    if not has_resource:
        missing_fields.append("resource_completion")
    if not has_mastery_change:
        missing_fields.append("mastery_report")
    if not has_trace:
        missing_fields.append("trace_diagnosis")

    return EffectivenessResponse(
        rows=result_rows,
        partial=bool(missing_fields),
        missing_fields=missing_fields,
    )


CSV_HEADERS = [
    "user_id",
    "course_id",
    "chapter_id",
    "skill_id",
    "before_mastery_score",
    "after_mastery_score",
    "mastery_delta",
    "oj_attempts",
    "oj_failures",
    "oj_accept_rate",
    "trace_diagnosis_count",
    "hint_count",
    "resource_completion_count",
    "path_adjustment_count",
    "latest_error_pattern",
    "improvement_summary",
]


def build_csv_rows(data: EffectivenessResponse) -> list[list[str]]:
    lines: list[list[str]] = [CSV_HEADERS]
    for r in data.rows:
        lines.append([
            str(r.user_id),
            r.course_id,
            r.chapter_id,
            r.skill_id,
            str(r.before_mastery_score),
            str(r.after_mastery_score),
            str(r.mastery_delta),
            str(r.oj_attempts),
            str(r.oj_failures),
            f"{r.oj_accept_rate:.4f}",
            str(r.trace_diagnosis_count),
            str(r.hint_count),
            str(r.resource_completion_count),
            str(r.path_adjustment_count),
            r.latest_error_pattern,
            r.improvement_summary,
        ])
    return lines
