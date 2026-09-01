from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import get_current_user
from api.rate_limit import enforce_oj_rate_limit
from core.config import settings
from core.database import get_db
from models.db_models import OjSubmission, User
from sqlalchemy import func
from sqlalchemy.orm import Session
from schemas.oj import (
    AiComplexityReport,
    AiDiagnoseRequest,
    AiDiagnoseResponse,
    AiEdgeCaseInfo,
    AiGuidedDiagnosis,
    AiGuidedHint,
    TraceBugDiagnoseRequest,
    TraceBugDiagnoseResponse,
    CaseResultOut,
    JudgeRequest,
    JudgeResponse,
    OjSubmissionDetail,
    OjSubmissionListItem,
    TraceDiagnosisReport,
    TraceReportRequest,
    ProblemDetail,
    ProblemListItem,
    TraceNarrateRequest,
    TraceNarrationLine,
    TraceRequest,
    TraceResponse,
    TraceStepOut,
    TraceVarSnapshot,
)
from services.oj.problem_store import ProblemNotFoundError, get_cases, get_problem, get_public_problem, list_problems
from services.oj.tutoring_pipeline import apply_oj_tutoring
from services.oj.cpp_runner import run_cases_cpp, _find_gpp
from services.oj.cpp_trace_runner import _find_gdb, gdb_available, run_trace_cpp, run_trace_cpp_stdio
from services.oj.trace_step_narration import generate_step_narration
from services.oj.runner import run_cases
from services.oj.stdio_runner import run_cases_stdio
from services.oj.trace_demo_narration import generate_demo_narration
from services.oj.trace_narration import generate_trace_narration
from services.oj.ai_diagnosis import (
    analyze_complexity,
    compress_trace_steps_to_text,
    diagnose_trace_bug,
    gate_code_before_dynamic_analysis,
    generate_edge_case,
    _fallback_trace_bug_diagnosis,
)
from services.oj.trace_runner import run_trace, run_trace_stdio
from services.oj.stdio_io import case_input_text, case_output_text
from services.oj.error_patterns import ERROR_TYPE_LABELS, classify_error_type
from services.oj.first_divergence import run_first_divergence_analysis
from services.oj.counterexample_integration import try_counterexample
from services.evidence.execution_evidence_builder import build_execution_evidence
from services.evidence.persistence import (
    persist_bug_record,
    persist_execution_trace,
    persist_hint_record,
)
from services.mastery.mastery_update import update_knowledge_state

router = APIRouter(prefix="/oj", tags=["oj"])

_logger = logging.getLogger(__name__)


def _validate_oj_code(code: str) -> None:
    if len(code or "") > settings.oj_max_code_chars:
        raise HTTPException(
            status_code=413,
            detail=f"代码长度超过限制（最多 {settings.oj_max_code_chars} 个字符）",
        )


def _count_consecutive_failures(db: Session, user_id: int, slug: str) -> int:
    """统计当前用户在指定题目上最近的连续失败次数（含本次）。

    查询最近 N 条提交，从最新往前数，遇到第一个 AC 即停止。
    返回值含本次失败（即历史失败数 + 1）。
    """
    last_accepted_id = (
        db.query(func.max(OjSubmission.id))
        .filter(
            OjSubmission.user_id == user_id,
            OjSubmission.problem_slug == slug,
            OjSubmission.verdict == "AC",
        )
        .scalar()
    )
    query = db.query(func.count(OjSubmission.id)).filter(
        OjSubmission.user_id == user_id,
        OjSubmission.problem_slug == slug,
        OjSubmission.verdict != "AC",
    )
    if last_accepted_id is not None:
        query = query.filter(OjSubmission.id > last_accepted_id)
    return int(query.scalar() or 0) + 1


def _first_failure_message(cases) -> str:
    """取第一个失败用例的 message；全 AC 或无 cases 时返回空串。"""
    if not cases:
        return ""
    for c in cases:
        if getattr(c, "verdict", "") != "AC":
            return getattr(c, "message", "") or ""
    return ""


@router.get("/capabilities")
def api_capabilities():
    gpp = _find_gpp()
    gdb = _find_gdb()
    return {
        "languages": ["python", "cpp"],
        "cpp_compiler": gpp,
        "gdb_path": gdb,
        "gdb_available": gdb is not None,
        "trace_python": True,
        "trace_cpp": gdb is not None and gpp is not None,
    }


@router.get("/problems", response_model=list[ProblemListItem])
def api_list_problems(q: str | None = Query(None, description="按标题或 slug 搜索")):
    items = []
    for p in list_problems(q=q):
        slug = p["slug"]
        course_id = p.get("course_id", "data_structures_algorithms")
        chapter_id = p.get("chapter_id", "")
        module_key = p.get("module_key", "")
        skill_id = p.get("skill_id", "")
        tags = p.get("tags", [])
        common_errors = p.get("common_errors", [])
        try:
            detail = get_public_problem(slug)
            ready = detail["ready"]
            course_id = detail.get("course_id", course_id)
            chapter_id = detail.get("chapter_id", chapter_id)
            module_key = detail.get("module_key", module_key)
            skill_id = detail.get("skill_id", skill_id)
            tags = detail.get("tags", tags)
            common_errors = detail.get("common_errors", common_errors)
        except ProblemNotFoundError:
            ready = False
        items.append(
            ProblemListItem(
                slug=slug,
                title=p.get("title") or slug,
                lc_id=p.get("lc_id", 0),
                difficulty=p.get("difficulty", "medium"),
                ready=ready,
                course_id=course_id,
                chapter_id=chapter_id,
                module_key=module_key,
                skill_id=skill_id,
                tags=tags,
                common_errors=common_errors,
            )
        )
    return items


@router.get("/problems/{slug}", response_model=ProblemDetail)
def api_get_problem(slug: str):
    try:
        return ProblemDetail(**get_public_problem(slug))
    except ProblemNotFoundError:
        raise HTTPException(404, "题目不存在") from None


@router.post("/problems/{slug}/run", response_model=JudgeResponse)
def api_run_samples(slug: str, body: JudgeRequest, user: User = Depends(get_current_user)):
    enforce_oj_rate_limit(user, "run")
    return _judge(slug, body, mode="run")


