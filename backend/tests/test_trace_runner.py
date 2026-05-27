"""Trace Runner：Python 力扣风格追踪。"""

from __future__ import annotations

import pytest

from services.oj.trace_runner import run_trace

REVERSE_LIST_CODE = """
class Solution:
    def reverseList(self, head):
        prev = None
        curr = head
        while curr:
            nxt = curr.next
            curr.next = prev
            prev = curr
            curr = nxt
        return prev
"""

SUM_LOOP_CODE = """
class Solution:
    def sumN(self, n):
        s = 0
        for i in range(1, n + 1):
            s += i
        return s
"""


@pytest.mark.parametrize(
    "code,method,args",
    [
        (REVERSE_LIST_CODE, "reverseList", [[1, 2, 3]]),
        (SUM_LOOP_CODE, "sumN", [5]),
    ],
)
def test_python_trace_ok(code: str, method: str, args: list) -> None:
    entry = {"class": "Solution", "method": method, "list_arg_indices": [0] if method == "reverseList" else []}
    summary = run_trace(code, entry=entry, case={"args": args}, language="python")
    assert summary.verdict == "OK", summary.message
    assert len(summary.steps) >= 1


def test_python_trace_syntax_error() -> None:
    summary = run_trace("def oops(:\n  pass", entry={"method": "f"}, case={"args": []})
    assert summary.verdict == "CE"
