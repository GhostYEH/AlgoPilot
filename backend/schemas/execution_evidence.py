"""Execution Evidence Engine — 程序执行证据引擎统一数据模型。

AlgoPilot 核心创新：AI 不只返回自然语言，而是基于真实程序执行证据诊断。
本模块将 Static Analysis / OJ / Test Case / Trace / AI Diagnosis 统一抽象为
ExecutionEvidence，作为诊断页面的单一数据源。

不破坏现有 schemas/oj.py 中的细分模型，而是提供统一组装层。
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class CompileResult(BaseModel):
    verdict: Literal["AC", "WA", "TLE", "RE", "CE"]
    compile_error: str | None = None
    runtime_ms_avg: int = 0


class StaticAnalysisFinding(BaseModel):
    agent: str = "ASTAnalyzerAgent"
    passed: bool = True
    reason: str = ""
    findings: list[dict[str, Any]] = Field(default_factory=list)


class FailedTestCase(BaseModel):
    """最能暴露 Bug 的失败测试用例。"""

    index: int
    input_preview: str
    expected_output: str
    actual_output: str | None = None
    runtime_ms: int | None = None
    why_exposes_bug: str = ""
    source: str = "official"


class TraceVariableChange(BaseModel):
    name: str
    before: Any = None
    after: Any = None
    line: int = 0


class ExecutionTraceEvidence(BaseModel):
    """执行轨迹证据：控制流 + 变量变化。"""

    available: bool = False
    user_line_count: int = 0
    total_steps: int = 0
    steps: list[dict[str, Any]] = Field(default_factory=list)
    key_variable_changes: list[TraceVariableChange] = Field(default_factory=list)
    narrations: list[dict[str, Any]] = Field(default_factory=list)
    scene: str = ""


class FirstDivergence(BaseModel):
    """首次状态偏离检测——AlgoPilot 核心创新。"""

    detected: bool = False
    step_index: int = 0
    line: int | None = None
    student_state: str = ""
    reference_state: str = ""
    explanation: str = ""
    confidence: Literal["high", "medium", "low"] = "low"


class BugDiagnosis(BaseModel):
    """Bug 诊断结论——证据可解释。"""

    bug_type: str = "unknown"
    bug_type_label: str = "未分类逻辑错误"
    suspicious_lines: list[int] = Field(default_factory=list)
    first_divergence: FirstDivergence = Field(default_factory=FirstDivergence)
    root_cause: str = ""
    actual_state: str = ""
    expected_state: str = ""
    invariant: str = ""
    confidence: Literal["high", "medium", "low"] = "low"
    confidence_source: str = "rule_based"
    diagnosis_evidence: str = ""
    source: str = "fallback"


class KnowledgePointMapping(BaseModel):
    """Bug → 知识点映射。"""

    module_key: str = ""
    concept_id: str = ""
    knowledge_point: str = ""
    mastery: float = 0.0


class LayeredHint(BaseModel):
    level: int = Field(ge=1, le=4)
    title: str = ""
    content: str = ""


class ExecutionEvidence(BaseModel):
    """程序执行证据——诊断页面的统一数据源。

    组装自 OJ 判题结果 + Trace + 静态分析 + AI 诊断，
    确保诊断结论可追溯、可展示、可验证。
    """

    submission_id: int | None = None
    user_id: int | None = None
    problem_slug: str = ""
    language: str = "python"
    source_code: str = ""

    compile_result: CompileResult = Field(default_factory=CompileResult)
    static_analysis: StaticAnalysisFinding = Field(default_factory=StaticAnalysisFinding)

    total_cases: int = 0
    passed_cases: int = 0
    failed_test_cases: list[FailedTestCase] = Field(default_factory=list)

    execution_trace: ExecutionTraceEvidence = Field(default_factory=ExecutionTraceEvidence)

    bug_diagnosis: BugDiagnosis = Field(default_factory=BugDiagnosis)
    related_knowledge_points: list[KnowledgePointMapping] = Field(default_factory=list)
    layered_hints: list[LayeredHint] = Field(default_factory=list)

    ai_available: bool = True
    fallback_reason: str = ""

    @property
    def has_execution_evidence(self) -> bool:
        """是否携带结构化执行证据（非纯文本诊断）。"""
        return (
            self.execution_trace.available
            or bool(self.failed_test_cases)
            or not self.static_analysis.passed
        )

    @property
    def is_diagnosed(self) -> bool:
        return self.bug_diagnosis.bug_type != "unknown" or bool(self.bug_diagnosis.root_cause)