from __future__ import annotations

from services.oj.trace_runner import TraceStepOut
from services.oj.trace_steps_filter import (
    collapse_consecutive_same_line_steps,
    compress_initialization_phase,
)


def test_collapse_same_line_keeps_initialized_container_frame() -> None:
    steps = [
        TraceStepOut(
            line=4,
            vars={"a": {"type": "sequence", "view_hint": "array", "value": [0, 999]}},
            changed=["a"],
        ),
        TraceStepOut(
            line=4,
            vars={"a": {"type": "sequence", "view_hint": "array", "value": [3, 4]}},
            changed=["a"],
        ),
        TraceStepOut(
            line=5,
            vars={
                "a": {"type": "sequence", "view_hint": "array", "value": [3, 4]},
                "i": {"type": "int", "value": 0},
            },
            changed=["i"],
        ),
    ]

    collapsed = collapse_consecutive_same_line_steps(steps)

    assert [step.line for step in collapsed] == [4, 5]
    assert collapsed[0].vars["a"]["value"] == [3, 4]
    assert collapsed[0].changed == ["a"]
    assert collapsed[1].changed == ["i"]


def test_collapse_same_line_preserves_multiple_statements() -> None:
    steps = [
        TraceStepOut(line=1, vars={"a": {"type": "int", "value": 0}}, changed=["a"]),
        TraceStepOut(line=1, vars={"a": {"type": "int", "value": 1}}, changed=["a"]),
        TraceStepOut(
            line=1,
            vars={"a": {"type": "int", "value": 1}, "b": {"type": "int", "value": 2}},
            changed=["b"],
        ),
        TraceStepOut(
            line=1,
            vars={
                "a": {"type": "int", "value": 1},
                "b": {"type": "int", "value": 2},
                "c": {"type": "int", "value": 3},
            },
            changed=["c"],
        ),
    ]

    collapsed = collapse_consecutive_same_line_steps(steps)

    assert len(collapsed) == 3
    assert [step.changed for step in collapsed] == [["a"], ["b"], ["c"]]


# ============ compress_initialization_phase 测试 ============

_CPP_SOURCE = """\
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n; cin >> n;
    vector<int> a(n);
    for (int i = 0; i < n; i++) cin >> a[i];
    int ans = 0;
    for (int i = 0; i < n; i++) ans += a[i];
    cout << ans << endl;
    return 0;
}
"""

_PY_SOURCE = """\
n = int(input())
arr = list(map(int, input().split()))
ans = 0
for x in arr:
    ans += x
print(ans)
"""


def _step(line: int, vars_: dict, changed: list[str]) -> TraceStepOut:
    return TraceStepOut(line=line, vars=vars_, changed=changed)


def test_compress_cpp_readin_loop_keeps_only_head_tail() -> None:
    """C++ 读入循环 n 步应被压缩为首末两步。"""
    steps = [
        _step(4, {"n": {"type": "int", "value": 5}}, ["n"]),          # cin >> n
        _step(5, {"n": {"type": "int", "value": 5}, "a": {"type": "sequence", "view_hint": "vector", "value": []}}, ["a"]),  # vector<int> a(n)
        _step(6, {"a": {"type": "sequence", "view_hint": "vector", "value": [1]}}, ["a"]),  # cin >> a[0]
        _step(6, {"a": {"type": "sequence", "view_hint": "vector", "value": [1, 2]}}, ["a"]),  # cin >> a[1]
        _step(6, {"a": {"type": "sequence", "view_hint": "vector", "value": [1, 2, 3]}}, ["a"]),  # cin >> a[2]
        _step(6, {"a": {"type": "sequence", "view_hint": "vector", "value": [1, 2, 3, 4]}}, ["a"]),  # cin >> a[3]
        _step(6, {"a": {"type": "sequence", "view_hint": "vector", "value": [1, 2, 3, 4, 5]}}, ["a"]),  # cin >> a[4]
        _step(7, {"ans": {"type": "int", "value": 0}}, ["ans"]),      # 算法核心起点
        _step(8, {"ans": {"type": "int", "value": 1}}, ["ans"]),      # ans += a[0]
        _step(8, {"ans": {"type": "int", "value": 3}}, ["ans"]),      # ans += a[1]
        _step(8, {"ans": {"type": "int", "value": 15}}, ["ans"]),     # ans += a[4]
    ]

    out = compress_initialization_phase(steps, source=_CPP_SOURCE)

    # 读入段（line 4-6 共 7 步）应被压缩为 2 步
    # 算法段（line 7-8 共 4 步）应全部保留
    init_lines = [s.line for s in out if s.line in (4, 5, 6)]
    algo_lines = [s.line for s in out if s.line in (7, 8)]
    assert init_lines == [4, 6], f"读入段应压缩为首末两步，实际: {init_lines}"
    assert len(algo_lines) == 4, f"算法段应全部保留，实际: {algo_lines}"


