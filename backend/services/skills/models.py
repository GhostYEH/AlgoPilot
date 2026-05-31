"""Learning SkillCard 算法学习技能卡 — Pydantic 模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SkillTriggerSpec(BaseModel):
    """命中条件：关键词、模块、判题结果、错误模式等。"""

    keywords: list[str] = Field(default_factory=list)
    module_keys: list[str] = Field(default_factory=list)
    chapter_ids: list[str] = Field(default_factory=list)
    oj_verdicts: list[str] = Field(default_factory=list)
    error_patterns: list[str] = Field(default_factory=list)
    min_consecutive_failures: int = Field(default=0, ge=0, le=20)


class SkillMistakeItem(BaseModel):
    text: str = Field(min_length=4, max_length=500)
    severity: str = Field(default="medium", pattern=r"^(low|medium|high)$")
    detector_hint: str = Field(default="", max_length=200)


class SkillResourceStrategy(BaseModel):
    """按资源类型的生成约束（写入 Agent 上下文）。"""

    document: str = ""
    mindmap: str = ""
    exercises: str = ""
    code_case: str = ""
    trace_animation: str = ""
    ppt: str = ""
    video_script: str = ""
    reading: str = ""
    default: str = Field(
        default="",
        description="未指定类型时使用的通用策略",
    )

    def for_resource_type(self, resource_type: str) -> str:
        val = getattr(self, resource_type, None) or ""
        return val.strip() or self.default.strip()


class SkillHintLevel(BaseModel):
    level: int = Field(ge=1, le=4)
    policy: str = Field(min_length=8, max_length=800)


class SkillHintPolicy(BaseModel):
    max_code_lines: int = Field(default=0, ge=0, description="0=不直接给完整代码")
    forbid_full_solution: bool = True
    socratic: bool = True
    levels: list[SkillHintLevel] = Field(default_factory=list)
    escalation_after_failures: int = Field(default=2, ge=1, le=10)


class SkillEvaluationRule(BaseModel):
    rule_id: str = Field(min_length=2, max_length=64)
    description: str = Field(min_length=8, max_length=400)
    weight: float = Field(default=0.25, ge=0.0, le=1.0)
    pass_threshold: int = Field(default=60, ge=0, le=100)


class SkillCard(BaseModel):
    id: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=120)
    course_id: str = Field(default="data_structures_algorithms")
    chapter_id: str = Field(default="", max_length=80)
    description: str = Field(min_length=20, max_length=2000)
    prerequisites: list[str] = Field(default_factory=list)
    triggers: SkillTriggerSpec = Field(default_factory=SkillTriggerSpec)
    common_mistakes: list[SkillMistakeItem] = Field(default_factory=list, min_length=1)
    resource_strategy: SkillResourceStrategy = Field(default_factory=SkillResourceStrategy)
    hint_policy: SkillHintPolicy = Field(default_factory=SkillHintPolicy)
    trace_focus: list[str] = Field(default_factory=list)
    evaluation_rules: list[SkillEvaluationRule] = Field(default_factory=list)
    recommended_resources: list[str] = Field(default_factory=list)
    recommended_problems: list[str] = Field(default_factory=list)


class SkillCardSummary(BaseModel):
    id: str
    name: str
    course_id: str
    chapter_id: str
    description: str = ""


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


class SkillRouteMatch(BaseModel):
    skill_id: str
    name: str
    score: float = Field(ge=0.0)
    reasons: list[str] = Field(default_factory=list)


class SkillRouteResponse(BaseModel):
    primary: SkillCardSummary | None = None
    matches: list[SkillRouteMatch] = Field(default_factory=list)
    skill_card: SkillCard | None = Field(
        default=None,
        description="完整技能卡（仅 route 详情或内部编排使用）",
    )
