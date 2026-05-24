"""验证：62 不同路径 — matrix 序列化 + 演示旁白。"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.oj.trace_demo_narration import generate_demo_narration
from services.oj.trace_runner import run_trace
from services.oj.trace_serialize import is_matrix, matrix_payload

assert is_matrix([[1, 2], [3, 4]])
assert not is_matrix([[1, 2], [3]])
m = matrix_payload([[1, 0], [1, 1]])
assert m["type"] == "matrix" and m["value"]["rows"] == 2

CODE = """
class Solution:
    def uniquePaths(self, m, n):
        dp = [[1] * n for _ in range(m)]
        for i in range(1, m):
            for j in range(1, n):
                dp[i][j] = dp[i - 1][j] + dp[i][j - 1]
        return dp[m - 1][n - 1]
"""

entry = {"class": "Solution", "method": "uniquePaths", "_slug": "unique-paths"}
summary = run_trace(CODE, entry=entry, case={"args": [3, 3]})
print("trace", summary.verdict, "steps", len(summary.steps))
assert summary.verdict == "OK"

has_matrix = any(
    (s.vars.get("dp") or {}).get("type") == "matrix" for s in summary.steps
)
print("has_matrix", has_matrix)
assert has_matrix

steps_raw = [
    {"line": s.line, "changed": s.changed, "vars": s.vars} for s in summary.steps
]
narr = generate_demo_narration("unique-paths", CODE, steps_raw)
print("demo_narrations", len(narr or []))
assert narr and len(narr) >= 3
print("sample", narr[2])