def test_compress_python_readin_keeps_head_tail() -> None:
    """Python 读入 + 构造应被压缩。"""
    steps = [
        _step(1, {"n": {"type": "int", "value": 5}}, ["n"]),          # n = int(input())
        _step(2, {"arr": {"type": "list", "value": [1, 2, 3, 4, 5]}}, ["arr"]),  # arr = list(map(...))
        _step(3, {"ans": {"type": "int", "value": 0}}, ["ans"]),      # ans = 0
        _step(4, {"ans": {"type": "int", "value": 1}}, ["ans"]),      # ans += x
        _step(4, {"ans": {"type": "int", "value": 3}}, ["ans"]),
        _step(4, {"ans": {"type": "int", "value": 15}}, ["ans"]),
    ]

    out = compress_initialization_phase(steps, source=_PY_SOURCE)

    # 前两步是读入/构造，但只有 2 步 < min_compress(4)，不压缩
    # 算法段全部保留
    assert [s.line for s in out] == [1, 2, 3, 4, 4, 4]


def test_compress_skips_short_segments() -> None:
    """短于 min_compress 的准备段不应被压缩。"""
    steps = [
        _step(1, {"n": {"type": "int", "value": 5}}, ["n"]),          # input()
        _step(2, {"arr": {"type": "list", "value": [1, 2, 3]}}, ["arr"]),  # list()
        _step(3, {"ans": {"type": "int", "value": 0}}, ["ans"]),
        _step(4, {"ans": {"type": "int", "value": 6}}, ["ans"]),
    ]

    out = compress_initialization_phase(steps, source=_PY_SOURCE, min_compress=4)

    # 读入段只有 2 步，不压缩
    assert len(out) == 4


def test_compress_preserves_algorithm_core_with_res() -> None:
    """变化的变量含 res/ans 时不应误判为读入阶段。"""
    source = """\
n = int(input())
res = 0
for i in range(n):
    res += i
"""
    steps = [
        _step(1, {"n": {"type": "int", "value": 3}}, ["n"]),
        _step(2, {"res": {"type": "int", "value": 0}}, ["res"]),
        _step(4, {"res": {"type": "int", "value": 0}, "i": {"type": "int", "value": 0}}, ["i"]),
        _step(4, {"res": {"type": "int", "value": 0}, "i": {"type": "int", "value": 1}}, ["i"]),
        _step(4, {"res": {"type": "int", "value": 1}, "i": {"type": "int", "value": 1}}, ["res"]),
        _step(4, {"res": {"type": "int", "value": 3}, "i": {"type": "int", "value": 2}}, ["res"]),
    ]

    out = compress_initialization_phase(steps, source=source)

    # line 4 的步骤变化变量是 res/i，不是纯容器，应全部保留
    line4_count = sum(1 for s in out if s.line == 4)
    assert line4_count == 4, f"算法核心段不应被压缩，实际保留: {line4_count}"


