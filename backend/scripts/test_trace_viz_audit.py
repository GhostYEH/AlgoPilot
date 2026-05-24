"""可视化调试自检：栈 / 队列 / 哈希场景与解析。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from services.oj.cpp_trace_runner import (
    _cpp_expr_to_payload,
    _normalize_var_payload,
    _parse_stl_stack,
    run_trace_cpp_stdio,
)
from services.oj.trace_runner import run_trace_stdio
from services.oj.trace_serialize import serialize_value

FAILURES: list[str] = []


def ok(name: str) -> None:
    print(f"  OK  {name}")


def fail(name: str, detail: str) -> None:
    FAILURES.append(f"{name}: {detail}")
    print(f"  FAIL {name}: {detail}")


def test_cpp_stack_parse() -> None:
    print("\n[C++] stack / deque 解析")
    garbage = (
        "std::stack wrapping: std::deque with -900422984 elements = "
        "{ 2 '\\002', 0 '\\000' }"
    )
    p = _parse_stl_stack(garbage)
    if p != {"type": "sequence", "view_hint": "stack", "value": []}:
        fail("garbage stack length", repr(p))
    else:
        ok("garbage stack length → empty")

    valid = "std::stack wrapping: std::deque with 2 elements = { 40 '(', 41 ')' }"
    p2 = _normalize_var_payload(_parse_stl_stack(valid) or {})
    if p2 != {"type": "sequence", "view_hint": "stack", "value": ["(", ")"]}:
        fail("valid stack chars", repr(p2))
    else:
        ok("valid stack chars")

    empty = "std::stack wrapping: std::deque with 0 elements"
    p3 = _cpp_expr_to_payload(empty)
    if p3 and p3.get("type") == "sequence" and p3.get("view_hint") == "stack" and p3.get("value") == []:
        ok("empty stack")
    else:
        fail("empty stack", repr(p3))


def test_python_tree_serialize() -> None:
    print("\n[Python] 二叉树序列化")

    class TreeNode:
        def __init__(self, val: int, left=None, right=None):
            self.val = val
            self.left = left
            self.right = right

    root = TreeNode(1, TreeNode(2), TreeNode(3, TreeNode(4), TreeNode(5)))
    tree_nodes: dict = {}
    tree_visited: dict = {}
    snap = serialize_value(root, {}, {}, "root", tree_visited=tree_visited, tree_nodes=tree_nodes)
    if snap.get("type") != "tree":
        fail("tree type", repr(snap))
        return
    g = snap.get("value") or {}
    nodes = g.get("nodes") or {}
    if len(nodes) < 3:
        fail("tree nodes count", repr(nodes))
    else:
        ok(f"tree {len(nodes)} nodes root={g.get('root')}")


def test_python_stack_serialize() -> None:
    print("\n[Python] stack 序列化")
    from collections import deque

    snap = serialize_value(["(", ")"], {}, {}, "st")
    if snap.get("type") != "stack" or snap.get("value") != ["(", ")"]:
        fail("list as st", repr(snap))
    else:
        ok("list as st → stack")

    snap2 = serialize_value(deque([0, 1, 2]), {}, {}, "q")
    if snap2.get("type") != "queue":
        fail("deque as q", repr(snap2))
    else:
        ok("deque as q → queue")


def test_cpp_paren_trace() -> None:
    print("\n[C++] 有效括号 stdio 追踪")
    code = r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string s;
    if (!(cin >> s)) return 0;
    stack<char> st;
    bool is_valid = true;
    for (char c : s) {
        if (c == '(') st.push(c);
        else if (c == ')') {
            if (st.empty()) { is_valid = false; break; }
            st.pop();
        }
    }
    if (!st.empty()) is_valid = false;
    cout << (is_valid ? "true" : "false") << "\n";
    return 0;
}
""".strip()
    r = run_trace_cpp_stdio(
        code,
        case={"stdin": "()\n", "stdout": "true\n"},
        time_limit_ms=12000,
    )
    if r.verdict != "OK":
        fail("paren trace verdict", r.verdict + " " + r.message)
        return
    ok(f"paren trace {len(r.steps)} steps")

    has_stack_type = False
    has_st_other_garbage = False
    for s in r.steps:
        st = s.vars.get("st", {})
        if st.get("type") in ("stack", "sequence") and (
            st.get("view_hint") == "stack" or st.get("type") == "stack"
        ):
            has_stack_type = True
        if st.get("type") == "other" and "std::stack" in str(st.get("value", "")):
            if "-900" in str(st.get("value", "")) or "140732" in str(st.get("value", "")):
                has_st_other_garbage = True

    if has_st_other_garbage:
        fail("st still garbage other", "found corrupt std::stack string in steps")
    else:
        ok("no corrupt st snapshots")

    if not has_stack_type and not any(
        s.vars.get("st", {}).get("type") in ("stack", "sequence") for s in r.steps
    ):
        # empty stack steps are OK as stack type []
        if not any("st" in s.vars for s in r.steps):
            fail("st missing", "no st in any step")
        else:
            ok("st present (may be empty stack)")

    last_with_st = next((s for s in reversed(r.steps) if "st" in s.vars), None)
    if last_with_st:
        st = last_with_st.vars["st"]
        if st.get("type") in ("stack", "sequence"):
            ok(f"final st type={st.get('type')} value={st.get('value')!r}")
        elif st.get("type") == "other":
            fail("final st still other", str(st.get("value"))[:80])


