"""本地验证：206 反转链表追踪是否捕获 prev/curr/next 变化。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.oj.runner import LIST_NODE_HELPERS
from services.oj.trace_runner import run_trace

CODE = """
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

entry = {
    "class": "Solution",
    "method": "reverseList",
    "list_arg_indices": [0],
    "_slug": "reverse-linked-list",
}
case = {"args": [[1, 2, 3, 4]]}

summary = run_trace(CODE, entry=entry, case=case)
print("verdict", summary.verdict, "steps", len(summary.steps))
if summary.verdict != "OK":
    print(summary.message)
    sys.exit(1)

for i, s in enumerate(summary.steps):
    if not s.changed:
        continue
    brief = {}
    for k in s.changed:
        v = s.vars.get(k, {})
        t = v.get("type")
        if t == "node_ref":
            val = v.get("value") or {}
            brief[k] = f"->{val.get('node')}"
        elif t == "linked_list":
            val = v.get("value") or {}
            brief[k] = f"head={val.get('head')}"
        else:
            brief[k] = t
    print(f"step {i} line {s.line} changed={s.changed} {brief}")

# 应出现 curr.next 或节点 next 字段变化
has_edge_change = any(
    "curr" in s.changed or "prev" in s.changed or "nxt" in s.changed
    for s in summary.steps
)
print("pointer_steps_ok", has_edge_change)
