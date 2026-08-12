"""ExecutionEvidence 组装器：从 OJ 判题 + Trace + 静态分析 + AI 诊断统一构建。

AlgoPilot 核心创新的数据层闭环：
  静态分析 → OJ 真实判题 → 失败用例 → Trace → 首次偏离 → Bug 分类 → 知识点映射
  → 统一 ExecutionEvidence → 诊断页面单一数据源
"""

from __future__ import annotations

from typing import Any

from schemas.execution_evidence import (
    BugDiagnosis,
    CompileResult,
    ExecutionEvidence,
    ExecutionTraceEvidence,
    FailedTestCase,
    FirstDivergence,
    KnowledgePointMapping,
    LayeredHint,
    StaticAnalysisFinding,
    TraceVariableChange,
)
from services.oj.error_patterns import ERROR_TYPE_LABELS, classify_error_type


def build_execution_evidence(
    *,
    problem_slug: str = "",
    language: str = "python",
    source_code: str = "",
    submission_id: int | None = None,
    user_id: int | None = None,
    judge_result: dict[str, Any] | None = None,
    trace_result: dict[str, Any] | None = None,
    static_audit: dict[str, Any] | None = None,
    ai_diagnosis: dict[str, Any] | None = None,
    edge_cases: list[dict[str, Any]] | None = None,
    knowledge_mappings: list[dict[str, Any]] | None = None,
    ai_available: bool = True,
    fallback_reason: str = "",
) -> ExecutionEvidence:
    """从各子系统结果组装统一 ExecutionEvidence。"""

    compile_result = _build_compile_result(judge_result)
    static_analysis = _build_static_analysis(static_audit, judge_result)
    failed_cases = _build_failed_cases(judge_result, edge_cases)
    trace_evidence = _build_trace_evidence(trace_result)
    bug_diagnosis = _build_bug_diagnosis(
        ai_diagnosis, judge_result, trace_result, source_code, problem_slug
    )
    hints = _build_layered_hints(ai_diagnosis)
    kp_mappings = _build_knowledge_mappings(knowledge_mappings)

    return ExecutionEvidence(
        submission_id=submission_id,
        user_id=user_id,
        problem_slug=problem_slug,
        language=language,
        source_code=source_code,
        compile_result=compile_result,
        static_analysis=static_analysis,
        total_cases=compile_result.verdict if False else (judge_result or {}).get("total", 0),
        passed_cases=(judge_result or {}).get("passed", 0),
        failed_test_cases=failed_cases,
        execution_trace=trace_evidence,
        bug_diagnosis=bug_diagnosis,
        related_knowledge_points=kp_mappings,
        layered_hints=hints,
        ai_available=ai_available,
        fallback_reason=fallback_reason,
    )


def _build_compile_result(judge_result: dict[str, Any] | None) -> CompileResult:
    if not judge_result:
        return CompileResult(verdict="CE")
    return CompileResult(
        verdict=judge_result.get("verdict", "CE"),
        compile_error=judge_result.get("compile_error"),
        runtime_ms_avg=judge_result.get("runtime_ms_avg", 0),
    )


def _build_static_analysis(
    static_audit: dict[str, Any] | None,
    judge_result: dict[str, Any] | None,
) -> StaticAnalysisFinding:
    if static_audit:
        return StaticAnalysisFinding(
            agent=static_audit.get("agent", "ASTAnalyzerAgent"),
            passed=static_audit.get("passed", True),
            reason=static_audit.get("reason", ""),
            findings=static_audit.get("findings", []),
        )
    if judge_result and judge_result.get("verdict") == "CE" and judge_result.get("compile_error"):
        return StaticAnalysisFinding(
            passed=False,
            reason=judge_result.get("compile_error", ""),
        )
    return StaticAnalysisFinding()


def _build_failed_cases(
    judge_result: dict[str, Any] | None,
    edge_cases: list[dict[str, Any]] | None,
) -> list[FailedTestCase]:
    cases: list[FailedTestCase] = []
    if judge_result:
        for c in judge_result.get("cases", []):
            if c.get("verdict") in ("WA", "RE", "TLE"):
                cases.append(
                    FailedTestCase(
                        index=c.get("index", 0),
                        input_preview=c.get("input_preview", ""),
                        expected_output=c.get("expected_preview", ""),
                        actual_output=c.get("actual_preview"),
                        runtime_ms=c.get("runtime_ms"),
                        source="official",
                    )
                )
    if edge_cases:
        for i, ec in enumerate(edge_cases):
            cases.append(
                FailedTestCase(
                    index=len(cases) + i,
                    input_preview=ec.get("input_preview", ""),
                    expected_output=ec.get("expected_preview", ""),
                    actual_output=ec.get("actual_preview"),
                    why_exposes_bug=ec.get("reason", ""),
                    source=ec.get("source", "llm"),
                )
            )
    return cases[:5]