def test_python_two_sum_not_queue() -> None:
    print("\n[Python] 两数之和 trace 含 dict")
    code = """
import sys
def main():
    lines = sys.stdin.read().strip().splitlines()
    n = int(lines[0])
    nums = list(map(int, lines[1].split()))
    target = int(lines[2])
    seen = {}
    for i, x in enumerate(nums):
        need = target - x
        if need in seen:
            print(seen[need], i)
            return
        seen[x] = i
if __name__ == '__main__':
    main()
""".strip()
    r = run_trace_stdio(
        code,
        case={"stdin": "4\n2 7 11 15\n9\n", "stdout": "0 1\n"},
        time_limit_ms=10000,
    )
    if r.verdict != "OK":
        fail("two-sum trace", r.message)
        return
    ok(f"two-sum {len(r.steps)} steps")
    if any(s.vars.get("seen", {}).get("type") == "dict" for s in r.steps):
        ok("seen dict captured")
    else:
        fail("seen dict", "no dict type for seen")


def test_cpp_sliding_window_deque() -> None:
    print("\n[C++] 滑动窗口最大值 deque")
    code = r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, k;
    cin >> n;
    vector<int> nums(n);
    for (int i = 0; i < n; ++i) cin >> nums[i];
    cin >> k;
    deque<int> q;
    for (int i = 0; i < n; ++i) {
        while (!q.empty() && nums[q.back()] <= nums[i]) q.pop_back();
        q.push_back(i);
        if (q.front() <= i - k) q.pop_front();
        if (i >= k - 1) cout << nums[q.front()] << " ";
    }
    cout << "\n";
    return 0;
}
""".strip()
    r = run_trace_cpp_stdio(
        code,
        case={"stdin": "8\n1 3 -1 -3 5 3 6 7\n3\n", "stdout": "3 3 5 5 6 7\n"},
        time_limit_ms=15000,
    )
    if r.verdict != "OK":
        fail("sw-max trace", r.message)
        return
    ok(f"sw-max {len(r.steps)} steps")
    q_types = {s.vars.get("q", {}).get("type") for s in r.steps if "q" in s.vars}
    good_q = q_types & {"queue", "stack", "sequence"}
    bad_other = [
        str(s.vars["q"].get("value", ""))[:40]
        for s in r.steps
        if s.vars.get("q", {}).get("type") == "other"
        and ("8189" in str(s.vars["q"].get("value", "")) or "140732" in str(s.vars["q"].get("value", "")))
    ]
    if bad_other:
        fail("q garbage", bad_other[0])
    elif good_q:
        ok(f"q types {q_types}")
    else:
        ok(f"q types {q_types} (no corrupt snapshots)")


def test_trace_api_preserves_view_hint() -> None:
    print("\n[API] TraceResponse 保留 view_hint")
    from api.oj import _trace_to_response
    from services.oj.cpp_trace_runner import run_trace_cpp_stdio

    code = r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    stack<char> st;
    st.push('x');
    return 0;
}
""".strip()
    summary = run_trace_cpp_stdio(code, case={"stdin": "\n", "stdout": ""}, time_limit_ms=8000)
    if summary.verdict != "OK":
        fail("stack trace for api", summary.verdict)
        return
    resp = _trace_to_response(summary)
    found = False
    for step in resp.steps:
        st = step.vars.get("st")
        if not st:
            continue
        if st.view_hint == "stack" and isinstance(st.value, list) and st.value:
            found = True
            break
    if found:
        ok("view_hint=stack in TraceVarSnapshot")
    else:
        fail("view_hint missing", "st snapshot lost view_hint or empty stack")


def main() -> int:
    print("=== trace viz audit ===")
    test_cpp_stack_parse()
    test_python_tree_serialize()
    test_python_stack_serialize()
    test_cpp_paren_trace()
    test_trace_api_preserves_view_hint()
    test_python_two_sum_not_queue()
    test_cpp_sliding_window_deque()
    print()
    if FAILURES:
        print(f"FAILED {len(FAILURES)}:")
        for f in FAILURES:
            print(" -", f)
        return 1
    print("ALL PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
