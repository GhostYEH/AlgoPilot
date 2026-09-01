"""Counterexample Generator 反例生成器测试。"""

from __future__ import annotations

from services.oj.counterexample import (
    CounterexampleCandidate,
    generate_boundary_cases,
    generate_random_cases,
    verify_and_find_best,
)


class TestBoundaryCaseGeneration:
    def test_array_boundary_cases_cover_key_categories(self):
        cases = generate_boundary_cases(problem_type="array")
        categories = {c.category for c in cases}
        assert "empty" in categories
        assert "single" in categories
        assert "duplicate" in categories
        assert "sorted" in categories
        assert "reverse_sorted" in categories

    def test_binary_search_boundary_cases(self):
        cases = generate_boundary_cases(problem_type="binary-search")
        categories = {c.category for c in cases}
        assert "last_element" in categories
        assert "first_element" in categories
        assert "not_found_upper" in categories
        assert "empty_search" in categories

    def test_linked_list_boundary_cases(self):
        cases = generate_boundary_cases(problem_type="linked-list")
        categories = {c.category for c in cases}
        assert "empty_list" in categories
        assert "single_node" in categories

    def test_dp_boundary_cases(self):
        cases = generate_boundary_cases(problem_type="dp")
        categories = {c.category for c in cases}
        assert "zero_input" in categories
        assert "one_input" in categories

    def test_all_cases_have_reason(self):
        cases = generate_boundary_cases(problem_type="array")
        for c in cases:
            assert c.reason, f"category {c.category} 缺少 reason"

    def test_count_limit(self):
        cases = generate_boundary_cases(problem_type="array", count=3)
        assert len(cases) <= 3


class TestRandomCaseGeneration:
    def test_random_cases_generated(self):
        cases = generate_random_cases(problem_type="array", count=5, seed=42)
        assert len(cases) == 5
        assert all(c.source == "random" for c in cases)

    def test_random_seed_reproducible(self):
        cases1 = generate_random_cases(seed=42, count=3)
        cases2 = generate_random_cases(seed=42, count=3)
        assert [c.args for c in cases1] == [c.args for c in cases2]

    def test_binary_search_random_has_target(self):
        cases = generate_random_cases(problem_type="binary-search", count=3, seed=1)
        for c in cases:
            assert len(c.args) == 2


class TestVerifyAndFindBest:
    def test_correct_code_no_trigger(self):
        candidates = generate_boundary_cases(problem_type="array")

        def user_runner(args):
            return len(args[0]) if args else 0

        def ref_runner(args):
            return len(args[0]) if args else 0

        result = verify_and_find_best(candidates, user_runner=user_runner, reference_runner=ref_runner)
        assert result.best is None
        assert result.trigger_rate == 0.0

    def test_buggy_code_triggers(self):
        candidates = [
            CounterexampleCandidate(args=[[]], category="empty", reason="空输入"),
            CounterexampleCandidate(args=[[1, 2, 3]], category="normal", reason="正常"),
        ]

        def user_runner(args):
            arr = args[0]
            return sum(arr) if arr else -1

        def expected_override(args):
            return sum(args[0])

        result = verify_and_find_best(
            candidates, user_runner=user_runner, expected_override=expected_override
        )
        assert result.best is not None
        assert result.best.category == "empty"
        assert result.best.triggered is True
        assert result.trigger_rate == 50.0

    def test_runtime_error_not_verified(self):
        candidates = [CounterexampleCandidate(args=[[1]], category="test", reason="")]

        def user_runner(args):
            raise RuntimeError("RE")

        result = verify_and_find_best(candidates, user_runner=user_runner, expected_override=lambda a: 1)
        assert result.total_verified == 0
        assert result.best is None

    def test_trigger_rate_calculation(self):
        candidates = [
            CounterexampleCandidate(args=[i], category=f"c{i}", reason="")
            for i in range(4)
        ]

        def user_runner(args):
            return args[0] * 2

        def expected_override(args):
            return args[0] * 2 if args[0] < 2 else args[0] * 3

        result = verify_and_find_best(
            candidates, user_runner=user_runner, expected_override=expected_override
        )
        assert result.total_generated == 4
        assert result.trigger_rate == 50.0

    def test_execution_budget_limits_candidate_checks(self):
        calls = 0

        def runner(args):
            nonlocal calls
            calls += 1
            return args[0]

        candidates = [
            CounterexampleCandidate(args=[i], category=f"c{i}", reason="")
            for i in range(5)
        ]
        result = verify_and_find_best(
            candidates,
            user_runner=runner,
            reference_runner=runner,
            max_execution_count=2,
        )
        assert calls == 2
        assert result.total_verified == 1

    def test_expired_deadline_runs_no_candidate(self):
        calls = 0

        def runner(args):
            nonlocal calls
            calls += 1
            return args[0]

        result = verify_and_find_best(
            [CounterexampleCandidate(args=[1], category="late", reason="")],
            user_runner=runner,
            reference_runner=runner,
            deadline=0.0,
        )
        assert calls == 0
        assert result.total_verified == 0