def test_compress_empty_source_returns_original() -> None:
    """无源码时不压缩。"""
    steps = [_step(1, {"a": {"type": "int", "value": 1}}, ["a"])]
    out = compress_initialization_phase(steps, source="")
    assert out is steps


# ============ 防止误压缩算法核心的回归测试 ============

_DP_SOURCE = """\
n = int(input())
m = int(input())
dp = [[0] * m for _ in range(n)]
for i in range(n):
    for j in range(m):
        dp[i][j] = i + j
print(dp[n-1][m-1])
"""


def test_compress_does_not_compress_dp_fill() -> None:
    """DP 填表循环不能被误判为读入阶段（dp 是算法核心数据结构）。"""
    steps = [
        _step(1, {"n": {"type": "int", "value": 3}}, ["n"]),
        _step(2, {"m": {"type": "int", "value": 3}}, ["m"]),
        _step(3, {"dp": {"type": "matrix", "value": {"rows": 3, "cols": 3, "cells": [[0,0,0],[0,0,0],[0,0,0]]}}}, ["dp"]),
        _step(5, {"dp": {"type": "matrix", "value": {"rows": 3, "cols": 3, "cells": [[0,1,0],[0,0,0],[0,0,0]]}}}, ["dp"]),
        _step(5, {"dp": {"type": "matrix", "value": {"rows": 3, "cols": 3, "cells": [[0,1,2],[0,0,0],[0,0,0]]}}}, ["dp"]),
        _step(5, {"dp": {"type": "matrix", "value": {"rows": 3, "cols": 3, "cells": [[0,1,2],[1,0,0],[0,0,0]]}}}, ["dp"]),
        _step(5, {"dp": {"type": "matrix", "value": {"rows": 3, "cols": 3, "cells": [[0,1,2],[1,2,0],[0,0,0]]}}}, ["dp"]),
        _step(5, {"dp": {"type": "matrix", "value": {"rows": 3, "cols": 3, "cells": [[0,1,2],[1,2,3],[0,0,0]]}}}, ["dp"]),
    ]

    out = compress_initialization_phase(steps, source=_DP_SOURCE)

    # line 5 是 DP 填表，变化变量是 dp（算法核心），不应被压缩
    line5_count = sum(1 for s in out if s.line == 5)
    assert line5_count == 5, f"DP 填表步不应被压缩，实际保留: {line5_count}"


_BFS_SOURCE = """\
from collections import deque
n, m = map(int, input().split())
graph = [[] for _ in range(n)]
for _ in range(m):
    u, v = map(int, input().split())
    graph[u].append(v)
    graph[v].append(u)
visited = [False] * n
q = deque([0])
visited[0] = True
while q:
    u = q.popleft()
    for v in graph[u]:
        if not visited[v]:
            visited[v] = True
            q.append(v)
"""


def test_compress_does_not_compress_bfs_queue() -> None:
    """BFS 入队操作不能被误判为读入阶段（q/visited/graph 是算法核心）。"""
    steps = [
        _step(10, {"q": {"type": "sequence", "view_hint": "deque", "value": [0]}, "visited": {"type": "list", "value": [True, False, False]}}, ["q", "visited"]),
        _step(12, {"u": {"type": "int", "value": 0}, "q": {"type": "sequence", "view_hint": "deque", "value": []}}, ["u", "q"]),
        _step(14, {"visited": {"type": "list", "value": [True, True, False]}, "q": {"type": "sequence", "view_hint": "deque", "value": [1]}}, ["visited", "q"]),
        _step(14, {"visited": {"type": "list", "value": [True, True, True]}, "q": {"type": "sequence", "view_hint": "deque", "value": [1, 2]}}, ["visited", "q"]),
        _step(12, {"u": {"type": "int", "value": 1}, "q": {"type": "sequence", "view_hint": "deque", "value": [2]}}, ["u", "q"]),
        _step(12, {"u": {"type": "int", "value": 2}, "q": {"type": "sequence", "view_hint": "deque", "value": []}}, ["u", "q"]),
    ]

    out = compress_initialization_phase(steps, source=_BFS_SOURCE)

    # BFS 核心循环步全部保留（q/visited/u 都不是"读入缓冲容器"）
    assert len(out) == 6, f"BFS 核心步不应被压缩，实际保留: {len(out)}"


