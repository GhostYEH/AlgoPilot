from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, computed_field


class ProblemListItem(BaseModel):
    slug: str
    title: str
    lc_id: int = 0
    difficulty: str = "medium"
    ready: bool = False
    course_id: str = "data_structures_algorithms"
    chapter_id: str = ""
    module_key: str = ""
    skill_id: str = ""
    tags: list[str] = Field(default_factory=list)
    common_errors: list[str] = Field(default_factory=list)


class ProblemDetail(BaseModel):
    slug: str
    title: str
    lc_id: int = 0
    difficulty: str = "medium"
    description: str
    judge_mode: str = "stdio"
    entry: dict[str, Any] | None = None
    starter_code: dict[str, str] = Field(default_factory=dict)
    samples: list[dict[str, Any]] = Field(default_factory=list)
    hidden_count: int = 0
    ready: bool = False
    time_limit_ms: int = 3000
    order_insensitive: bool = False
    course_id: str = "data_structures_algorithms"
    chapter_id: str = ""
    module_key: str = ""
    skill_id: str = ""
    tags: list[str] = Field(default_factory=list)
    common_errors: list[str] = Field(default_factory=list)


class JudgeRequest(BaseModel):
    code: str
    language: str = "python"


class TraceRequest(BaseModel):
    code: str
    language: str = "python"
    """指定追踪的测例下标（run 模式样例列表）；缺省则自动选取。"""
    case_index: int | None = None


class CaseResultOut(BaseModel):
    index: int
    verdict: Literal["AC", "WA", "TLE", "RE", "CE"]
    message: str
    input_preview: str
    expected_preview: str
    actual_preview: str | None = None
    runtime_ms: int | None = None


class JudgeResponse(BaseModel):
    verdict: Literal["AC", "WA", "TLE", "RE", "CE"]
    passed: int
    total: int
    cases: list[CaseResultOut]
    compile_error: str | None = None
    event_id: str | None = None
    event_logs: list[dict[str, str]] = Field(default_factory=list)


class TraceVarSnapshot(BaseModel):
    type: str
    value: Any = None
    view_hint: str | None = None


class TraceStepOut(BaseModel):
    line: int
    vars: dict[str, TraceVarSnapshot] = Field(default_factory=dict)
    changed: list[str] = Field(default_factory=list)


class TraceNarrationLine(BaseModel):
    step_index: int
    text: str
    critical: bool = False


class TraceNarrateRequest(BaseModel):
    code: str
    language: str = "python"
    steps: list[TraceStepOut] = Field(default_factory=list)
    problem_title: str = ""


class StaticAuditRejection(BaseModel):
    status: Literal["rejected"] = "rejected"
    agent: str = "ASTAnalyzerAgent"
    reason: str
    findings: list[dict[str, Any]] = Field(default_factory=list)


class TraceResponse(BaseModel):
    verdict: Literal["OK", "RE", "TLE", "CE"]
    message: str
    user_line_count: int = 0
    steps: list[TraceStepOut] = Field(default_factory=list)
    result_preview: str | None = None
    narrations: list[TraceNarrationLine] = Field(default_factory=list)
    static_audit: StaticAuditRejection | dict[str, Any] | None = None


class AiDiagnoseRequest(BaseModel):
    code: str
    language: str = "python"
    """可选：最近一次判题结果，用于辅助生成边界测例"""
    judge_verdict: str | None = None
    failed_cases: list[CaseResultOut] = Field(default_factory=list)


class AiEdgeCaseInfo(BaseModel):
    reason: str
    category: str
    input_preview: str
    expected_preview: str
    source: str = "llm"


class AiComplexityReport(BaseModel):
    input_size_n: int
    total_steps: int
    meaningful_steps: int
    estimated_complexity: str
    report: str
    alternative_hint: str = ""
    source: str = "llm"


class SkillCardBrief(BaseModel):
    id: str
    name: str
    chapter_id: str = ""
    description: str = ""


class RecommendedResourceHint(BaseModel):
    resource_type: str
    topic: str = ""
    reason: str = ""
    chapter_id: str = ""


class OjTutoringPayload(BaseModel):
    course_id: str = "data_structures_algorithms"
    chapter_id: str = ""
    skill_id: str = ""
    module_key: str = ""
    matched_skill: SkillCardBrief | None = None
    error_pattern: str = ""
    error_pattern_label: str = ""
    bug_step_index: int = 0
    trace_summary: str = ""
    hint_level: int = Field(default=1, ge=1, le=4)
    layered_hints: list[str] = Field(default_factory=list)
    recommended_resources: list[RecommendedResourceHint] = Field(default_factory=list)
    memory_event_id: int | None = None
    mastery_update_summary: str = ""
    path_adjustment_hint: str = ""
    memory_recorded: bool = False
    mastery_updated: bool = False
    persona_updated: bool = False
    persona_patch_summary: str = ""
    persona_patch_warning: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def profile_updated(self) -> bool:
        """已弃用：等价于 persona_updated，不代表 memory_recorded。"""
        return self.persona_updated


class AiDiagnoseResponse(BaseModel):
    edge_case: AiEdgeCaseInfo
    edge_verdict: str
    edge_message: str
    trace: TraceResponse
    complexity: AiComplexityReport
    summary: str
    tutoring: OjTutoringPayload | None = None


class TraceBugDiagnoseRequest(BaseModel):
    code: str
    language: str = "python"
    steps: list[TraceStepOut] = Field(default_factory=list)
    """可选：覆盖题库描述（默认使用题目 description）"""
    problem_description: str = ""


class TraceBugDiagnoseResponse(BaseModel):
    bug_step_index: int
    diagnosis_title: str
    detailed_analysis: str
    source: str = "llm"
    error_type: str = ""
    error_type_label: str = ""
    why_failed: str = ""
    fix_suggestion: str = ""
    recommended_knowledge_points: list[str] = Field(default_factory=list)
    intervention_suggestion: str = ""
    variable_evidence: list[str] = Field(default_factory=list)
    tutoring: OjTutoringPayload | None = None


class VarChangeItem(BaseModel):
    step_index: int
    line: int
    variable_name: str
    before: str = ""
    after: str = ""


class TraceStepBrief(BaseModel):
    step_index: int
    line: int
    changed_vars: list[str] = Field(default_factory=list)
    var_summary: dict[str, str] = Field(default_factory=dict)
    is_error_step: bool = False


class TraceDiagnosisReport(BaseModel):
    error_type: str = ""
    error_category: str = ""
    error_category_label: str = ""
    failed_test_point: str = ""
    key_variable_changes: list[VarChangeItem] = Field(default_factory=list)
    error_step: TraceStepBrief | None = None
    possible_cause: str = ""
    why_failed: str = ""
    fix_suggestion: str = ""
    recommended_knowledge_points: list[str] = Field(default_factory=list)
    intervention_suggestion: str = ""
    learning_intervention_generated: bool = False
    recommended_resources: list[RecommendedResourceHint] = Field(default_factory=list)
    path_rearrange_triggered: bool = False
    trace_steps: list[TraceStepBrief] = Field(default_factory=list)
    source: str = "fallback"
    tutoring: OjTutoringPayload | None = None


class TraceReportRequest(BaseModel):
    code: str
    language: str = "python"
    judge_verdict: str = ""
    failed_cases: list[CaseResultOut] = Field(default_factory=list)
