from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import get_current_user
from models.db_models import User
from schemas.oj import (
    AiComplexityReport,
    AiDiagnoseRequest,
    AiDiagnoseResponse,
    AiEdgeCaseInfo,
    TraceBugDiagnoseRequest,
    TraceBugDiagnoseResponse,
    CaseResultOut,
    JudgeRequest,
    JudgeResponse,
    TraceRequest,
    ProblemDetail,
    ProblemListItem,
    TraceNarrateRequest,
    TraceNarrationLine,
    TraceResponse,
    TraceStepOut,
    TraceVarSnapshot,
)
from services.oj.problem_store import ProblemNotFoundError, get_cases, get_problem, get_public_problem, list_problems
from services.oj.cpp_runner import run_cases_cpp, _find_gpp
from services.oj.cpp_trace_runner import _find_gdb, gdb_available, run_trace_cpp, run_trace_cpp_stdio
from services.oj.trace_step_narration import generate_step_narration
from services.oj.runner import run_cases
from services.oj.stdio_runner import run_cases_stdio
from services.oj.trace_demo_narration import generate_demo_narration
from services.oj.trace_narration import generate_trace_narration
from services.oj.ai_diagnosis import (
    analyze_complexity,
    diagnose_trace_bug,
    gate_code_before_dynamic_analysis,
    generate_edge_case,
    generate_trace_diagnosis,
    merge_diagnosis_narrations,
)
from services.oj.trace_runner import run_trace, run_trace_stdio
from services.oj.stdio_io import case_input_text, case_output_text

router = APIRouter(prefix="/oj", tags=["oj"])


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
        try:
            detail = get_public_problem(slug)
            ready = detail["ready"]
        except ProblemNotFoundError:
            ready = False
        items.append(
            ProblemListItem(
                slug=slug,
                title=p.get("title") or slug,
                lc_id=p.get("lc_id", 0),
                difficulty=p.get("difficulty", "medium"),
                ready=ready,
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
def api_run_samples(slug: str, body: JudgeRequest):
    return _judge(slug, body, mode="run")


@router.post("/problems/{slug}/submit", response_model=JudgeResponse)
def api_submit(
    slug: str,
    body: JudgeRequest,
    user: User = Depends(get_current_user),
):
    _ = user
    return _judge(slug, body, mode="submit")


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
        steps_raw = [
            {"line": s.line, "changed": s.changed, "vars": s.vars}
            for s in summary.steps
        ]
        step_lines = generate_step_narration(steps_raw)
        if step_lines:
            narrations = [
                TraceNarrationLine(step_index=n["step_index"], text=n["text"]) for n in step_lines
            ]
        elif attach_demo_narration:
            demo = generate_demo_narration(slug, user_code, steps_raw)
            if demo:
                narrations = [
                    TraceNarrationLine(step_index=n["step_index"], text=n["text"]) for n in demo
                ]
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
    )


@router.post("/problems/{slug}/trace", response_model=TraceResponse)
def api_trace_execution(slug: str, body: TraceRequest):
    """可视化调试：Python sys.settrace / C++ GDB MI（可指定样例下标）。"""
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

    return _trace_to_response(summary, slug=slug, user_code=body.code)


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
async def api_trace_bug_diagnose(slug: str, body: TraceBugDiagnoseRequest):
    """
    AI 轨迹诊断：基于已有 trace steps 压缩投喂 LLM，定位 bug 起源步。
    适用于 WA / TLE 等场景下用户已生成可视化轨迹。
    """
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
    result = await diagnose_trace_bug(description, body.code, steps_raw)
    return TraceBugDiagnoseResponse(**result)


@router.post("/problems/{slug}/ai/diagnose", response_model=AiDiagnoseResponse)
async def api_ai_diagnose(slug: str, body: AiDiagnoseRequest):
    """
    AI 深度诊断：生成边界测例 → 判题验证 → 可视化追踪 → 破案式旁白 → 复杂度报告。
    """
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
            "input_preview": c.input_preview,
            "message": c.message,
        }
        for c in body.failed_cases
        if c.verdict != "AC"
    ]

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

    diagnosis, complexity_raw = await asyncio.gather(
        generate_trace_diagnosis(
            user_code=body.code,
            steps=steps_raw,
            problem_title=problem.get("title") or slug,
            edge_reason=str(edge.get("reason") or ""),
        ),
        analyze_complexity(
            steps=steps_raw,
            case=edge_case,
            user_code=body.code,
            problem_title=problem.get("title") or slug,
        ),
    )

    merged = merge_diagnosis_narrations(step_lines, diagnosis)
    trace_resp.narrations = [
        TraceNarrationLine(step_index=n["step_index"], text=n["text"], critical=n.get("critical", False))
        for n in merged
    ]

    inp_preview = case_input_text(edge_case)[:200] if judge_mode == "stdio" else str(edge_case.get("args", ""))[:200]
    exp_preview = case_output_text(edge_case)[:200] if judge_mode == "stdio" else str(edge_case.get("expected", ""))[:200]

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

    return AiDiagnoseResponse(
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
    )


@router.post("/problems/{slug}/trace/narrate", response_model=TraceResponse)
async def api_trace_narrate(slug: str, body: TraceNarrateRequest):
    """为已有 trace steps 生成旁白（优先演示预置，否则单次 LLM）。"""
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
