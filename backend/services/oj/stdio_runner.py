

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Literal

from services.oj.runner import CaseResult, RunSummary, _preview_value
from services.oj.stdio_io import case_input_text, case_output_text, stdout_equal
from services.oj.cpp_runner import ensure_toolchain_on_path
from utils import python_exec_args

Verdict = Literal["AC", "WA", "TLE", "RE", "CE"]


def _preview_stdio(case: dict[str, Any], field: str) -> str:
    text = case_input_text(case) if field == "in" else case_output_text(case)
    return text[:500]


def run_cases_stdio(
    user_code: str,
    *,
    cases: list[dict[str, Any]],
    language: str,
    time_limit_ms: int = 3000,
    order_insensitive: bool = False,
) -> RunSummary:
    from services.oj.static_audit import audit_user_code, run_summary_rejected

    lang = (language or "python").lower()
    audit = audit_user_code(user_code, language=lang)
    if not audit.passed:
        return run_summary_rejected(audit, total=max(1, len(cases)))
    if lang in ("cpp", "c++", "cxx"):
        return _run_cpp_stdio(user_code, cases=cases, time_limit_ms=time_limit_ms, order_insensitive=order_insensitive)
    return _run_python_stdio(user_code, cases=cases, time_limit_ms=time_limit_ms, order_insensitive=order_insensitive)


def _run_python_stdio(
    user_code: str,
    *,
    cases: list[dict[str, Any]],
    time_limit_ms: int,
    order_insensitive: bool,
) -> RunSummary:
    results: list[CaseResult] = []
    passed = 0
    timeout_s = max(1, time_limit_ms / 1000)

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(user_code)
        path = Path(f.name)

    try:
        for idx, case in enumerate(cases):
            stdin = case.get("stdin")
            if stdin is None:
                from services.oj.stdio_io import ensure_stdio_fields

                stdin = ensure_stdio_fields(case)["stdin"]
            expected = case.get("stdout")
            if expected is None:
                from services.oj.stdio_io import ensure_stdio_fields

                expected = ensure_stdio_fields(case)["stdout"]

            try:
                proc = subprocess.run(
                    python_exec_args(str(path)),
                    input=stdin,
                    capture_output=True,
                    text=True,
                    timeout=timeout_s,
                    cwd=str(path.parent),
                )
            except subprocess.TimeoutExpired:
                results.append(
                    CaseResult(
                        index=idx,
                        verdict="TLE",
                        message=f"超出时间限制 {time_limit_ms}ms",
                        input_preview=_preview_stdio(case, "in"),
                        expected_preview=_preview_stdio(case, "out"),
                        actual_preview=None,
                    )
                )
                return RunSummary(verdict="TLE", passed=passed, total=len(cases), cases=results)

            if proc.returncode != 0:
                err = (proc.stderr or proc.stdout or "运行错误").strip()
                results.append(
                    CaseResult(
                        index=idx,
                        verdict="RE",
                        message=err[:800],
                        input_preview=_preview_stdio(case, "in"),
                        expected_preview=_preview_stdio(case, "out"),
                        actual_preview=(proc.stdout or "")[:400] or None,
                    )
                )
                return RunSummary(verdict="RE", passed=passed, total=len(cases), cases=results)

            actual = proc.stdout or ""
            exp = expected or ""
            case_insensitive = order_insensitive or case.get("order_insensitive", False)
            if stdout_equal(actual, exp, order_insensitive=case_insensitive):
                passed += 1
                results.append(
                    CaseResult(
                        index=idx,
                        verdict="AC",
                        message="通过",
                        input_preview=_preview_stdio(case, "in"),
                        expected_preview=_preview_stdio(case, "out"),
                        actual_preview=actual.strip()[:400],
                        runtime_ms=0,
                    )
                )
            else:
                results.append(
                    CaseResult(
                        index=idx,
                        verdict="WA",
                        message="输出与预期不符",
                        input_preview=_preview_stdio(case, "in"),
                        expected_preview=_preview_stdio(case, "out"),
                        actual_preview=actual.strip()[:400],
                        runtime_ms=0,
                    )
                )
                return RunSummary(verdict="WA", passed=passed, total=len(cases), cases=results)
    finally:
        path.unlink(missing_ok=True)

    return RunSummary(verdict="AC", passed=passed, total=len(cases), cases=results)


