"""掌握度评估 API Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field

from services.mastery.models import MasteryReport
from schemas.learning_path import ModuleProgressInput


class MasteryReportResponse(BaseModel):
    course_id: str
    overall_score: int = 50
    overall_level: str = "beginner"
    report: MasteryReport | None = None
    chapters: list[MasteryReport] = Field(default_factory=list)
    updated_at: str = ""


class MasteryRecalculateRequest(BaseModel):
    course_id: str = Field(default="data_structures_algorithms", max_length=64)
    chapter_id: str = Field(default="", max_length=80)
    modules: list[ModuleProgressInput] = Field(default_factory=list)
    overall_percent: int = Field(default=0, ge=0, le=100)


class MasteryRecalculateResponse(BaseModel):
    ok: bool = True
    overview: MasteryReportResponse
