"""学生学习记忆 — 服务层数据结构（与 API schemas 对齐）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MemoryEventInput(BaseModel):
    course_id: str = Field(default="data_structures_algorithms", max_length=64)
    chapter_id: str = Field(default="", max_length=80)
    skill_id: str = Field(default="", max_length=64)
    problem_slug: str = Field(default="", max_length=128)
    event_type: str = Field(min_length=1, max_length=32)
    observed_error_pattern: str = Field(default="", max_length=500)
    trace_summary: str = Field(default="", max_length=2000)
    failed_strategy: str = Field(default="", max_length=500)
    successful_hint: str = Field(default="", max_length=500)
    mastery_delta: int = Field(default=0, ge=-10, le=10)
    evidence_json: dict[str, Any] = Field(default_factory=dict)


class MemoryEventRecord(BaseModel):
    id: int
    user_id: int
    course_id: str
    chapter_id: str = ""
    skill_id: str = ""
    problem_slug: str = ""
    event_type: str
    observed_error_pattern: str = ""
    trace_summary: str = ""
    failed_strategy: str = ""
    successful_hint: str = ""
    mastery_delta: int = 0
    evidence_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_orm_row(cls, row) -> MemoryEventRecord:
        return cls(
            id=row.id,
            user_id=row.user_id,
            course_id=row.course_id or "data_structures_algorithms",
            chapter_id=row.chapter_id or "",
            skill_id=row.skill_id or "",
            problem_slug=row.problem_slug or "",
            event_type=row.event_type,
            observed_error_pattern=row.observed_error_pattern or "",
            trace_summary=row.trace_summary or "",
            failed_strategy=row.failed_strategy or "",
            successful_hint=row.successful_hint or "",
            mastery_delta=int(row.mastery_delta or 0),
            evidence_json=dict(row.evidence_json or {}),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
