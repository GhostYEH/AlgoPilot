"""掌握度评估数据结构。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

MasteryLevel = Literal["beginner", "improving", "competent", "advanced"]
MasteryTrend = Literal["rising", "stable", "falling"]
ConfidenceLevel = Literal["low", "medium", "high"]

MASTERY_LEVEL_THRESHOLDS: list[tuple[int, MasteryLevel]] = [
    (80, "advanced"),
    (60, "competent"),
    (40, "improving"),
    (0, "beginner"),
]


class MasteryComponentScore(BaseModel):
    key: str
    label: str
    score: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    weighted: float = 0.0
    data_available: bool = True
    note: str = ""


class MasteryEvidenceItem(BaseModel):
    source: str = ""
    detail: str = ""
    at: str | None = None


class MasteryResourceHint(BaseModel):
    resource_type: str
    topic: str = ""
    reason: str = ""


class MasteryReport(BaseModel):
    user_id: int
    course_id: str = "data_structures_algorithms"
    chapter_id: str = ""
    chapter_title: str = ""
    mastery_score: int = Field(ge=0, le=100, default=50)
    mastery_level: MasteryLevel = "beginner"
    weak_skills: list[str] = Field(default_factory=list)
    strong_skills: list[str] = Field(default_factory=list)
    evidence: list[MasteryEvidenceItem] = Field(default_factory=list)
    component_scores: list[MasteryComponentScore] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    recommended_resources: list[MasteryResourceHint] = Field(default_factory=list)
    path_adjustment_suggestion: str = ""
    mastery_probability: float = Field(ge=0.0, le=1.0, default=0.5)
    mastery_trend: MasteryTrend = "stable"
    confidence_level: ConfidenceLevel = "low"
    probability_explanation: str = ""
    updated_at: str = ""

    @classmethod
    def default_for_user(
        cls,
        user_id: int,
        *,
        course_id: str = "data_structures_algorithms",
        chapter_id: str = "",
        chapter_title: str = "",
    ) -> MasteryReport:
        now = datetime.utcnow().isoformat()
        return cls(
            user_id=user_id,
            course_id=course_id,
            chapter_id=chapter_id,
            chapter_title=chapter_title or ("课程总览" if not chapter_id else chapter_id),
            mastery_score=50,
            mastery_level="beginner",
            evidence=[
                MasteryEvidenceItem(
                    source="default",
                    detail="暂无学习行为记录，使用默认掌握度 50（beginner）",
                    at=now,
                )
            ],
            component_scores=[],
            recommended_actions=["完成章节学习与 OJ 练习以生成可解释评估"],
            recommended_resources=[
                MasteryResourceHint(
                    resource_type="document",
                    topic="课程导学",
                    reason="建立基础概念框架",
                )
            ],
            path_adjustment_suggestion="按课程默认章节顺序学习，完成破冰画像后获取个性化路径",
            updated_at=now,
        )


class MasteryCourseOverview(BaseModel):
    course_id: str
    overall_score: int = 50
    overall_level: MasteryLevel = "beginner"
    chapters: list[MasteryReport] = Field(default_factory=list)
    report: MasteryReport | None = None
    updated_at: str = ""


class MasterySignals(BaseModel):
    """从记忆与进度提取的原始信号。"""

    quiz_total: int = 0
    quiz_correct: int = 0
    oj_failures: int = 0
    oj_diagnoses: int = 0
    resource_completions: int = 0
    section_completions: int = 0
    struggle_events: int = 0
    positive_deltas: int = 0
    negative_deltas: int = 0
    recent_fail_patterns: list[str] = Field(default_factory=list)
    older_fail_patterns: list[str] = Field(default_factory=list)
    trace_with_hints: int = 0
    skill_fail_counts: dict[str, int] = Field(default_factory=dict)
    skill_success_counts: dict[str, int] = Field(default_factory=dict)
    module_percents: dict[str, int] = Field(default_factory=dict)
    self_report_score: float | None = None
    memory_event_count: int = 0
    gamified_practice_count: int = 0

    model_config = {"extra": "allow"}


def mastery_level_from_score(score: int) -> MasteryLevel:
    for threshold, level in MASTERY_LEVEL_THRESHOLDS:
        if score >= threshold:
            return level
    return "beginner"
