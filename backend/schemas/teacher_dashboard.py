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


# --- 学情管理：学生花名册 ---

class StudentRosterItem(BaseModel):
    user_id: int
    username: str
    created_at: str = ""
    mastery_score: float = 0.0
    progress_percent: float = 0.0
    profile_summary: str = ""
    oj_submissions: int = 0
    oj_accepted: int = 0
    resource_count: int = 0
    weak_modules: list[str] = Field(default_factory=list)
    last_active: str = ""


class StudentRosterResponse(BaseModel):
    total: int = 0
    students: list[StudentRosterItem] = Field(default_factory=list)
    generated_at: str = ""


class StudentDetailModuleProgress(BaseModel):
    module_key: str
    module_label: str
    percent: float = 0.0
    mastery_score: float = 0.0


class StudentDetailResponse(BaseModel):
    user_id: int
    username: str
    created_at: str = ""
    mastery_score: float = 0.0
    progress_percent: float = 0.0
    profile_summary: str = ""
    profile_dimensions: dict = Field(default_factory=dict)
    oj_submissions: int = 0
    oj_accepted: int = 0
    resource_count: int = 0
    weak_modules: list[str] = Field(default_factory=list)
    last_active: str = ""
    module_progress: list[StudentDetailModuleProgress] = Field(default_factory=list)
    recent_memories: list[dict] = Field(default_factory=list)


# --- OJ 学情分析 ---

class OjProblemStat(BaseModel):
    slug: str
    title: str
    module_key: str = ""
    module_label: str = ""
    difficulty: str = ""
    total_submissions: int = 0
    accepted: int = 0
    acceptance_rate: float = 0.0
    common_errors: list[str] = Field(default_factory=list)


class OjModuleStat(BaseModel):
    module_key: str
    module_label: str
    total_submissions: int = 0
    accepted: int = 0
    acceptance_rate: float = 0.0


class OjAnalyticsResponse(BaseModel):
    total_submissions: int = 0
    accepted: int = 0
    acceptance_rate: float = 0.0
    active_students: int = 0
    per_problem: list[OjProblemStat] = Field(default_factory=list)
    per_module: list[OjModuleStat] = Field(default_factory=list)
    generated_at: str = ""
