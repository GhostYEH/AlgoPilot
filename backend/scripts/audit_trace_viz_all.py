"""全题库可视化调试审计：追踪可运行性 + 前端解析是否丢数据（view_hint / 类型）。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from api.oj import _pick_trace_case, _trace_to_response  # noqa: E402
from services.oj.cpp_trace_runner import gdb_available, run_trace_cpp_stdio  # noqa: E402
from services.oj.problem_store import _merge_starter_code, get_cases, get_problem  # noqa: E402
from services.oj.trace_runner import run_trace_stdio  # noqa: E402

STACK_NAMES = {"st", "stack", "stk", "paren_stack", "char_stack", "brackets"}
QUEUE_NAMES = {"q", "dq", "deque", "queue", "monotonic_queue", "mq", "candq"}
MAP_NAMES = {"num_map", "map", "seen", "hash", "freq", "m", "table", "dict", "count"}


def _is_stack_name(n: str) -> bool:
    low = n.lower()
    return low in STACK_NAMES or low.endswith("_stack") or low.endswith("stack")


def _is_queue_name(n: str) -> bool:
    low = n.lower()
    return low in QUEUE_NAMES or low.endswith("_queue") or low.endswith("deque")


def _is_map_name(n: str) -> bool:
    return n in MAP_NAMES or n.endswith("_map")


def _sequence_items(snap: dict) -> list:
    v = snap.get("value")
    return list(v) if isinstance(v, list) else []


def _view_hint(snap: dict) -> str:
    hint = snap.get("view_hint")
    if hint:
        return str(hint)
    t = snap.get("type") or ""
    if t == "stack":
        return "stack"
    if t == "queue":
        return "queue"
    return "vector"


def _parse_stack_items(snap: dict, name: str) -> list[str]:
    t = snap.get("type")
    if t in ("sequence", "stack", "list", "queue"):
        hint = _view_hint(snap)
        if hint == "stack" or _is_stack_name(name):
            return [str(x) for x in _sequence_items(snap)]
    if t == "stack":
        return [str(x) for x in _sequence_items(snap)]
    return []


def _parse_queue_indices(snap: dict, name: str) -> list[int]:
    t = snap.get("type")
    if t in ("sequence", "stack", "list", "queue"):
        hint = _view_hint(snap)
        if hint in ("queue", "deque", "priority_queue") or _is_queue_name(name):
            out: list[int] = []
            for x in _sequence_items(snap):
                try:
                    out.append(int(x))
                except (TypeError, ValueError):
                    pass
            return out
    if t == "queue":
        return [int(x) for x in _sequence_items(snap) if str(x).lstrip("-").isdigit()]
    return []


def _parse_map_entries(snap: dict) -> list[tuple[str, str]]:
    t = snap.get("type")
    v = snap.get("value")
    if t in ("dict", "associative", "map"):
        if isinstance(v, list):
            rows = []
            for e in v:
                if isinstance(e, dict):
                    rows.append((str(e.get("key", "")), str(e.get("value", ""))))
            return rows
        if isinstance(v, dict) and isinstance(v.get("entries"), list):
            return [
                (str(e.get("key", "")), str(e.get("value", "")))
                for e in v["entries"]
                if isinstance(e, dict)
            ]
    return []


def _list_like(snap: dict | None) -> list[str]:
    if not snap:
        return []
    t = snap.get("type")
    if t in ("list", "sequence"):
        hint = _view_hint(snap)
        if hint in ("stack", "queue", "priority_queue"):
            return []
        return [str(x) for x in _sequence_items(snap)]
    return []


def _audit_steps(steps: list, *, lang: str) -> list[str]:
    """模拟前端解析，返回本题的 viz 问题列表。"""
    issues: list[str] = []
    api_steps = steps
    if steps and hasattr(steps[0], "vars"):
        api_steps = [
            {
                "line": s.line,
                "changed": s.changed,
                "vars": {
                    k: {"type": v.type, "value": v.value, "view_hint": v.view_hint}
                    for k, v in s.vars.items()
                },
            }
            for s in steps
        ]

    lost_hints = 0
    parse_gaps: list[str] = []

    for i, step in enumerate(api_steps):
        vars_map = step.get("vars") or {}
        for name, snap in vars_map.items():
            if not isinstance(snap, dict):
                continue
            raw = snap
            t = raw.get("type")
            val = raw.get("value")
            # 原始 runner 有 view_hint 但 API 模型丢失（历史 bug）
            if t == "sequence" and raw.get("view_hint") is None and lang == "cpp":
                lost_hints += 1

            if _is_stack_name(name) and isinstance(val, list) and len(val) > 0:
                parsed = _parse_stack_items(raw, name)
                if not parsed and _view_hint(raw) != "stack":
                    parse_gaps.append(
                        f"step[{i}] {name}: value={val!r} but parse_stack_items=[] "
                        f"(hint={raw.get('view_hint')!r})"
                    )

            if _is_queue_name(name) and isinstance(val, list) and len(val) > 0:
                parsed = _parse_queue_indices(raw, name)
                hint = _view_hint(raw)
                if not parsed and hint not in ("queue", "deque", "priority_queue"):
                    parse_gaps.append(
                        f"step[{i}] {name}: value={val!r} but parse_queue=[] "
                        f"(hint={raw.get('view_hint')!r})"
                    )

            if (_is_map_name(name) or t in ("dict", "associative")) and val:
                entries = _parse_map_entries(raw)
                if isinstance(val, (list, dict)) and not entries and t in ("dict", "associative"):
                    parse_gaps.append(f"step[{i}] {name}: map value present but parse_map_entries empty")

        nums_names = ("nums", "nums1", "arr", "array", "numbers")
        for nn in nums_names:
            snap = vars_map.get(nn)
            if snap and isinstance(snap.get("value"), list) and len(snap["value"]) > 0:
                if not _list_like(snap) and snap.get("type") == "sequence":
                    parse_gaps.append(
                        f"step[{i}] {nn}: sequence nums not readable by listLike (legacy list-only)"
                    )

    if lost_hints:
        issues.append(f"API 丢失 view_hint 的 sequence 快照 ×{lost_hints}")
    issues.extend(parse_gaps[:3])
    if len(parse_gaps) > 3:
        issues.append(f"…另有 {len(parse_gaps) - 3} 处解析缺口")
    return issues


def main() -> int:
    bundle_path = _ROOT / "data" / "oj" / "tests_bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    has_gdb = gdb_available()
    ok, skip, fail = 0, 0, 0
    viz_issues: list[str] = []
    fails: list[str] = []

    for slug in sorted(bundle.keys()):
        try:
            prob = get_problem(slug)
            mode = prob.get("judge_mode", "stdio")
            if mode != "stdio":
                skip += 1
                continue
            cases = get_cases(slug, mode="run")
            if not cases:
                skip += 1
                continue
            case = _pick_trace_case(cases)
            starters = _merge_starter_code(prob)
            py_code = (starters.get("python") or "").strip()
            cpp_code = (starters.get("cpp") or "").strip()

            for lang, code in (("python", py_code), ("cpp", cpp_code)):
                if not code:
                    continue
                if lang == "cpp" and not has_gdb:
                    continue
                if lang == "python":
                    summary = run_trace_stdio(code, case=case, time_limit_ms=8000)
                else:
                    summary = run_trace_cpp_stdio(code, case=case, time_limit_ms=12000)
                if summary.verdict not in ("OK", "RE", "TLE", "CE"):
                    fail += 1
                    fails.append(f"{slug}/{lang}: {summary.verdict} {summary.message[:60]}")
                    continue
                if summary.verdict != "OK" or not summary.steps:
                    ok += 1
                    continue
                resp = _trace_to_response(summary)
                issues = _audit_steps(resp.steps, lang=lang)
                if issues:
                    viz_issues.append(f"{slug}/{lang}: " + "; ".join(issues))
                ok += 1
        except Exception as e:
            fail += 1
            fails.append(f"{slug}: EXC {e}")

    print(f"=== audit_trace_viz_all ===")
    print(f"trace_runs_ok={ok} skip={skip} fail={fail} gdb={has_gdb}")
    if fails:
        print("\n-- failures --")
        for line in fails[:25]:
            print(" ", line)
    if viz_issues:
        print(f"\n-- viz_parse_issues ({len(viz_issues)}) --")
        for line in viz_issues[:40]:
            print(" ", line)
        if len(viz_issues) > 40:
            print(f"  …共 {len(viz_issues)} 题")
    else:
        print("\n-- no viz_parse_issues detected --")

    return 1 if fail or viz_issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
