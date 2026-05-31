"""学生学习记忆 API Schema。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from services.memory.schemas import MemoryEventInput, MemoryEventRecord


class MemoryEventCreateRequest(MemoryEventInput):
    """POST /api/memory/events 请求体。"""


class MemoryEventCreateResponse(BaseModel):
    ok: bool = True
    event: MemoryEventRecord


class LearningEvidenceItem(BaseModel):
    id: int
    event_type: str
    event_label: str = ""
    problem_slug: str = ""
    skill_id: str = ""
    chapter_id: str = ""
    summary: str = ""
    at: str | None = None


class MemorySummaryResponse(BaseModel):
    course_id: str
    learning_memory_summary: str = ""
    weak_patterns: list[str] = Field(default_factory=list)
    recent_count: int = 0
    dimension_evidence: dict[str, list[str]] = Field(default_factory=dict)
    update_reason: str = ""
    recent_evidence: list[LearningEvidenceItem] = Field(default_factory=list)
    generated_at: str = ""


class MemoryRecentResponse(BaseModel):
    items: list[MemoryEventRecord] = Field(default_factory=list)
    total: int = 0
