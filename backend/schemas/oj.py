from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ProblemListItem(BaseModel):
    slug: str
    title: str
    lc_id: int = 0
    difficulty: str = "medium"
    ready: bool = False


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


class TraceResponse(BaseModel):
    verdict: Literal["OK", "RE", "TLE", "CE"]
    message: str
    user_line_count: int = 0
    steps: list[TraceStepOut] = Field(default_factory=list)
    result_preview: str | None = None
    narrations: list[TraceNarrationLine] = Field(default_factory=list)


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


class AiDiagnoseResponse(BaseModel):
    edge_case: AiEdgeCaseInfo
    edge_verdict: str
    edge_message: str
    trace: TraceResponse
    complexity: AiComplexityReport
    summary: str


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
