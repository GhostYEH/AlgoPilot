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


class StudentOjRecentSubmission(BaseModel):
    """最近 OJ 提交摘要。"""
    problem_slug: str = ""
    problem_title: str = ""
    verdict: str = ""
    passed: int = 0
    total: int = 0
    runtime_ms: int = 0
    language: str = ""
    created_at: str = ""


class StudentOjVerdictStat(BaseModel):
    """OJ 提交按 verdict 分布。"""
    verdict: str
    label: str
    count: int = 0
    color: str = ""


class StudentErrorTypeStat(BaseModel):
    """学生错误类型分布。"""
    error_type: str
    label: str
    count: int = 0


class StudentResourceTypeStat(BaseModel):
    """学生资源类型分布。"""
    resource_type: str
    label: str
    count: int = 0


class StudentActivityItem(BaseModel):
    """学生活跃时间线条目。"""
    event_type: str
    label: str
    description: str = ""
    created_at: str = ""
    icon: str = ""


class StudentSkillMastery(BaseModel):
    """按技能维度的掌握度。"""
    skill_id: str
    skill_label: str
    mastery_score: float = 0.0
    sample_count: int = 0


class StudentProfileDimensionStat(BaseModel):
    """六维画像量化分项。"""
    key: str
    label: str
    text: str = ""
    score: int = 0  # 1-10 量化分
    confidence: str = ""  # explicit/inferred


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
    # ====== 学情详情可视化扩展字段 ======
    dimension_stats: list[StudentProfileDimensionStat] = Field(default_factory=list)
    oj_verdict_breakdown: list[StudentOjVerdictStat] = Field(default_factory=list)
    oj_recent_submissions: list[StudentOjRecentSubmission] = Field(default_factory=list)
    error_type_breakdown: list[StudentErrorTypeStat] = Field(default_factory=list)
    resource_type_breakdown: list[StudentResourceTypeStat] = Field(default_factory=list)
    activity_timeline: list[StudentActivityItem] = Field(default_factory=list)
    skill_mastery: list[StudentSkillMastery] = Field(default_factory=list)
    learning_streak_days: int = 0
    profile_completeness: float = 0.0  # 画像完成度 0-100
    data_completeness_note: str = ""


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