_MONO_STACK_SOURCE = """\
n = int(input())
nums = list(map(int, input().split()))
st = []
res = [-1] * n
for i in range(n):
    while st and nums[st[-1]] < nums[i]:
        res[st.pop()] = i
    st.append(i)
"""


def test_compress_does_not_compress_monotonic_stack() -> None:
    """单调栈入栈/出栈不能被误判为读入阶段（st 是算法核心）。"""
    steps = [
        _step(5, {"st": {"type": "sequence", "view_hint": "stack", "value": [0]}, "i": {"type": "int", "value": 0}, "res": {"type": "list", "value": [-1, -1, -1]}}, ["st", "i"]),
        _step(6, {"st": {"type": "sequence", "view_hint": "stack", "value": []}, "res": {"type": "list", "value": [1, -1, -1]}}, ["st", "res"]),
        _step(7, {"st": {"type": "sequence", "view_hint": "stack", "value": [1]}, "i": {"type": "int", "value": 1}}, ["st", "i"]),
        _step(5, {"st": {"type": "sequence", "view_hint": "stack", "value": [1, 2]}, "i": {"type": "int", "value": 2}}, ["st", "i"]),
    ]

    out = compress_initialization_phase(steps, source=_MONO_STACK_SOURCE)

    # 单调栈核心步全部保留（st 是算法核心，不在读入缓冲容器名单）
    assert len(out) == 4, f"单调栈核心步不应被压缩，实际保留: {len(out)}"


def test_compress_does_not_misidentify_for_loop_as_init() -> None:
    """for(int i=0;...) 形式的算法循环不能被误判为读入阶段。"""
    source = """\
int n; cin >> n;
vector<int> a(n);
for (int i = 0; i < n; i++) cin >> a[i];
int ans = 0;
for (int i = 0; i < n; i++) ans = max(ans, a[i]);
"""
    steps = [
        _step(1, {"n": {"type": "int", "value": 3}}, ["n"]),
        _step(2, {"a": {"type": "sequence", "view_hint": "vector", "value": []}}, ["a"]),
        _step(3, {"a": {"type": "sequence", "view_hint": "vector", "value": [1]}}, ["a"]),
        _step(3, {"a": {"type": "sequence", "view_hint": "vector", "value": [1, 2]}}, ["a"]),
        _step(3, {"a": {"type": "sequence", "view_hint": "vector", "value": [1, 2, 3]}}, ["a"]),
        _step(4, {"ans": {"type": "int", "value": 0}}, ["ans"]),
        _step(5, {"ans": {"type": "int", "value": 1}, "i": {"type": "int", "value": 0}}, ["ans", "i"]),
        _step(5, {"ans": {"type": "int", "value": 2}, "i": {"type": "int", "value": 1}}, ["ans", "i"]),
        _step(5, {"ans": {"type": "int", "value": 3}, "i": {"type": "int", "value": 2}}, ["ans", "i"]),
    ]

    out = compress_initialization_phase(steps, source=source)

    # line 1-3 构成连续 init 段（cin >> n / vector a(n) / cin >> a[i]）共 5 步 ≥ 4，压缩为首末
    # 保留：line 1（首）+ line 3（末，a=[1,2,3]）
    init_lines = [s.line for s in out if s.line in (1, 2, 3)]
    assert init_lines == [1, 3], f"读入段应压缩为首末两步，实际: {init_lines}"
    # line 5（ans = max(...)）是算法核心，3 步全部保留
    line5_count = sum(1 for s in out if s.line == 5)
    assert line5_count == 3, f"算法循环不应被压缩，实际保留: {line5_count}"
