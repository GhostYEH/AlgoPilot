"""OJ 静态审计门闸：动态 trace/runner 执行前的统一入口。"""

from __future__ import annotations

from services.agents.ast_analyzer import ASTAnalyzerAgent, AstAuditResult
from services.oj.runner import CaseResult, RunSummary
from services.oj.trace_runner import TraceSummary
from utils.security import CppSecurityViolation, check_cpp_security


def audit_user_code(user_code: str, *, language: str = "python") -> AstAuditResult:
    lang = (language or "python").lower().replace("c++", "cpp")
    if lang in {"cpp", "cxx"}:
        try:
            check_cpp_security(user_code)
        except CppSecurityViolation as exc:
            return AstAuditResult(
                passed=False,
                status="rejected",
                reason=str(exc),
                language="cpp",
                source="rule",
            )
    return ASTAnalyzerAgent.audit(user_code, language=language)


def run_summary_rejected(result: AstAuditResult, *, total: int = 1) -> RunSummary:
    return RunSummary(
        verdict="CE",
        passed=0,
        total=total,
        cases=[
            CaseResult(
                index=0,
                verdict="CE",
                message=result.reason,
                input_preview="(静态分析)",
                expected_preview="",
                actual_preview=None,
            )
        ],
        compile_error=result.reason,
    )


def trace_summary_rejected(result: AstAuditResult) -> TraceSummary:
    return TraceSummary(
        verdict="CE",
        message=result.reason,
        user_line_count=0,
        steps=[],
        result_preview=None,
        static_rejection=result.to_rejection_payload(),
    )