def _run_cpp_stdio(
    user_code: str,
    *,
    cases: list[dict[str, Any]],
    time_limit_ms: int,
    order_insensitive: bool,
) -> RunSummary:
    ensure_toolchain_on_path()
    gpp = None
    for name in ("g++", "g++.exe", "clang++", "clang++.exe"):
        p = shutil.which(name)
        if p:
            gpp = p
            break
    if not gpp:
        return RunSummary(
            verdict="CE",
            passed=0,
            total=len(cases),
            cases=[],
            compile_error="未找到 g++ / clang++",
        )

    results: list[CaseResult] = []
    passed = 0
    timeout_s = max(1, time_limit_ms / 1000)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        cpp_file = tmp_path / "main.cpp"
        cpp_file.write_text(user_code, encoding="utf-8")
        exe = tmp_path / "main.exe" if "g++" in Path(gpp).name.lower() else tmp_path / "main"

        compile = subprocess.run(
            [gpp, "-std=c++17", "-O2", str(cpp_file), "-o", str(exe)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if compile.returncode != 0:
            err = (compile.stderr or compile.stdout or "编译失败").strip()
            return RunSummary(
                verdict="CE",
                passed=0,
                total=len(cases),
                cases=[],
                compile_error=err[:2000],
            )

        for idx, case in enumerate(cases):
            stdin = case.get("stdin")
            expected = case.get("stdout")
            if stdin is None or expected is None:
                from services.oj.stdio_io import ensure_stdio_fields

                fixed = ensure_stdio_fields(case)
                stdin = fixed["stdin"]
                expected = fixed["stdout"]

            try:
                proc = subprocess.run(
                    [str(exe)],
                    input=stdin,
                    capture_output=True,
                    text=True,
                    timeout=timeout_s,
                    cwd=str(tmp_path),
                )
            except subprocess.TimeoutExpired:
                results.append(
                    CaseResult(
                        index=idx,
                        verdict="TLE",
                        message=f"超出时间限制 {time_limit_ms}ms",
                        input_preview=_preview_stdio(case, "in"),
                        expected_preview=_preview_stdio(case, "out"),
                        actual_preview=None,
                    )
                )
                return RunSummary(verdict="TLE", passed=passed, total=len(cases), cases=results)

            if proc.returncode != 0:
                err = (proc.stderr or proc.stdout or "运行错误").strip()
                results.append(
                    CaseResult(
                        index=idx,
                        verdict="RE",
                        message=err[:800],
                        input_preview=_preview_stdio(case, "in"),
                        expected_preview=_preview_stdio(case, "out"),
                        actual_preview=(proc.stdout or "")[:400] or None,
                    )
                )
                return RunSummary(verdict="RE", passed=passed, total=len(cases), cases=results)

            actual = proc.stdout or ""
            case_insensitive = order_insensitive or case.get("order_insensitive", False)
            if stdout_equal(actual, expected or "", order_insensitive=case_insensitive):
                passed += 1
                results.append(
                    CaseResult(
                        index=idx,
                        verdict="AC",
                        message="通过",
                        input_preview=_preview_stdio(case, "in"),
                        expected_preview=_preview_stdio(case, "out"),
                        actual_preview=actual.strip()[:400],
                        runtime_ms=0,
                    )
                )
            else:
                results.append(
                    CaseResult(
                        index=idx,
                        verdict="WA",
                        message="输出与预期不符",
                        input_preview=_preview_stdio(case, "in"),
                        expected_preview=_preview_stdio(case, "out"),
                        actual_preview=actual.strip()[:400],
                        runtime_ms=0,
                    )
                )
                return RunSummary(verdict="WA", passed=passed, total=len(cases), cases=results)

    return RunSummary(verdict="AC", passed=passed, total=len(cases), cases=results)
