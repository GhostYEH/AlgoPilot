"""OJ C++ 判题与可视化调试（GDB trace）回归测试。

覆盖 _build_cpp_source 对非 const 引用参数（如 vector<int>&）的具名化修复，
确保力扣风格 C++ 判题与 GDB trace 不会因右值绑定失败而 CE。
"""

from __future__ import annotations

import pytest

from services.oj.cpp_runner import _find_gpp, run_cases_cpp
from services.oj.cpp_trace_runner import _find_gdb, run_trace_cpp, run_trace_cpp_stdio
from services.oj.stdio_runner import run_cases_stdio
from services.oj.trace_runner import run_trace, run_trace_stdio

_HAS_GPP = bool(_find_gpp())
_HAS_GDB = bool(_find_gdb())
_skip_no_gpp = pytest.mark.skipif(not _HAS_GPP, reason="未找到 g++ 工具链")
_skip_no_gdb = pytest.mark.skipif(not _HAS_GDB, reason="未找到 gdb")


_CPP_TWO_SUM = """
class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        unordered_map<int,int> seen;
        for (int i = 0; i < (int)nums.size(); ++i) {
            int comp = target - nums[i];
            if (seen.count(comp)) return {seen[comp], i};
            seen[nums[i]] = i;
        }
        return {};
    }
};
"""

_ENTRY = {"class": "Solution", "method": "twoSum"}
_CASES = [
    {"args": [[2, 7, 11, 15], 9], "expected": [0, 1]},
    {"args": [[3, 2, 4], 6], "expected": [1, 2]},
]

_CPP_STDIO = """
#include <iostream>
using namespace std;
int main() {
    int n; cin >> n;
    long long total = 0;
    for (int i = 0; i < n; ++i) { int a, b; cin >> a >> b; total += a + b; }
    cout << total << endl;
    return 0;
}
"""
_STDIO_CASES = [{"stdin": "2\n1 2\n3 4\n", "stdout": "10\n"}]


@_skip_no_gpp
class TestCppLeetcodeJudge:
    """力扣风格 C++ 判题：非 const 引用参数必须能编译并判题。"""

    def test_two_sum_ac(self):
        r = run_cases_cpp(_CPP_TWO_SUM, entry=_ENTRY, cases=_CASES, time_limit_ms=5000)
        assert r.verdict == "AC", f"verdict={r.verdict} err={r.compile_error}"
        assert r.passed == 2

    def test_wrong_answer(self):
        wrong = """
class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        return {0, 1};
    }
};
"""
        r = run_cases_cpp(wrong, entry=_ENTRY, cases=_CASES, time_limit_ms=5000)
        assert r.verdict == "WA"


@_skip_no_gpp
class TestCppStdioJudge:
    def test_stdio_ac(self):
        r = run_cases_stdio(_CPP_STDIO, cases=_STDIO_CASES, language="cpp", time_limit_ms=5000)
        assert r.verdict == "AC", f"verdict={r.verdict}"
        assert r.passed == 1


@_skip_no_gdb
class TestCppLeetcodeTrace:
    """力扣风格 C++ GDB trace：非 const 引用参数必须能编译并采集步骤。"""

    def test_trace_ok_with_steps(self):
        s = run_trace_cpp(_CPP_TWO_SUM, entry=_ENTRY, case=_CASES[0], time_limit_ms=15000)
        assert s.verdict == "OK", f"verdict={s.verdict} msg={s.message}"
        assert len(s.steps) > 0


@_skip_no_gdb
class TestCppStdioTrace:
    def test_stdio_trace_ok_with_steps(self):
        s = run_trace_cpp_stdio(_CPP_STDIO, case=_STDIO_CASES[0], time_limit_ms=15000)
        assert s.verdict == "OK", f"verdict={s.verdict} msg={s.message}"
        assert len(s.steps) > 0


class TestPythonTraceRegression:
    """Python trace 回归：确保修改 cpp_runner 未波及 Python 路径。"""

    def test_py_leetcode_trace(self):
        code = """
class Solution:
    def twoSum(self, nums, target):
        seen = {}
        for i, x in enumerate(nums):
            if target - x in seen:
                return [seen[target - x], i]
            seen[x] = i
        return []
"""
        s = run_trace(code, entry=_ENTRY, case=_CASES[0], time_limit_ms=5000)
        assert s.verdict == "OK"
        assert len(s.steps) > 0

    def test_py_stdio_trace(self):
        code = """
n = int(input())
total = 0
for _ in range(n):
    a, b = map(int, input().split())
    total += a + b
print(total)
"""
        s = run_trace_stdio(code, case=_STDIO_CASES[0], time_limit_ms=5000)
        assert s.verdict == "OK"
        assert len(s.steps) > 0