@router.post("/problems/{slug}/submit", response_model=JudgeResponse)
def api_submit(
    slug: str,
    body: JudgeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_oj_rate_limit(user, "submit")
    resp = _judge(slug, body, mode="submit")
    event_logs: list[dict[str, str]] = []
    event_id: str | None = None
    problem = get_public_problem(slug)
    message = _first_failure_message(resp.cases)
    consecutive_failures = _count_consecutive_failures(db, user.id, slug) if resp.verdict != "AC" else 0
    runtime_ms_values = [c.runtime_ms for c in resp.cases if c.runtime_ms is not None]
    runtime_ms_avg = round(sum(runtime_ms_values) / len(runtime_ms_values)) if runtime_ms_values else 0

    # 先保存真实提交，再触发会产生其它写入的事件处理。这样事件处理或关联失败时，
    # 判题记录仍然存在，不会出现“学情已更新但提交记录丢失”的状态。
    try:
        submission = OjSubmission(
            user_id=user.id,
            problem_slug=slug,
            language=body.language or "python",
            code=body.code or "",
            verdict=resp.verdict,
            passed=resp.passed,
            total=resp.total,
            compile_error=resp.compile_error or "",
            cases=[c.model_dump() for c in resp.cases],
            runtime_ms_avg=runtime_ms_avg,
            event_id=None,
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
    except Exception:
        db.rollback()
        _logger.exception(
            "OJ 提交记录落库失败 user=%s slug=%s verdict=%s",
            user.id,
            slug,
            resp.verdict,
        )
        raise HTTPException(500, "提交结果保存失败，请重试") from None

    payload = {
        "problem_slug": slug,
        "verdict": resp.verdict,
        "message": message,
        "error_pattern": message[:200] if message else resp.verdict,
        "module_key": str(problem.get("module_key") or ""),
        "chapter_id": str(problem.get("chapter_id") or ""),
        "skill_id": str(problem.get("skill_id") or ""),
        "consecutive_failures": consecutive_failures,
    }
    try:
        from services.events.event_bus import event_bus

        pub = event_bus.publish(
            db,
            event_type=("on_oj_submission_accepted" if resp.verdict == "AC" else "on_oj_submission_failed"),
            user_id=user.id,
            chapter_id=payload["chapter_id"],
            skill_id=payload["skill_id"],
            payload=payload,
        )
        event_logs = [log.model_dump() for log in pub.event.agent_logs]
        if pub.persisted:
            try:
                submission.event_id = pub.event.event_id
                db.commit()
                event_id = pub.event.event_id
            except Exception:
                db.rollback()
                _logger.exception(
                    "OJ 提交与事件关联失败 submission_id=%s event_id=%s",
                    submission.id,
                    pub.event.event_id,
                )
        if not pub.ok:
            _logger.warning(
                "OJ 提交事件处理不完整 user=%s slug=%s status=%s errors=%s",
                user.id,
                slug,
                pub.event.status,
                pub.event.handler_errors,
            )
    except Exception:
        db.rollback()
        _logger.exception("OJ 提交事件发布异常 user=%s slug=%s", user.id, slug)

    # === AC/WA 提交直接更新知识状态（不依赖 AI 诊断）===
    try:
        module_key = str(problem.get("module_key") or "")
        concept_id = str(problem.get("skill_id") or "")
        if module_key or concept_id:
            is_first_ac = resp.verdict == "AC" and not (
                db.query(OjSubmission)
                .filter(
                    OjSubmission.user_id == user.id,
                    OjSubmission.problem_slug == slug,
                    OjSubmission.verdict == "AC",
                    OjSubmission.id < submission.id,
                )
                .first()
            )
            update_knowledge_state(
                db,
                user_id=user.id,
                module_key=module_key,
                concept_id=concept_id,
                knowledge_point=str(problem.get("title") or slug),
                verdict=resp.verdict,
                difficulty=str(problem.get("difficulty") or "medium"),
                is_first_ac=is_first_ac,
                is_independent=True,
                submission_id=submission.id,
                evidence_type="SUBMISSION_RESULT",
            )
    except Exception:
        _logger.exception("api_submit 知识状态更新失败 user=%s slug=%s", user.id, slug)

    return JudgeResponse(
        verdict=resp.verdict,
        passed=resp.passed,
        total=resp.total,
        cases=resp.cases,
        compile_error=resp.compile_error,
        event_id=event_id,
        event_logs=event_logs,
    )


@router.get(
    "/problems/{slug}/submissions",
    response_model=list[OjSubmissionListItem],
)
def api_list_problem_submissions(
    slug: str,
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """当前用户在某道题下的真实提交记录（最新在前）。"""
    rows = (
        db.query(OjSubmission)
        .filter(
            OjSubmission.user_id == user.id,
            OjSubmission.problem_slug == slug,
        )
        .order_by(OjSubmission.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        OjSubmissionListItem(
            id=r.id,
            problem_slug=r.problem_slug,
            language=r.language,
            verdict=r.verdict,
            passed=r.passed,
            total=r.total,
            runtime_ms_avg=r.runtime_ms_avg,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.get("/submissions/{submission_id}", response_model=OjSubmissionDetail)
def api_get_submission(
    submission_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询单条提交详情（仅限本人）。"""
    row = db.get(OjSubmission, submission_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(404, "提交记录不存在")
    return OjSubmissionDetail(
        id=row.id,
        problem_slug=row.problem_slug,
        language=row.language,
        verdict=row.verdict,
        passed=row.passed,
        total=row.total,
        runtime_ms_avg=row.runtime_ms_avg,
        created_at=row.created_at,
        code=row.code,
        compile_error=row.compile_error or "",
        cases=[CaseResultOut(**c) for c in row.cases],
        event_id=row.event_id,
    )


def _pick_trace_case(cases: list[dict]) -> dict:
    """可视化调试优先选用输入更长的样例，便于展示栈/队列等状态变化。"""

    def _case_input_len(c: dict) -> int:
        stdin = c.get("stdin")
        if isinstance(stdin, str) and stdin.strip():
            return len(stdin.strip())
        args = c.get("args")
        if isinstance(args, list) and args:
            return len(" ".join(str(a) for a in args))
        return 0

    return max(cases, key=_case_input_len)


def _resolve_trace_case(cases: list[dict], case_index: int | None) -> dict:
    """按指定下标选取测例；越界或未指定时回退到首个样例或自动优选。"""
    if not cases:
        raise HTTPException(400, "无样例可追踪")
    if case_index is not None and 0 <= case_index < len(cases):
        return cases[case_index]
    if case_index is not None:
        return cases[0]
    return _pick_trace_case(cases)


def _trace_to_response(
    summary,
    *,
    slug: str = "",
    user_code: str = "",
    attach_demo_narration: bool = True,
    code_style_warning: str | None = None,
) -> TraceResponse:
    static_rejection = getattr(summary, "static_rejection", None)
    steps_out = [
        TraceStepOut(
            line=s.line,
            changed=s.changed,
            vars={
                k: TraceVarSnapshot(
                    type=v.get("type", "other"),
                    value=v.get("value"),
                    view_hint=v.get("view_hint"),
                )
                for k, v in s.vars.items()
            },
        )
        for s in summary.steps
    ]
    narrations: list[TraceNarrationLine] = []
    step_lines: list[dict[str, int | str]] = []
    if summary.verdict == "OK" and steps_out:
        steps_raw = [{"line": s.line, "changed": s.changed, "vars": s.vars} for s in summary.steps]
        step_lines = generate_step_narration(steps_raw)
        if step_lines:
            narrations = [TraceNarrationLine(step_index=n["step_index"], text=n["text"]) for n in step_lines]
        elif attach_demo_narration:
            demo = generate_demo_narration(slug, user_code, steps_raw)
            if demo:
                narrations = [TraceNarrationLine(step_index=n["step_index"], text=n["text"]) for n in demo]
    msg = summary.message
    if narrations and step_lines:
        msg = f"{summary.message}（旁白来自本次执行的变量变化）"
    elif narrations:
        msg = f"{summary.message}（已附带演示旁白）"
    return TraceResponse(
        verdict=summary.verdict,
        message=msg,
        user_line_count=summary.user_line_count,
        result_preview=summary.result_preview,
        steps=steps_out,
        narrations=narrations,
        static_audit=static_rejection,
        code_style_warning=code_style_warning,
    )


_LEETCODE_CLASS_PATTERN = re.compile(r"^\s*class\s+Solution\b", re.MULTILINE)
_LEETCODE_CPP_PATTERN = re.compile(
    r"\bclass\s+Solution\b|\bpublic\s*:\s*\n\s*(?:vector|optional|string|int|bool|void|ListNode\*|TreeNode\*|auto)",
    re.MULTILINE,
)


def _detect_code_style_mismatch(code: str, judge_mode: str, lang: str) -> str | None:
    """检测用户代码风格与判题模式是否匹配，不匹配时返回友好提示。

    - stdio 题目收到 LeetCode 风格（class Solution）代码时，运行几乎无输出且 trace 几乎为空，
      用户难以诊断原因。此处返回提示，引导用户改用题目提供的 starter_code。
    - function 题目收到纯 stdio 风格（无 class Solution）代码时，同样提示。
    """
    if not code or not code.strip():
        return None
    is_leetcode_style: bool
    if lang == "cpp":
        is_leetcode_style = bool(_LEETCODE_CPP_PATTERN.search(code))
    else:
        is_leetcode_style = bool(_LEETCODE_CLASS_PATTERN.search(code))

    if judge_mode == "stdio" and is_leetcode_style:
        return (
            "检测到代码采用 LeetCode 风格（class Solution），但本题判题模式为 stdio（标准输入输出）。"
            "这会导致程序没有读取输入、没有输出，trace 也只能记录到类定义本身。"
            "请使用题目右侧「代码模板」提供的 starter_code，从标准输入读取数据后再处理。"
        )
    if judge_mode != "stdio" and not is_leetcode_style:
        return (
            "检测到代码采用 stdio 风格，但本题判题模式为方法调用（LeetCode 风格）。"
            "请使用题目右侧「代码模板」提供的 starter_code，实现指定类与方法。"
        )
    return None


@router.post("/problems/{slug}/trace", response_model=TraceResponse)
def api_trace_execution(
    slug: str,
    body: TraceRequest,
    user: User = Depends(get_current_user),
):
    """可视化调试：Python sys.settrace / C++ GDB MI（可指定样例下标）。"""
    enforce_oj_rate_limit(user, "trace")
    _validate_oj_code(body.code)
    lang = _normalize_lang(body.language)

    ast_gate = gate_code_before_dynamic_analysis(body.code, language=lang)
    if not ast_gate.passed:
        from services.oj.static_audit import trace_summary_rejected

        return _trace_to_response(trace_summary_rejected(ast_gate), user_code=body.code)

    try:
        problem = get_public_problem(slug)
        cases = get_cases(slug, mode="run")
    except ProblemNotFoundError:
        raise HTTPException(404, "题目不存在") from None

    if not cases:
        raise HTTPException(400, "无样例可追踪")

    tl = min(problem.get("time_limit_ms", 3000), 5000)
    judge_mode = problem.get("judge_mode", "stdio")

    code_style_warning = _detect_code_style_mismatch(body.code, judge_mode, lang)

    if judge_mode == "stdio":
        if lang == "cpp":
            if not gdb_available() or _find_gpp() is None:
                raise HTTPException(
                    400,
                    "C++ 可视化调试需要本机 g++ 与 gdb（MinGW）。请安装后重启后端。",
                )
            trace_case = _resolve_trace_case(cases, body.case_index)
            summary = run_trace_cpp_stdio(body.code, case=trace_case, time_limit_ms=tl)
        elif lang == "python":
            trace_case = _resolve_trace_case(cases, body.case_index)
            summary = run_trace_stdio(body.code, case=trace_case, time_limit_ms=tl)
        else:
            raise HTTPException(400, f"可视化调试暂不支持: {lang}")
    else:
        entry = problem.get("entry")
        if not entry:
            raise HTTPException(400, "本题未配置方法入口")
        entry_run = {**entry, "_slug": slug}
        if lang == "cpp":
            if not gdb_available():
                raise HTTPException(
                    400,
                    "C++ 可视化调试需要本机 gdb（MinGW 自带）。请安装后重启后端。",
                )
            trace_case = _resolve_trace_case(cases, body.case_index)
            summary = run_trace_cpp(body.code, entry=entry_run, case=trace_case, time_limit_ms=tl)
        elif lang == "python":
            trace_case = _resolve_trace_case(cases, body.case_index)
            summary = run_trace(body.code, entry=entry_run, case=trace_case, time_limit_ms=tl)
        else:
            raise HTTPException(400, f"可视化调试暂不支持: {lang}")

    return _trace_to_response(
        summary,
        slug=slug,
        user_code=body.code,
        code_style_warning=code_style_warning,
    )


def _run_trace_for_case(
    *,
    slug: str,
    user_code: str,
    lang: str,
    problem: dict,
    case: dict,
    time_limit_ms: int,
):
    ast_gate = gate_code_before_dynamic_analysis(user_code, language=lang)
    if not ast_gate.passed:
        from services.oj.static_audit import trace_summary_rejected

        return trace_summary_rejected(ast_gate)

    judge_mode = problem.get("judge_mode", "stdio")
    if judge_mode == "stdio":
        if lang == "cpp":
            from services.oj.cpp_trace_runner import run_trace_cpp_stdio

            return run_trace_cpp_stdio(user_code, case=case, time_limit_ms=time_limit_ms)
        return run_trace_stdio(user_code, case=case, time_limit_ms=time_limit_ms)
    entry = problem.get("entry")
    if not entry:
        raise HTTPException(400, "本题未配置方法入口")
    entry_run = {**entry, "_slug": slug}
    if lang == "cpp":
        from services.oj.cpp_trace_runner import run_trace_cpp

        return run_trace_cpp(user_code, entry=entry_run, case=case, time_limit_ms=time_limit_ms)
    return run_trace(user_code, entry=entry_run, case=case, time_limit_ms=time_limit_ms)


def _judge_single_case(
    *,
    user_code: str,
    lang: str,
    problem: dict,
    slug: str,
    case: dict,
    time_limit_ms: int,
):
    ast_gate = gate_code_before_dynamic_analysis(user_code, language=lang)
    if not ast_gate.passed:
        return "CE", ast_gate.reason

    judge_mode = problem.get("judge_mode", "stdio")
    if judge_mode == "stdio":
        summary = run_cases_stdio(
            user_code,
            cases=[case],
            language=lang,
            time_limit_ms=time_limit_ms,
            order_insensitive=problem.get("order_insensitive", False),
        )
    else:
        entry = problem.get("entry")
        if not entry:
            raise HTTPException(400, "本题未配置方法入口")
        entry_run = {**entry, "_slug": slug}
        kwargs = dict(
            entry=entry_run,
            cases=[case],
            time_limit_ms=time_limit_ms,
            order_insensitive=problem.get("order_insensitive", False),
        )
        if lang == "cpp":
            from services.oj.cpp_runner import run_cases_cpp

            summary = run_cases_cpp(user_code, **kwargs)
        else:
            summary = run_cases(user_code, **kwargs)
    if not summary.cases:
        return "RE", "无判题结果"
    c = summary.cases[0]
    return c.verdict, c.message


@router.post("/problems/{slug}/diagnose", response_model=TraceBugDiagnoseResponse)
async def api_trace_bug_diagnose(
    slug: str,
    body: TraceBugDiagnoseRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    AI 轨迹诊断：基于已有 trace steps 压缩投喂 LLM，定位 bug 起源步。
    适用于 WA / TLE 等场景下用户已生成可视化轨迹。
    """
    enforce_oj_rate_limit(user, "trace_diagnose")
    _validate_oj_code(body.code)
    try:
        problem = get_public_problem(slug)
    except ProblemNotFoundError:
        raise HTTPException(404, "题目不存在") from None

    if not body.steps:
        raise HTTPException(400, "steps 为空，请先运行可视化调试")

    description = (body.problem_description or "").strip() or (problem.get("description") or "")
    steps_raw = [
        {
            "line": s.line,
            "changed": s.changed,
            "vars": {k: v.model_dump() for k, v in s.vars.items()},
        }
        for s in body.steps
    ]
    result = await diagnose_trace_bug(
        description,
        body.code,
        steps_raw,
        slug=slug,
        judge_verdict=body.judge_verdict or "WA",
    )
    tutoring = apply_oj_tutoring(
        db,
        user,
        slug=slug,
        problem=problem,
        bug_step_index=int(result.get("bug_step_index") or 0),
        diagnosis_title=str(result.get("diagnosis_title") or ""),
        detailed_analysis=str(result.get("detailed_analysis") or ""),
        judge_verdict=body.judge_verdict or "WA",
        code=body.code,
    )
    try:
        from services.events.event_bus import event_bus

        event_bus.publish(
            db,
            event_type="on_trace_diagnosed",
            user_id=user.id,
            payload={
                "problem_slug": slug,
                "diagnosis": result,
                "source": "trace_bug",
                "memory_written": True,
                "memory_event_id": tutoring.memory_event_id,
            },
        )
    except Exception:
        _logger.exception("trace_bug_diagnose 事件发布失败 user=%s slug=%s", user.id, slug)
    return TraceBugDiagnoseResponse(**result, tutoring=tutoring)


@router.post("/problems/{slug}/ai/diagnose", response_model=AiDiagnoseResponse)
async def api_ai_diagnose(
    slug: str,
    body: AiDiagnoseRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    AI 深度诊断：生成边界测例 → 判题验证 → 可视化追踪 → 破案式旁白 → 复杂度报告。
    """
    enforce_oj_rate_limit(user, "ai_diagnose")
    _validate_oj_code(body.code)
    lang = _normalize_lang(body.language)

    ast_gate = gate_code_before_dynamic_analysis(body.code, language=lang)
    if not ast_gate.passed:
        from services.oj.static_audit import trace_summary_rejected

        trace_resp = _trace_to_response(
            trace_summary_rejected(ast_gate),
            slug=slug,
            user_code=body.code,
            attach_demo_narration=False,
        )
        return AiDiagnoseResponse(
            edge_case=AiEdgeCaseInfo(
                reason="静态分析熔断，未生成边界测例",
                category="static_rejected",
                input_preview="",
                expected_preview="",
                source="ASTAnalyzerAgent",
            ),
            edge_verdict="CE",
            edge_message=ast_gate.reason[:300],
            trace=trace_resp,
            complexity=AiComplexityReport(
                input_size_n=0,
                total_steps=0,
                meaningful_steps=0,
                estimated_complexity="N/A",
                report="代码未通过静态 AST 审计，已拦截动态沙箱执行。",
                alternative_hint="请修复死循环/指针未更新等问题后重试。",
                source="ASTAnalyzerAgent",
            ),
            summary=ast_gate.reason,
        )

    try:
        problem = get_public_problem(slug)
        problem_full = get_problem(slug)
        cases = get_cases(slug, mode="run")
    except ProblemNotFoundError:
        raise HTTPException(404, "题目不存在") from None

    if not cases:
        raise HTTPException(400, "无样例可诊断")

    sample = cases[0]
    tl = min(problem.get("time_limit_ms", 3000), 5000)
    judge_mode = problem.get("judge_mode", "stdio")

    failed_raw = [
        {
            "index": c.index,
            "input_preview": c.input_preview,
            "message": c.message,
        }
        for c in body.failed_cases
        if c.verdict != "AC"
    ]

    failed_case_index = next(
        (c.index for c in body.failed_cases if c.verdict != "AC" and 0 <= c.index < len(cases)),
        None,
    )
    if failed_case_index is not None:
        edge = {
            "case": cases[failed_case_index],
            "reason": "复用最近一次判题中已确认失败的测例，避免用未复现输入推测根因。",
            "category": "verified_failure",
            "source": "judge",
        }
    else:
        edge = await generate_edge_case(
            problem_title=problem.get("title") or slug,
            description=problem.get("description") or "",
            judge_mode=judge_mode,
            sample=sample,
            user_code=body.code,
            failed_cases=failed_raw or None,
        )
    edge_case = edge["case"]

    edge_verdict, edge_message = _judge_single_case(
        user_code=body.code,
        lang=lang,
        problem=problem_full,
        slug=slug,
        case=edge_case,
        time_limit_ms=tl,
    )

    # AI 生成的边界测例若没有复现错误，回查公开样例并追踪首个真实失败输入。
    # 诊断宁可明确“证据不足”，也不能在 AC 轨迹上强行制造根因。
    if edge_verdict == "AC":
        for candidate in cases:
            candidate_verdict, candidate_message = _judge_single_case(
                user_code=body.code,
                lang=lang,
                problem=problem_full,
                slug=slug,
                case=candidate,
                time_limit_ms=tl,
            )
            if candidate_verdict != "AC":
                edge_case = candidate
                edge_verdict = candidate_verdict
                edge_message = candidate_message
                edge = {
                    "case": candidate,
                    "reason": "AI 边界测例未复现错误，已自动切换到判题确认失败的公开样例。",
                    "category": "verified_sample",
                    "source": "judge",
                }
                break

    # === Counterexample Generator 集成 ===
    counterexample_dict: dict[str, Any] | None = None
    if edge_verdict != "AC":
        try:
            original_failed = {
                "input": case_input_text(edge_case)[:500],
                "expected": case_output_text(edge_case)[:500],
                "category": str(edge.get("category") or "original"),
            }

            def _ce_run_output(code: str, args_list: list[Any]) -> Any:
                ce_case = {
                    "args": args_list,
                    "stdin": None,
                    "stdout": None,
                    "expected": None,
                }
                trace = _run_trace_for_case(
                    slug=slug,
                    user_code=code,
                    lang=lang,
                    problem=problem_full,
                    case=ce_case,
                    time_limit_ms=tl,
                )
                if trace.verdict != "OK" or trace.result_preview is None:
                    raise RuntimeError(f"candidate execution failed: {trace.verdict}")
                preview = trace.result_preview
                if len(preview) >= 300:
                    raise RuntimeError("candidate output exceeds reliable preview limit")
                if problem_full.get("judge_mode", "stdio") == "stdio":
                    return preview
                try:
                    return json.loads(preview)
                except json.JSONDecodeError as exc:
                    raise RuntimeError("candidate output is not valid JSON") from exc

            def _ce_user_runner(args_list: list[Any]) -> Any:
                return _ce_run_output(body.code, args_list)

            def _ce_reference_runner(args_list: list[Any]) -> Any:
                ref_code = None
                if user is not None:
                    from services.oj.first_divergence import find_reference_solution

                    ref_code = find_reference_solution(
                        db,
                        slug,
                        language=lang,
                        student_code=body.code,
                    )
                if ref_code is None:
                    return None
                return _ce_run_output(ref_code, args_list)

            ce_result = try_counterexample(
                slug=slug,
                module_key=str(problem.get("module_key") or ""),
                original_failed_case=original_failed,
                user_runner=_ce_user_runner,
                reference_runner=_ce_reference_runner,
            )
            counterexample_dict = ce_result.to_dict()

            if ce_result.source == "generated_verified" and ce_result.selected_case:
                edge_case = ce_result.selected_case
                edge_verdict, edge_message = _judge_single_case(
                    user_code=body.code,
                    lang=lang,
                    problem=problem_full,
                    slug=slug,
                    case=edge_case,
                    time_limit_ms=tl,
                )
                edge = {
                    "case": edge_case,
                    "reason": ce_result.reason,
                    "category": ce_result.category or "generated_verified",
                    "source": "counterexample_generator",
                }
        except Exception:
            _logger.exception("Counterexample 集成异常 slug=%s", slug)
            counterexample_dict = {
                "source": "original_failed_case",
                "reason": "反例集成异常，保留原始失败样例",
            }

    summary = _run_trace_for_case(
        slug=slug,
        user_code=body.code,
        lang=lang,
        problem=problem_full,
        case=edge_case,
        time_limit_ms=tl,
    )
    trace_resp = _trace_to_response(
        summary,
        slug=slug,
        user_code=body.code,
        attach_demo_narration=False,
    )

    steps_raw = [
        {"line": s.line, "changed": s.changed, "vars": {k: v.model_dump() for k, v in s.vars.items()}}
        for s in trace_resp.steps
    ]
    step_lines = generate_step_narration(steps_raw) if steps_raw else []

    diagnosis_failures = [
        {
            "index": 0,
            "input_preview": case_input_text(edge_case)[:200],
            "expected_preview": case_output_text(edge_case)[:200],
            "actual_preview": (trace_resp.result_preview or "")[:200],
            "message": edge_message,
        }
    ]
    diagnosis_failures.extend(failed_raw[:2])

    diagnosis_raw, complexity_raw = await asyncio.gather(
        diagnose_trace_bug(
            problem.get("description") or "",
            body.code,
            steps_raw,
            slug=slug,
            judge_verdict=edge_verdict,
            failed_cases=diagnosis_failures,
        ),
        analyze_complexity(
            steps=steps_raw,
            case=edge_case,
            user_code=body.code,
            problem_title=problem.get("title") or slug,
        ),
    )

    bug_step_index = max(0, min(int(diagnosis_raw.get("bug_step_index") or 0), max(0, len(steps_raw) - 1)))
    bug_line = steps_raw[bug_step_index].get("line") if steps_raw else None
    diagnosis_title = str(diagnosis_raw.get("diagnosis_title") or "诊断证据不足")
    detailed_analysis = str(diagnosis_raw.get("detailed_analysis") or "")
    confidence = str(diagnosis_raw.get("confidence") or "low")
    if edge_verdict == "AC":
        confidence = "low"

    raw_hints = diagnosis_raw.get("hints") or []
    hints = [
        AiGuidedHint(
            level=max(1, min(3, int(h.get("level") or i + 1))),
            title=str(h.get("title") or f"提示 {i + 1}"),
            content=str(h.get("content") or ""),
        )
        for i, h in enumerate(raw_hints[:3])
        if isinstance(h, dict) and str(h.get("content") or "").strip()
    ]
    if not hints:
        hints = [
            AiGuidedHint(level=1, title="先观察", content=f"从 Step {bug_step_index + 1} 开始对照关键变量。"),
            AiGuidedHint(level=2, title="再推理", content=str(diagnosis_raw.get("invariant") or detailed_analysis)[:260]),
            AiGuidedHint(level=3, title="修改方向", content=str(diagnosis_raw.get("fix_suggestion") or "只调整首次破坏不变量的语句。")[:260]),
        ]

    guided_diagnosis = AiGuidedDiagnosis(
        bug_step_index=bug_step_index,
        bug_line=bug_line,
        title=diagnosis_title,
        root_cause=detailed_analysis,
        actual_state=str(diagnosis_raw.get("actual_state") or ""),
        expected_state=str(diagnosis_raw.get("expected_state") or ""),
        invariant=str(diagnosis_raw.get("invariant") or ""),
        observation_question=str(
            diagnosis_raw.get("observation_question")
            or f"观察 Step {bug_step_index + 1}：哪个变量第一次偏离了手算结果？"
        ),
        hints=hints,
        fix_direction=str(diagnosis_raw.get("fix_suggestion") or ""),
        verification=str(diagnosis_raw.get("verification") or "用同一失败输入重新运行并对照关键步骤。"),
        confidence=confidence if confidence in ("high", "medium", "low") else "low",
        source=str(diagnosis_raw.get("source") or "fallback"),
    )

    narration_by_step = {
        int(n["step_index"]): TraceNarrationLine(
            step_index=int(n["step_index"]),
            text=str(n["text"]),
            critical=False,
        )
        for n in step_lines
    }
    narration_by_step[bug_step_index] = TraceNarrationLine(
        step_index=bug_step_index,
        text=detailed_analysis[:240] or diagnosis_title,
        critical=True,
    )
    trace_resp.narrations = [narration_by_step[i] for i in sorted(narration_by_step)]

    inp_preview = case_input_text(edge_case)[:200] if judge_mode == "stdio" else str(edge_case.get("args", ""))[:200]
    exp_preview = (
        case_output_text(edge_case)[:200] if judge_mode == "stdio" else str(edge_case.get("expected", ""))[:200]
    )

    if edge_verdict == "AC":
        summary_text = (
            f"边界测例未复现错误（判题 {edge_verdict}）。"
            f"已用该测例生成 {len(trace_resp.steps)} 步可视化与复杂度分析，请结合旁白检查逻辑。"
        )
    else:
        summary_text = (
            f"AI 已生成边界测例（{edge.get('category', 'edge')}），判题 {edge_verdict}。"
            f"下方可视化回放展示程序在该测例上的执行过程。"
        )

    tutoring = apply_oj_tutoring(
        db,
        user,
        slug=slug,
        problem=problem,
        bug_step_index=bug_step_index,
        diagnosis_title=diagnosis_title,
        detailed_analysis=detailed_analysis,
        edge_category=str(edge.get("category") or ""),
        edge_verdict=edge_verdict,
        judge_verdict=body.judge_verdict or edge_verdict,
        code=body.code,
    )


    # M6 修复：未登录用户诊断结果不入库，记录日志便于审计
    if user is None:
        _logger.info(
            "未登录用户调用 ai_diagnose slug=%s，诊断结果未入库",
            slug,
        )
    else:
        try:
            from services.events.event_bus import event_bus

            diag_payload = {
                "bug_step_index": bug_step_index,
                "diagnosis_title": diagnosis_title,
                "detailed_analysis": detailed_analysis,
                "source": "ai_diagnose",
            }
            event_bus.publish(
                db,
                event_type="on_trace_diagnosed",
                user_id=user.id,
                payload={
                    "problem_slug": slug,
                    "diagnosis": diag_payload,
                    "edge_category": str(edge.get("category") or ""),
                    "memory_written": True,
                    "memory_event_id": tutoring.memory_event_id,
                },
            )
        except Exception:
            _logger.exception("ai_diagnose 事件发布失败 user=%s slug=%s", user.id, slug)

    # === Execution Evidence Engine 集成 ===
    execution_evidence_dict: dict[str, Any] | None = None
    first_divergence_dict: dict[str, Any] | None = None
    bug_record_id: int | None = None
    trace_record_id: int | None = None

    try:
        bug_type = classify_error_type(
            slug=slug,
            analysis=detailed_analysis,
            trace_summary=summary.message if hasattr(summary, "message") else "",
            verdict=edge_verdict,
            code=body.code,
        )
        bug_type_label = ERROR_TYPE_LABELS.get(bug_type, "未分类逻辑错误")

        execution_evidence = build_execution_evidence(
            problem_slug=slug,
            language=lang,
            source_code=body.code,
            judge_result={
                "verdict": edge_verdict,
                "passed": 1 if edge_verdict == "AC" else 0,
                "total": 1,
                "cases": [
                    {
                        "index": 0,
                        "verdict": edge_verdict,
                        "input_preview": inp_preview,
                        "expected_preview": exp_preview,
                        "actual_preview": trace_resp.result_preview or "",
                    }
                ],
                "compile_error": None,
            },
            trace_result={
                "verdict": trace_resp.verdict,
                "user_line_count": trace_resp.user_line_count,
                "steps": steps_raw,
                "narrations": [n.model_dump() for n in trace_resp.narrations],
            },
            ai_diagnosis={
                "bug_step_index": bug_step_index,
                "bug_line": bug_line,
                "root_cause": detailed_analysis,
                "actual_state": guided_diagnosis.actual_state,
                "expected_state": guided_diagnosis.expected_state,
                "invariant": guided_diagnosis.invariant,
                "confidence": guided_diagnosis.confidence,
                "source": guided_diagnosis.source,
                "hints": [h.model_dump() for h in hints],
            },
            ai_available=settings.llm_configured,
            fallback_reason="" if settings.llm_configured else "LLM 不可用，使用规则诊断兜底",
        )
        execution_evidence_dict = execution_evidence.model_dump()

        if user is not None:
            submission_id = None
            latest_sub = (
                db.query(OjSubmission)
                .filter(
                    OjSubmission.user_id == user.id,
                    OjSubmission.problem_slug == slug,
                )
                .order_by(OjSubmission.created_at.desc())
                .first()
            )
            if latest_sub is not None:
                submission_id = latest_sub.id

            trace_rec = persist_execution_trace(
                db,
                submission_id=submission_id or 0,
                steps=steps_raw,
                language=lang,
                first_divergence_step=bug_step_index,
                first_divergence_line=bug_line,
            )
            if trace_rec is not None:
                trace_record_id = trace_rec.id

            bug_rec = persist_bug_record(
                db,
                user_id=user.id,
                problem_slug=slug,
                bug_type=bug_type,
                bug_type_label=bug_type_label,
                suspicious_lines=[bug_line] if bug_line else [],
                first_divergence_step=bug_step_index,
                first_divergence_line=bug_line,
                root_cause=detailed_analysis,
                confidence=guided_diagnosis.confidence,
                confidence_source="ai_with_evidence" if guided_diagnosis.source != "fallback" else "rule_based",
                related_module_key=str(problem.get("module_key") or ""),
                related_concept_id=str(problem.get("skill_id") or ""),
                diagnosis_source=guided_diagnosis.source,
                submission_id=submission_id,
            )
            if bug_rec is not None:
                bug_record_id = bug_rec.id

            hint_level_used = max((h.level for h in hints), default=0)
            persist_hint_record(
                db,
                user_id=user.id,
                problem_slug=slug,
                hint_level_used=hint_level_used,
                hint_count=len(hints),
                eventually_accepted=edge_verdict == "AC",
                bug_type=bug_type,
                module_key=str(problem.get("module_key") or ""),
                submission_id=submission_id,
            )

            module_key = str(problem.get("module_key") or "")
            concept_id = str(problem.get("skill_id") or "")
            if module_key or concept_id and submission_id is not None:
                update_knowledge_state(
                    db,
                    user_id=user.id,
                    module_key=module_key,
                    concept_id=concept_id,
                    knowledge_point=diagnosis_title,
                    verdict=body.judge_verdict or edge_verdict,
                    bug_type=bug_type,
                    hint_level_used=hint_level_used,
                    difficulty=str(problem.get("difficulty") or "medium"),
                    is_first_ac=False,
                    is_independent=hint_level_used <= 1,
                    submission_id=submission_id,
                    evidence_type="DIAGNOSIS_BUG",
                )

            def _run_ref_trace(ref_code: str, _slug: str, _lang: str) -> list[dict[str, Any]]:
                ref_summary = _run_trace_for_case(
                    slug=_slug,
                    user_code=ref_code,
                    lang=_lang,
                    problem=problem_full,
                    case=edge_case,
                    time_limit_ms=tl,
                )
                return [
                    {
                        "line": getattr(s, "line", 0),
                        "vars": {k: v.model_dump() if hasattr(v, "model_dump") else v for k, v in getattr(s, "vars", {}).items()},
                        "changed": getattr(s, "changed", []),
                    }
                    for s in getattr(ref_summary, "steps", [])
                ]

            fd_result = run_first_divergence_analysis(
                db,
                slug=slug,
                student_code=body.code,
                student_steps=steps_raw,
                language=lang,
                run_reference_trace_fn=_run_ref_trace,
            )
            first_divergence_dict = fd_result.to_dict()
    except Exception:
        _logger.exception("Execution Evidence Engine 集成失败 slug=%s", slug)

    response = AiDiagnoseResponse(
        edge_case=AiEdgeCaseInfo(
            reason=str(edge.get("reason") or ""),
            category=str(edge.get("category") or "edge"),
            input_preview=inp_preview,
            expected_preview=exp_preview,
            source=str(edge.get("source") or "llm"),
        ),
        edge_verdict=edge_verdict,
        edge_message=edge_message[:300],
        trace=trace_resp,
        complexity=AiComplexityReport(**complexity_raw),
        summary=summary_text,
        diagnosis=guided_diagnosis,
        tutoring=tutoring,
        execution_evidence=execution_evidence_dict,
        first_divergence=first_divergence_dict,
        counterexample=counterexample_dict,
        bug_record_id=bug_record_id,
        trace_record_id=trace_record_id,
    )
    return response


@router.post("/problems/{slug}/trace/narrate", response_model=TraceResponse)
async def api_trace_narrate(
    slug: str,
    body: TraceNarrateRequest,
    user: User = Depends(get_current_user),
):
    """为已有 trace steps 生成旁白（优先演示预置，否则单次 LLM）。"""
    enforce_oj_rate_limit(user, "trace_narrate")
    _validate_oj_code(body.code)
    try:
        problem = get_public_problem(slug)
    except ProblemNotFoundError:
        raise HTTPException(404, "题目不存在") from None

    steps_raw = [
        {
            "line": s.line,
            "changed": s.changed,
            "vars": {k: v.model_dump() if hasattr(v, "model_dump") else v for k, v in s.vars.items()},
        }
        for s in body.steps
    ]
    demo_first = generate_demo_narration(slug, body.code, steps_raw)
    if demo_first:
        narrations = demo_first
        src = "演示旁白"
    else:
        narrations = await generate_trace_narration(
            slug=slug,
            user_code=body.code,
            steps=steps_raw,
            problem_title=body.problem_title or problem.get("title") or slug,
            prefer_demo=False,
        )
        src = "AI 旁白"
    return TraceResponse(
        verdict="OK",
        message=f"{src}已生成",
        user_line_count=0,
        steps=body.steps,
        narrations=[TraceNarrationLine(step_index=n["step_index"], text=n["text"]) for n in narrations],
    )


def _normalize_lang(lang: str) -> str:
    k = (lang or "python").strip().lower()
    if k in ("cpp", "c++", "cxx"):
        return "cpp"
    if k in ("py", "python3", "python"):
        return "python"
    raise HTTPException(400, f"不支持的语言: {lang}")


def _judge(slug: str, body: JudgeRequest, *, mode: str) -> JudgeResponse:
    _validate_oj_code(body.code)
    lang = _normalize_lang(body.language)

    try:
        problem = get_public_problem(slug)
        cases = get_cases(slug, mode=mode)
    except ProblemNotFoundError:
        raise HTTPException(404, "题目不存在") from None

    judge_mode = problem.get("judge_mode", "stdio")
    if not cases:
        raise HTTPException(400, "本题测例尚未配置，暂无法运行")

    if judge_mode == "stdio":
        summary = run_cases_stdio(
            body.code,
            cases=cases,
            language=lang,
            time_limit_ms=problem.get("time_limit_ms", 3000),
            order_insensitive=problem.get("order_insensitive", False),
        )
    else:
        entry = problem.get("entry")
        if not entry:
            raise HTTPException(400, "本题测例尚未配置，暂无法运行")
        entry_run = {**entry, "_slug": slug}
        kwargs = dict(
            entry=entry_run,
            cases=cases,
            time_limit_ms=problem.get("time_limit_ms", 3000),
            order_insensitive=problem.get("order_insensitive", False),
        )
        if lang == "cpp":
            summary = run_cases_cpp(body.code, **kwargs)
        else:
            summary = run_cases(body.code, **kwargs, language=lang)

    return JudgeResponse(
        verdict=summary.verdict,
        passed=summary.passed,
        total=summary.total,
        compile_error=summary.compile_error,
        cases=[
            CaseResultOut(
                index=c.index,
                verdict=c.verdict,
                message=c.message,
                input_preview=c.input_preview,
                expected_preview=c.expected_preview,
                actual_preview=c.actual_preview,
                runtime_ms=c.runtime_ms,
            )
            for c in summary.cases
        ],
    )


@router.post("/problems/{slug}/trace-report", response_model=TraceDiagnosisReport)
async def api_trace_report(
    slug: str,
    body: TraceReportRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from services.oj.trace_report import (
        generate_trace_diagnosis_report,
        _build_demo_trace_steps,
    )

    enforce_oj_rate_limit(user, "trace_report")
    _validate_oj_code(body.code)
    lang = _normalize_lang(body.language)

    try:
        problem = get_public_problem(slug)
        problem_full = get_problem(slug)
    except ProblemNotFoundError:
        raise HTTPException(404, "题目不存在") from None

    cases = get_cases(slug, mode="submit")
    judge_verdict = body.judge_verdict or "WA"
    failed_raw = [
        {"index": c.index, "message": c.message, "input_preview": c.input_preview}
        for c in body.failed_cases
        if c.verdict != "AC"
    ]

    trace_steps: list[dict[str, Any]] = []
    bug_step_index = 0
    diagnosis_title = ""
    detailed_analysis = ""
    fix_suggestion = ""
    source = "fallback"
    trace_case_reproduced = False
    trace_case_verdict = ""
    trace_case_message = ""

    ast_gate = gate_code_before_dynamic_analysis(body.code, language=lang)
    if ast_gate.passed and cases:
        tl = min(problem.get("time_limit_ms", 3000), 5000)
        failed_index = next(
            (c.index for c in body.failed_cases if c.verdict != "AC" and 0 <= c.index < len(cases)),
            None,
        )
        trace_case = _resolve_trace_case(cases, failed_index)
        try:
            trace_case_verdict, trace_case_message = _judge_single_case(
                user_code=body.code,
                lang=lang,
                problem=problem_full,
                slug=slug,
                case=trace_case,
                time_limit_ms=tl,
            )
            trace_case_reproduced = trace_case_verdict != "AC"
            if trace_case_reproduced:
                judge_verdict = trace_case_verdict
            summary = _run_trace_for_case(
                slug=slug,
                user_code=body.code,
                lang=lang,
                problem=problem_full,
                case=trace_case,
                time_limit_ms=tl,
            )
            if summary.verdict == "OK" and summary.steps:
                trace_steps = [
                    {
                        "line": s.line,
                        "vars": {k: v.__dict__ if hasattr(v, "__dict__") else v for k, v in s.vars.items()},
                        "changed": s.changed,
                    }
                    for s in summary.steps
                ]
        except Exception:
            _logger.debug(
                "trace_report 动态 Trace 生成失败，回退到 demo 步骤 slug=%s language=%s",
                slug,
                lang,
                exc_info=True,
            )

    if not trace_steps:
        trace_steps = _build_demo_trace_steps(body.code)
        source = "demo"

    compressed_lines, _ = compress_trace_steps_to_text(trace_steps)

    if settings.llm_configured and trace_steps and compressed_lines:
        diag = await diagnose_trace_bug(
            (problem.get("description") or "")[:2000],
            body.code,
            trace_steps,
            slug=slug,
            judge_verdict=judge_verdict,
            failed_cases=failed_raw,
        )
        bug_step_index = int(diag.get("bug_step_index") or 0)
        diagnosis_title = str(diag.get("diagnosis_title") or "")
        detailed_analysis = str(diag.get("detailed_analysis") or "")
        source = diag.get("source", "llm")

        # diagnose_trace_bug 已完成一次模型分析。报告直接复用该结果，避免为
        # “原因/修复建议”串行发起第二次高度重复的模型请求。
        fix_suggestion = str(diag.get("fix_suggestion") or "")
    else:
        fallback = _fallback_trace_bug_diagnosis(
            trace_steps,
            compressed_lines,
            user_code=body.code,
            judge_verdict=judge_verdict,
        )
        bug_step_index = int(fallback.get("bug_step_index") or 0)
        diagnosis_title = str(fallback.get("diagnosis_title") or "")
        detailed_analysis = str(fallback.get("detailed_analysis") or "")
        source = fallback.get("source", "fallback")

    tutoring = apply_oj_tutoring(
        db,
        user,
        slug=slug,
        problem=problem,
        bug_step_index=bug_step_index,
        diagnosis_title=diagnosis_title,
        detailed_analysis=detailed_analysis,
        judge_verdict=judge_verdict,
        code=body.code,
    )

    report = generate_trace_diagnosis_report(
        user_code=body.code,
        judge_verdict=judge_verdict,
        failed_cases=failed_raw,
        trace_steps=trace_steps,
        bug_step_index=bug_step_index,
        diagnosis_title=diagnosis_title,
        detailed_analysis=detailed_analysis,
        problem=problem,
        slug=slug,
        tutoring=tutoring,
        source=source,
        fix_suggestion=fix_suggestion,
        trace_case_reproduced=trace_case_reproduced,
        trace_case_verdict=trace_case_verdict,
        trace_case_message=trace_case_message,
    )

    try:
        from services.events.event_bus import event_bus

        event_bus.publish(
            db,
            event_type="on_trace_diagnosed",
            user_id=user.id,
            payload={
                "problem_slug": slug,
                "diagnosis": {
                    "bug_step_index": bug_step_index,
                    "diagnosis_title": diagnosis_title,
                    "source": source,
                },
                "source": "trace_report",
            },
        )
    except Exception:
        _logger.exception("trace_report 事件发布失败 user=%s slug=%s", user.id, slug)

    return report
