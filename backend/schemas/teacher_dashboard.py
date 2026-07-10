from __future__ import annotations

from pydantic import BaseModel, Field


class ClassLearningOverview(BaseModel):
    student_count: int = 0
    profile_count: int = 0
    average_mastery: float = 0.0
    resource_count: int = 0
    oj_submission_count: int = 0


class WeakKnowledgePoint(BaseModel):
    module_key: str
    module_label: str
    error_count: int
    affected_students: int


class ErrorTypeStat(BaseModel):
    error_type: str
    label: str
    count: int
    percentage: float = 0.0


class TeachingSuggestion(BaseModel):
    title: str
    reason: str
    focus: str


class RecommendedOjProblem(BaseModel):
    slug: str
    title: str


class ReinforcementPack(BaseModel):
    module_key: str
    module_label: str
    resource_types: list[str] = Field(default_factory=list)
    oj_problems: list[RecommendedOjProblem] = Field(default_factory=list)


class TeacherDashboardSummaryResponse(BaseModel):
    overview: ClassLearningOverview
    weak_knowledge_points: list[WeakKnowledgePoint] = Field(default_factory=list)
    error_types: list[ErrorTypeStat] = Field(default_factory=list)
    teaching_suggestions: list[TeachingSuggestion] = Field(default_factory=list)
    reinforcement_packs: list[ReinforcementPack] = Field(default_factory=list)
    data_note: str = ""
    generated_at: str