def _build_trace_evidence(trace_result: dict[str, Any] | None) -> ExecutionTraceEvidence:
    if not trace_result:
        return ExecutionTraceEvidence()
    steps = trace_result.get("steps", [])
    return ExecutionTraceEvidence(
        available=bool(steps),
        user_line_count=trace_result.get("user_line_count", 0),
        total_steps=len(steps),
        steps=steps,
        narrations=trace_result.get("narrations", []),
        scene=trace_result.get("scene", ""),
    )


def _build_bug_diagnosis(
    ai_diagnosis: dict[str, Any] | None,
    judge_result: dict[str, Any] | None,
    trace_result: dict[str, Any] | None,
    source_code: str,
    problem_slug: str,
) -> BugDiagnosis:
    first_divergence = FirstDivergence()
    root_cause = ""
    actual_state = ""
    expected_state = ""
    invariant = ""
    confidence: str = "low"
    confidence_source = "rule_based"
    source = "fallback"
    suspicious_lines: list[int] = []

    if ai_diagnosis:
        bug_step = ai_diagnosis.get("bug_step_index", 0)
        bug_line = ai_diagnosis.get("bug_line")
        if bug_line:
            suspicious_lines = [bug_line]
        first_divergence = FirstDivergence(
            detected=bug_step > 0 or bug_line is not None,
            step_index=bug_step,
            line=bug_line,
            student_state=ai_diagnosis.get("actual_state", ""),
            reference_state=ai_diagnosis.get("expected_state", ""),
            explanation=ai_diagnosis.get("root_cause", ""),
            confidence=ai_diagnosis.get("confidence", "low"),
        )
        root_cause = ai_diagnosis.get("root_cause", "")
        actual_state = ai_diagnosis.get("actual_state", "")
        expected_state = ai_diagnosis.get("expected_state", "")
        invariant = ai_diagnosis.get("invariant", "")
        confidence = ai_diagnosis.get("confidence", "low")
        confidence_source = "ai_with_evidence"
        source = ai_diagnosis.get("source", "fallback")

    verdict = (judge_result or {}).get("verdict", "")
    trace_summary = ""
    if trace_result:
        trace_summary = trace_result.get("message", "")

    bug_type = classify_error_type(
        slug=problem_slug,
        analysis=root_cause or trace_summary,
        trace_summary=trace_summary,
        verdict=verdict,
        code=source_code,
    )

    return BugDiagnosis(
        bug_type=bug_type,
        bug_type_label=ERROR_TYPE_LABELS.get(bug_type, "未分类逻辑错误"),
        suspicious_lines=suspicious_lines,
        first_divergence=first_divergence,
        root_cause=root_cause,
        actual_state=actual_state,
        expected_state=expected_state,
        invariant=invariant,
        confidence=confidence,
        confidence_source=confidence_source,
        diagnosis_evidence=_build_evidence_text(
            bug_type, suspicious_lines, first_divergence, root_cause
        ),
        source=source,
    )


def _build_evidence_text(
    bug_type: str,
    suspicious_lines: list[int],
    first_divergence: FirstDivergence,
    root_cause: str,
) -> str:
    parts: list[str] = []
    label = ERROR_TYPE_LABELS.get(bug_type, bug_type)
    parts.append(f"错误类型：{label}")
    if suspicious_lines:
        parts.append(f"疑似位置：Line {', '.join(str(l) for l in suspicious_lines)}")
    if first_divergence.detected:
        loc = f"Step {first_divergence.step_index}"
        if first_divergence.line:
            loc += f" (Line {first_divergence.line})"
        parts.append(f"首次状态偏离：{loc}")
        if first_divergence.student_state:
            parts.append(f"学生状态：{first_divergence.student_state}")
        if first_divergence.reference_state:
            parts.append(f"参考状态：{first_divergence.reference_state}")
    if root_cause:
        parts.append(f"诊断：{root_cause}")
    return "\n".join(parts)


def _build_layered_hints(ai_diagnosis: dict[str, Any] | None) -> list[LayeredHint]:
    if not ai_diagnosis:
        return []
    hints_raw = ai_diagnosis.get("hints", [])
    return [
        LayeredHint(
            level=h.get("level", 1),
            title=h.get("title", ""),
            content=h.get("content", ""),
        )
        for h in hints_raw
    ]


def _build_knowledge_mappings(
    mappings: list[dict[str, Any]] | None,
) -> list[KnowledgePointMapping]:
    if not mappings:
        return []
    return [
        KnowledgePointMapping(
            module_key=m.get("module_key", ""),
            concept_id=m.get("concept_id", ""),
            knowledge_point=m.get("knowledge_point", ""),
            mastery=float(m.get("mastery", 0.0)),
        )
        for m in mappings
    ]