class TestEarlyStopOptimization:
    """early_stop=True 时找到第一个触发候选后应立即停止。"""

    def test_early_stop_reduces_runner_calls(self):
        call_count = 0

        def user_runner(args):
            nonlocal call_count
            call_count += 1
            return args[0] + 1

        def expected_override(args):
            return args[0] + 2

        candidates = [CounterexampleCandidate(args=[i], category=f"c{i}", reason="") for i in range(8)]
        result = verify_and_find_best(
            candidates, user_runner=user_runner, expected_override=expected_override, early_stop=True
        )
        assert result.best is not None
        assert call_count == 1

    def test_early_stop_best_is_first_triggered(self):
        def user_runner(args):
            return args[0] * 2

        def expected_override(args):
            return args[0] * 3

        candidates = [
            CounterexampleCandidate(args=[0], category="correct", reason=""),
            CounterexampleCandidate(args=[1], category="first_bug", reason=""),
            CounterexampleCandidate(args=[2], category="second_bug", reason=""),
        ]
        result = verify_and_find_best(
            candidates, user_runner=user_runner, expected_override=expected_override, early_stop=True
        )
        assert result.best is not None
        assert result.best.category == "first_bug"

    def test_no_early_stop_verifies_all(self):
        call_count = 0

        def user_runner(args):
            nonlocal call_count
            call_count += 1
            return args[0] * 2

        def expected_override(args):
            return args[0] * 3

        candidates = [CounterexampleCandidate(args=[i], category=f"c{i}", reason="") for i in range(8)]
        result = verify_and_find_best(
            candidates, user_runner=user_runner, expected_override=expected_override, early_stop=False
        )
        assert result.best is not None
        assert call_count == 8


class TestDeduplication:
    """args 完全相同的候选应被去重。"""

    def test_duplicate_args_are_deduplicated(self):
        candidates = [
            CounterexampleCandidate(args=[[1, 2]], category="first", reason=""),
            CounterexampleCandidate(args=[[1, 2]], category="duplicate", reason=""),
            CounterexampleCandidate(args=[[3, 4]], category="third", reason=""),
        ]

        def user_runner(args):
            return sum(args[0])

        def expected_override(args):
            return sum(args[0]) + 1

        result = verify_and_find_best(
            candidates, user_runner=user_runner, expected_override=expected_override
        )
        assert result.total_generated == 2

    def test_all_duplicates_reduced_to_one(self):
        candidates = [
            CounterexampleCandidate(args=[[1]], category=f"c{i}", reason="") for i in range(5)
        ]

        def user_runner(args):
            return 1

        def expected_override(args):
            return 2

        result = verify_and_find_best(
            candidates, user_runner=user_runner, expected_override=expected_override
        )
        assert result.total_generated == 1
        assert result.best is not None
