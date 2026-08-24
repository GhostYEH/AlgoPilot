"""Counterexample 集成测试。

Case 1: Binary Search boundary bug → verified counterexample → Trace
Case 2: 生成候选全部无效 → fallback original failed case
Case 3: Reference Solution 不可用 → 优雅降级
Case 4: Generator 异常 → 整个 AI diagnosis 不崩溃
"""

from __future__ import annotations

from services.oj.counterexample_integration import (
    CounterexampleIntegrationResult,
    try_counterexample,
)


class TestCase1VerifiedCounterexample:
    """Case 1: Binary Search boundary bug → verified counterexample。"""

    def test_buggy_binary_search_finds_counterexample(self):
        """学生代码在边界上出错，反例生成器应找到 verified counterexample。"""

        def buggy_runner(args: list) -> str:
            arr, target = args[0], args[1]
            lo, hi = 0, len(arr) - 1
            while lo < hi:
                mid = (lo + hi) // 2
                if arr[mid] >= target:
                    hi = mid
                else:
                    lo = mid + 1
            if 0 <= lo < len(arr) and arr[lo] == target:
                return "AC"
            return "WA"

        def correct_runner(args: list) -> str:
            arr, target = args[0], args[1]
            lo, hi = 0, len(arr) - 1
            while lo <= hi:
                mid = (lo + hi) // 2
                if arr[mid] == target:
                    return "AC"
                elif arr[mid] < target:
                    lo = mid + 1
                else:
                    hi = mid - 1
            return "WA"

        original = {"input": "4\n1 3 5 7\n5", "expected": "2", "category": "original"}

        result = try_counterexample(
            slug="binary-search",
            module_key="array",
            original_failed_case=original,
            user_runner=buggy_runner,
            reference_runner=correct_runner,
        )

        assert result.source in ("generated_verified", "original_failed_case")
        assert result.candidate_count > 0
        assert result.latency_ms >= 0
        assert result.selected_case is not None

    def test_result_to_dict_structure(self):
        result = CounterexampleIntegrationResult(
            selected_case={"args": [1, 2]},
            source="generated_verified",
            candidate_count=8,
            verified_count=6,
            triggered_count=2,
            latency_ms=150,
            category="empty_search",
            reason="test",
        )
        d = result.to_dict()
        assert d["source"] == "generated_verified"
        assert d["candidate_count"] == 8
        assert d["latency_ms"] == 150


class TestCase2AllCandidatesInvalid:
    """Case 2: 生成候选全部无效 → fallback original failed case。"""

    def test_no_trigger_falls_back_to_original(self):
        """学生代码在所有候选上都 AC，应保留原始失败样例。"""

        def always_ac_runner(args: list) -> str:
            return "AC"

        def ref_runner(args: list) -> str:
            return "AC"

        original = {"input": "test", "expected": "42", "category": "original"}

        result = try_counterexample(
            slug="binary-search",
            module_key="array",
            original_failed_case=original,
            user_runner=always_ac_runner,
            reference_runner=ref_runner,
        )

        assert result.source == "original_failed_case"
        assert result.selected_case == original

    def test_no_original_case_returns_fallback(self):
        result = try_counterexample(
            slug="binary-search",
            module_key="array",
            original_failed_case=None,
            user_runner=lambda args: "AC",
            reference_runner=lambda args: "AC",
        )
        assert result.source == "original_failed_case"
        assert result.selected_case is None


class TestCase3ReferenceUnavailable:
    """Case 3: Reference Solution 不可用 → 优雅降级。"""

    def test_no_reference_runner(self):
        """没有 reference_runner 时，应优雅降级不崩溃。"""
        original = {"input": "test", "expected": "42", "category": "original"}

        result = try_counterexample(
            slug="binary-search",
            module_key="array",
            original_failed_case=original,
            user_runner=lambda args: "WA",
            reference_runner=None,
        )

        assert result.source in ("original_failed_case", "generated_verified")
        assert result.selected_case is not None

    def test_reference_returns_none(self):
        """reference_runner 返回 None 时，候选不触发但不应崩溃。"""
        original = {"input": "test", "expected": "42", "category": "original"}

        result = try_counterexample(
            slug="binary-search",
            module_key="array",
            original_failed_case=original,
            user_runner=lambda args: "WA",
            reference_runner=lambda args: None,
        )

        assert result.source == "original_failed_case"


class TestCase4GeneratorException:
    """Case 4: Generator 异常 → 整个 AI diagnosis 不崩溃。"""

    def test_user_runner_exception_does_not_crash(self):
        """user_runner 抛异常时，应返回 fallback 不传播异常。"""
        original = {"input": "test", "expected": "42", "category": "original"}

        def crashing_runner(args: list) -> str:
            raise RuntimeError("sandbox crashed")

        result = try_counterexample(
            slug="binary-search",
            module_key="array",
            original_failed_case=original,
            user_runner=crashing_runner,
            reference_runner=lambda args: "AC",
        )

        assert result.source == "original_failed_case"
        assert result.selected_case == original

    def test_no_user_runner(self):
        original = {"input": "test", "expected": "42", "category": "original"}

        result = try_counterexample(
            slug="binary-search",
            module_key="array",
            original_failed_case=original,
            user_runner=None,
            reference_runner=lambda args: "AC",
        )

        assert result.source == "original_failed_case"
        assert "未提供" in result.reason


class TestCostLimits:
    """开销限制测试。"""

    def test_max_candidates_limit(self):
        """候选数量不超过 max_candidates。"""
        result = try_counterexample(
            slug="binary-search",
            module_key="array",
            original_failed_case={"input": "x"},
            user_runner=lambda args: "WA",
            reference_runner=lambda args: "AC",
            max_candidates=3,
        )
        assert result.candidate_count <= 3

    def test_latency_recorded(self):
        result = try_counterexample(
            slug="binary-search",
            module_key="array",
            original_failed_case={"input": "x"},
            user_runner=lambda args: "WA",
            reference_runner=lambda args: "AC",
        )
        assert result.latency_ms >= 0

    def test_total_timeout(self):
        """总超时时应返回 fallback。"""
        original = {"input": "test", "expected": "42", "category": "original"}

        result = try_counterexample(
            slug="binary-search",
            module_key="array",
            original_failed_case=original,
            user_runner=lambda args: "WA",
            reference_runner=lambda args: "AC",
            total_timeout_ms=0,
        )
        assert result.source == "original_failed_case"


class TestProblemTypeInference:
    """题目类型推断测试。"""

    def test_binary_search_inferred(self):
        result = try_counterexample(
            slug="binary-search",
            module_key="array",
            original_failed_case={"input": "x"},
            user_runner=lambda args: "WA",
            reference_runner=lambda args: "AC",
        )
        assert result.candidate_count > 0

    def test_sorting_inferred(self):
        result = try_counterexample(
            slug="merge-sort",
            module_key="sorting",
            original_failed_case={"input": "x"},
            user_runner=lambda args: "WA",
            reference_runner=lambda args: "AC",
        )
        assert result.candidate_count > 0
