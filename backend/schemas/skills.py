"""SkillCard API Schema（OpenAPI 用，避免 schemas ↔ services 循环导入）。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SkillCardSummary(BaseModel):
    id: str
    name: str
    course_id: str
    chapter_id: str = ""
    description: str = ""


class SkillRouteMatch(BaseModel):
    skill_id: str
    name: str
    score: float = Field(ge=0.0)
    reasons: list[str] = Field(default_factory=list)


class SkillRouteRequest(BaseModel):
    course_id: str = Field(default="data_structures_algorithms", max_length=64)
    chapter_id: str = Field(default="", max_length=80)
    module_key: str = Field(default="", max_length=64)
    topic: str = Field(default="", max_length=300)
    user_query: str = Field(default="", max_length=1000)
    profile_summary: str = Field(default="", max_length=500)
    profile_block: str = Field(default="", max_length=4000)
    oj_verdict: str = Field(default="", max_length=16)
    error_pattern: str = Field(default="", max_length=300)
    trace_summary: str = Field(default="", max_length=2000)
    consecutive_failures: int = Field(default=0, ge=0, le=20)
    top_k: int = Field(default=3, ge=1, le=10)


class SkillRouteResponse(BaseModel):
    primary: SkillCardSummary | None = None
    matches: list[SkillRouteMatch] = Field(default_factory=list)
    skill_card: dict | None = Field(
        default=None,
        description="完整技能卡 JSON（可选，供调试）",
    )
