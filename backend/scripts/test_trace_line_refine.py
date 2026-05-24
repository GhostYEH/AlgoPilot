"""trace_line_refine 多题型单测。"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from services.oj.trace_line_refine import (
    _eval_simple_condition,
    refine_trace_step_lines,
    resolve_branch_display_line,
)
from services.oj.trace_runner import TraceStepOut


def test_branch_else_if_cpp() -> None:
    src = """for (char c : s) {
    if (c == '(') st.push(')');
    else if (c == ')') {
        st.pop();
    }
}"""
    lines = src.splitlines()
    got = resolve_branch_display_line(2, lines, {"c": {"type": "str", "value": ")"}})
    assert got == 3, got


def test_two_sum_in_seen() -> None:
    src = """for i, x in enumerate(nums):
    need = target - x
    if need in seen:
        print(seen[need], i)
    seen[x] = i
"""
    lines = src.splitlines()
    vars_map = {
        "need": {"type": "int", "value": 2},
        "seen": {
            "type": "dict",
            "value": {"entries": [{"key": 2, "value": 0}]},
        },
    }
    assert _eval_simple_condition("need in seen", vars_map) is True
    got = resolve_branch_display_line(3, lines, vars_map)
    assert got == 3, got


def test_binary_search_compare() -> None:
    vars_map = {"left": {"type": "int", "value": 0}, "right": {"type": "int", "value": 4}}
    assert _eval_simple_condition("left <= right", vars_map) is True
    vars_map2 = {
        "nums": {"type": "list", "value": [1, 3, 5, 7, 9]},
        "mid": {"type": "int", "value": 2},
        "target": {"type": "int", "value": 5},
    }
    assert _eval_simple_condition("nums[mid] == target", vars_map2) is True


def test_sliding_window_while() -> None:
    src = """while left <= right:
    if sum >= target:
        left += 1
"""
    lines = src.splitlines()
    vars_map = {"sum": {"type": "int", "value": 10}, "target": {"type": "int", "value": 7}}
    assert _eval_simple_condition("sum >= target", vars_map) is True
    got = resolve_branch_display_line(2, lines, vars_map)
    assert got == 2, got


def test_python_effect_line() -> None:
    src = """import sys
def main():
    s = sys.stdin.readline().strip()
    st = []
    for c in s:
        if c == '(':
            st.append(')')
        elif c == ')':
            st.pop()
"""
    refined = refine_trace_step_lines(
        [
            TraceStepOut(line=3, vars={"s": {"type": "str", "value": "()"}}, changed=["s"]),
            TraceStepOut(line=4, vars={"st": {"type": "list", "value": []}}, changed=["st"]),
            TraceStepOut(line=6, vars={"c": {"type": "str", "value": ")"}}, changed=["c"]),
        ],
        src,
    )
    assert refined[0].line == 3
    assert refined[1].line == 4
    assert refined[2].line != 7, refined[2].line


def test_cpp_state_change_points_to_push() -> None:
    src = """for (char c : s) {
    if (c == '(') st.push(')');
    else if (c == ')') st.pop();
}"""
    refined = refine_trace_step_lines(
        [
            TraceStepOut(line=2, vars={"c": {"type": "str", "value": "("}}, changed=["c"]),
            TraceStepOut(line=3, vars={"st": {"type": "sequence", "view_hint": "stack", "value": [")"]}}, changed=["st"]),
        ],
        src,
    )
    assert refined[1].line == 2, refined[1].line


def main() -> int:
    test_branch_else_if_cpp()
    test_two_sum_in_seen()
    test_binary_search_compare()
    test_sliding_window_while()
    test_python_effect_line()
    test_cpp_state_change_points_to_push()
    print("trace_line_refine multi-pattern OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
