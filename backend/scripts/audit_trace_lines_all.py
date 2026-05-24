"""全题库追踪行号审计：行号合法 + 变化步不应指向空行/注释。"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from api.oj import _pick_trace_case, _trace_to_response
from services.oj.cpp_trace_runner import gdb_available, run_trace_cpp_stdio
from services.oj.problem_store import _merge_starter_code, get_cases, get_problem
from services.oj.trace_runner import run_trace_stdio

_EMPTY_LINE = re.compile(r"^\s*(//|#|/\*|\*)?.*$")
_COMMENT_ONLY = re.compile(r"^\s*(//|#).*$")


def _is_meaningful_line(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    if _COMMENT_ONLY.match(t):
        return False
    if t in ("{", "}", "};"):
        return False
    return True


def _audit_line_steps(steps: list, source: str) -> list[str]:
    issues: list[str] = []
    lines = source.splitlines()
    n = len(lines)
    for i, s in enumerate(steps):
        if hasattr(s, "line"):
            ln = int(s.line)
            changed = list(s.changed or [])
        else:
            ln = int(s.get("line") or 0)
            changed = list(s.get("changed") or [])
        if ln < 1 or ln > n:
            issues.append(f"step[{i}] line={ln} out of range 1..{n}")
            continue
        text = lines[ln - 1]
        if changed and not _is_meaningful_line(text):
            issues.append(f"step[{i}] changed={changed} but line {ln} is blank/comment: {text[:40]!r}")
    return issues


def main() -> int:
    bundle = json.loads((_ROOT / "data" / "oj" / "tests_bundle.json").read_text(encoding="utf-8"))
    has_gdb = gdb_available()
    ok, skip, line_issues = 0, 0, []

    for slug in sorted(bundle.keys()):
        prob = get_problem(slug)
        if prob.get("judge_mode", "stdio") != "stdio":
            skip += 1
            continue
        cases = get_cases(slug, mode="run")
        if not cases:
            skip += 1
            continue
        case = _pick_trace_case(cases)
        starters = _merge_starter_code(prob)

        for lang, code in (("python", starters.get("python", "")), ("cpp", starters.get("cpp", ""))):
            if not (code or "").strip():
                continue
            if lang == "cpp" and not has_gdb:
                continue
            summary = (
                run_trace_cpp_stdio(code, case=case, time_limit_ms=10000)
                if lang == "cpp"
                else run_trace_stdio(code, case=case, time_limit_ms=8000)
            )
            if summary.verdict != "OK" or not summary.steps:
                ok += 1
                continue
            resp = _trace_to_response(summary)
            src = code.strip()
            issues = _audit_line_steps(resp.steps, src)
            if issues:
                line_issues.append(f"{slug}/{lang}: " + "; ".join(issues[:2]))
            ok += 1

    print("=== audit_trace_lines_all ===")
    print(f"runs={ok} skip={skip} line_issues={len(line_issues)} gdb={has_gdb}")
    if line_issues:
        for row in line_issues[:30]:
            print(" ", row)
        if len(line_issues) > 30:
            print(f"  …共 {len(line_issues)} 条")
    else:
        print("-- no line issues --")
    return 1 if line_issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
