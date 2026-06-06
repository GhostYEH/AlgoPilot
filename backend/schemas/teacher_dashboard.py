from __future__ import annotations

from pydantic import BaseModel


class ClassOverviewResponse(BaseModel):
    student_count: int
    avg_mastery: float
    active_rate_7d: float
    oj_accept_rate: float
    error_type_distribution: dict[str, int]
    is_demo: bool = False


class WeakModuleItem(BaseModel):
    module_key: str
    module_label: str
    avg_mastery: float
    error_count: int


class WeakKnowledgeItem(BaseModel):
    knowledge_point: str
    error_count: int
    typical_error: str


class WeakProblemTypeItem(BaseModel):
    problem_slug: str
    problem_title: str
    wa_count: int
    tle_count: int


class WeakPointsResponse(BaseModel):
    weak_modules: list[WeakModuleItem]
    weak_knowledge_points: list[WeakKnowledgeItem]
    weak_problem_types: list[WeakProblemTypeItem]
    recommended_teaching_focus: list[str]
    is_demo: bool = False


class ResourceStatItem(BaseModel):
    resource_type: str
    resource_label: str
    count: int
    usage_rate: float
    avg_feedback_score: float


class ResourceStatsResponse(BaseModel):
    resource_stats: list[ResourceStatItem]
    recommended_supplements: list[str]
    is_demo: bool = False


class StrugglingStudentItem(BaseModel):
    user_id: int
    username: str
    consecutive_failures: int
    last_problem: str
    suggested_action: str


class HighPerformerItem(BaseModel):
    user_id: int
    username: str
    ac_count: int
    avg_mastery: float
    suggested_project: str


class InterventionResponse(BaseModel):
    struggling_students: list[StrugglingStudentItem]
    class_common_issues: list[str]
    suggested_topic_resources: list[str]
    high_performers: list[HighPerformerItem]
    is_demo: bool = False
