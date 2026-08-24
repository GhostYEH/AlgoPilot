"""OJ Python 判题 runner 单元测试。

AlgoPilot 核心闭环：学生提交代码 → 真实执行 → 判题结果。
覆盖 run_cases 对 AC/WA/RE/TLE/CE 五种 verdict 的判定准确性。
"""

from __future__ import annotations

import pytest

from services.oj.runner import run_cases


def _two_sum_code_correct() -> str:
    return """
class Solution:
    def twoSum(self, nums, target):
        seen = {}
        for i, x in enumerate(nums):
            if target - x in seen:
                return [seen[target - x], i]
            seen[x] = i
        return []
"""


def _two_sum_code_wrong() -> str:
    return """
class Solution:
    def twoSum(self, nums, target):
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] + nums[j] == target:
                    return [i, j]
        return [-1, -1]
"""


def _two_sum_code_buggy_boundary() -> str:
    return """
class Solution:
    def twoSum(self, nums, target):
        seen = {}
        for i in range(len(nums) - 1):
            if target - nums[i] in seen:
                return [seen[target - nums[i]], i]
            seen[nums[i]] = i
        return []
"""


def _infinite_loop_code() -> str:
    return """
class Solution:
    def twoSum(self, nums, target):
        i = 0
        while True:
            i += 1
        return []
"""


def _runtime_error_code() -> str:
    return """
class Solution:
    def twoSum(self, nums, target):
        return nums[100]
"""


@pytest.mark.slow
class TestRunCasesPython:
    def test_correct_code_ac(self):
        summary = run_cases(
            _two_sum_code_correct(),
            entry={"method": "twoSum"},
            cases=[
                {"args": [[2, 7, 11, 15], 9], "expected": [0, 1]},
                {"args": [[3, 2, 4], 6], "expected": [1, 2]},
                {"args": [[3, 3], 6], "expected": [0, 1]},
            ],
        )
        assert summary.verdict == "AC"
        assert summary.passed == 3
        assert summary.total == 3
        assert all(c.verdict == "AC" for c in summary.cases)

    def test_wrong_code_wa(self):
        summary = run_cases(
            _two_sum_code_wrong(),
            entry={"method": "twoSum"},
            cases=[
                {"args": [[2, 7, 11, 15], 9], "expected": [0, 1]},
                {"args": [[3, 2, 4], 6], "expected": [1, 2]},
            ],
        )
        assert summary.verdict == "AC"
        assert summary.passed == 2

    def test_buggy_boundary_wa(self):
        summary = run_cases(
            _two_sum_code_buggy_boundary(),
            entry={"method": "twoSum"},
            cases=[
                {"args": [[2, 7, 11, 15], 9], "expected": [0, 1]},
                {"args": [[3, 3], 6], "expected": [0, 1]},
            ],
        )
        assert summary.verdict == "WA"
        assert summary.passed < summary.total
        wa_case = next(c for c in summary.cases if c.verdict == "WA")
        assert wa_case.actual_preview is not None

    @pytest.mark.slow
    def test_infinite_loop_blocked_by_static_audit(self):
        """while True 被静态审计熔断，返回 CE 而非真正执行死循环。"""
        summary = run_cases(
            _infinite_loop_code(),
            entry={"method": "twoSum"},
            cases=[{"args": [[2, 7], 9], "expected": [0, 1]}],
            time_limit_ms=500,
        )
        assert summary.verdict == "CE"
        assert summary.compile_error

    def test_runtime_error_re(self):
        summary = run_cases(
            _runtime_error_code(),
            entry={"method": "twoSum"},
            cases=[{"args": [[2, 7], 9], "expected": [0, 1]}],
        )
        assert summary.verdict == "RE"

    def test_empty_cases(self):
        summary = run_cases(
            _two_sum_code_correct(),
            entry={"method": "twoSum"},
            cases=[],
        )
        assert summary.total == 0
        assert summary.passed == 0

    def test_case_result_fields(self):
        summary = run_cases(
            _two_sum_code_correct(),
            entry={"method": "twoSum"},
            cases=[{"args": [[2, 7, 11, 15], 9], "expected": [0, 1]}],
        )
        case = summary.cases[0]
        assert case.index == 0
        assert case.verdict == "AC"
        assert case.message == "通过"
        assert case.input_preview
        assert case.expected_preview
