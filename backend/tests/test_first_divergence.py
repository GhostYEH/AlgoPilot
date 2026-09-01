"""First Divergence 首次状态偏离检测单元测试。

覆盖场景：
1. 学生与参考解在同一变量首次偏离 → detected=True
2. 学生与参考解完全一致 → detected=False
3. 无关事件插入、变量重命名、循环步数不同 → 语义对齐
4. 无公共变量 → detected=False
5. 空 trace → detected=False + reason
6. _extract_var_value / _values_equal / _format_state 辅助函数
7. run_first_divergence_analysis: 无 AC 提交 → null + reason
8. run_first_divergence_analysis: 学生代码与参考解相同 → null + reason
9. run_first_divergence_analysis: 参考解运行失败 → null + reason
10. run_first_divergence_analysis: 正常流程 → detected=True
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from models.db_models import Base, OjSubmission, User
from services.oj.first_divergence import (
    FirstDivergenceResult,
    _build_source_line_context,
    _extract_var_value,
    _find_common_keys,
    _format_state,
    _values_equal,
    _vars_at_step,
    detect_first_divergence,
    find_reference_solution,
    run_first_divergence_analysis,
    select_reference_solution,
)


def _step(line: int, vars_dict: dict[str, Any]) -> dict[str, Any]:
    """构造 trace step，变量格式与生产一致：{name: {type: ..., value: ...}}。"""
    wrapped = {}
    for k, v in vars_dict.items():
        wrapped[k] = {"type": type(v).__name__, "value": v}
    return {"line": line, "vars": wrapped, "changed": list(vars_dict.keys())}


@pytest.fixture
def db_session() -> Session:
    """内存 SQLite 数据库，包含真实表结构。"""
    engine = create_engine("sqlite://", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, future=True)
    session = SessionLocal()
    yield session
    session.close()


class TestHelperFunctions:
    def test_extract_var_value_from_dict_snapshot(self):
        assert _extract_var_value({"type": "int", "value": 42}) == 42

    def test_extract_var_value_passthrough_for_non_dict(self):
        assert _extract_var_value([1, 2, 3]) == [1, 2, 3]
        assert _extract_var_value("hello") == "hello"

    def test_values_equal_int_float_precision(self):
        assert _values_equal(1, 1.0) is True
        assert _values_equal(1.0, 1.0 + 1e-12) is True
        assert _values_equal(1, 2) is False

    def test_values_equal_none_handling(self):
        assert _values_equal(None, None) is True
        assert _values_equal(None, 0) is False
        assert _values_equal(0, None) is False

    def test_values_equal_lists(self):
        assert _values_equal([1, 2, 3], [1, 2, 3]) is True
        assert _values_equal([1, 2], [1, 2, 3]) is False
        assert _values_equal([1, 2, 3], [1, 2, 4]) is False

    def test_values_equal_dicts(self):
        assert _values_equal({"a": 1}, {"a": 1}) is True
        assert _values_equal({"a": 1}, {"a": 1, "b": 2}) is False
        assert _values_equal({"a": 1}, {"a": 2}) is False

    def test_vars_at_step_extracts_values(self):
        step = _step(5, {"lo": 0, "hi": 10, "mid": 5})
        result = _vars_at_step(step)
        assert result == {"lo": 0, "hi": 10, "mid": 5}

    def test_find_common_keys_excludes_underscore(self):
        common = _find_common_keys({"lo": 1, "_tmp": 2, "hi": 3}, {"lo": 1, "hi": 3, "_other": 5})
        assert common == ["hi", "lo"]

    def test_format_state_with_focus_keys(self):
        result = _format_state({"lo": 0, "hi": 10, "mid": 5}, focus_keys=["mid"])
        assert result == "mid=5"

    def test_format_state_truncates_long_values(self):
        long_list = list(range(100))
        result = _format_state({"arr": long_list})
        assert "..." in result


class TestDetectFirstDivergence:
    def test_detects_variable_divergence_at_step_2(self):
        """二分查找：学生在 step 2 的 mid 偏离参考解。"""
        student_steps = [
            _step(1, {"lo": 0, "hi": 6}),
            _step(2, {"lo": 0, "hi": 6, "mid": 3}),
            _step(3, {"lo": 0, "hi": 2, "mid": 3}),
        ]
        reference_steps = [
            _step(1, {"lo": 0, "hi": 6}),
            _step(2, {"lo": 0, "hi": 6, "mid": 3}),
            _step(3, {"lo": 0, "hi": 2, "mid": 1}),
        ]
        result = detect_first_divergence(
            student_steps=student_steps,
            reference_steps=reference_steps,
        )
        assert result.detected is True
        assert result.step_index == 2
        assert result.divergent_variable == "mid"
        assert "mid" in result.explanation

    def test_no_divergence_when_traces_identical(self):
        steps = [
            _step(1, {"lo": 0, "hi": 6}),
            _step(2, {"lo": 0, "hi": 6, "mid": 3}),
        ]
        result = detect_first_divergence(student_steps=steps, reference_steps=steps)
        assert result.detected is False
        assert "一致" in result.reason

    def test_step_count_difference_with_different_final_state_detected(self):
        """学生多循环一次且最终状态不同，仍应定位真实状态偏离。"""
        student_steps = [
            _step(1, {"i": 0}),
            _step(2, {"i": 1}),
            _step(2, {"i": 2}),
        ]
        reference_steps = [
            _step(1, {"i": 0}),
            _step(2, {"i": 1}),
        ]
        result = detect_first_divergence(
            student_steps=student_steps,
            reference_steps=reference_steps,
        )
        assert result.detected is True
        assert result.student_state == "i=2"
        assert result.reference_state == "i=1"

    def test_irrelevant_assignment_is_aligned_as_noise(self):
        reference_steps = [
            _step(1, {"left": 0, "right": 4}),
            _step(2, {"left": 1, "right": 4}),
            _step(3, {"left": 1, "right": 3}),
        ]
        student_steps = [
            _step(10, {"left": 0, "right": 4}),
            _step(11, {"left": 0, "right": 4, "tmp": 99}),
            _step(12, {"left": 1, "right": 4}),
            _step(13, {"left": 1, "right": 3}),
        ]
        result = detect_first_divergence(
            student_steps=student_steps,
            reference_steps=reference_steps,
        )
        assert result.detected is False

    def test_variable_renaming_does_not_create_divergence(self):
        student_steps = [
            _step(1, {"l": 0, "r": 5}),
            _step(2, {"l": 1, "r": 5}),
            _step(3, {"l": 1, "r": 4}),
        ]
        reference_steps = [
            _step(11, {"left": 0, "right": 5}),
            _step(12, {"left": 1, "right": 5}),
            _step(13, {"left": 1, "right": 4}),
        ]
        result = detect_first_divergence(
            student_steps=student_steps,
            reference_steps=reference_steps,
        )
        assert result.detected is False

    def test_extra_loop_iteration_realigns_to_key_states(self):
        student_steps = [
            _step(1, {"i": 0}),
            _step(2, {"i": 1}),
            _step(3, {"i": 2}),
            _step(2, {"i": 1}),
            _step(3, {"i": 2}),
            _step(4, {"i": 3}),
        ]
        reference_steps = [
            _step(10, {"index": 0}),
            _step(20, {"index": 1}),
            _step(30, {"index": 2}),
            _step(40, {"index": 3}),
        ]
        result = detect_first_divergence(
            student_steps=student_steps,
            reference_steps=reference_steps,
        )
        assert result.detected is False

    def test_real_pointer_state_divergence_is_detected(self):
        student_steps = [
            _step(1, {"pointer": 0}),
            _step(2, {"pointer": 2}),
            _step(3, {"pointer": 3}),
        ]
        reference_steps = [
            _step(10, {"pointer": 0}),
            _step(20, {"pointer": 2}),
            _step(30, {"pointer": 4}),
        ]
        result = detect_first_divergence(
            student_steps=student_steps,
            reference_steps=reference_steps,
        )
        assert result.detected is True
        assert result.line == 3
        assert result.reference_line == 30
        assert result.divergent_variable == "pointer"

    def test_branch_outcome_divergence_is_detected(self):
        student_steps = [
            {**_step(1, {"x": 2}), "event_type": "branch", "branch_outcome": False},
        ]
        reference_steps = [
            {**_step(10, {"value": 2}), "event_type": "branch", "branch_outcome": True},
        ]
        result = detect_first_divergence(
            student_steps=student_steps,
            reference_steps=reference_steps,
        )
        assert result.detected is True
        assert "分支结果" in result.explanation

    def test_source_context_infers_branch_path_divergence(self):
        student_code = """def solve(x):
    if x > 0:
        result = 1
    else:
        result = 2
    return result
"""
        reference_code = student_code.replace("x > 0", "x < 0")
        student_steps = [
            _step(2, {"x": 1}),
            _step(3, {"x": 1, "result": 1}),
            _step(6, {"x": 1, "result": 1}),
        ]
        reference_steps = [
            _step(2, {"value": 1}),
            _step(5, {"value": 1, "answer": 2}),
            _step(6, {"value": 1, "answer": 2}),
        ]

        result = detect_first_divergence(
            student_steps=student_steps,
            reference_steps=reference_steps,
            student_code=student_code,
            reference_code=reference_code,
        )

        assert result.detected is True
        assert result.line == 2
        assert result.reference_line == 2
        assert "分支结果" in result.explanation

    def test_source_condition_recovers_branch_when_body_steps_are_filtered(self):
        student_code = """def solve(x):
    if x > 0:
        result = 1
    else:
        result = 2
    return x
"""
        reference_code = student_code.replace("x > 0", "x < 0")
        compressed_steps = [
            _step(2, {"x": 1}),
            _step(6, {"x": 1}),
        ]

        result = detect_first_divergence(
            student_steps=compressed_steps,
            reference_steps=compressed_steps,
            student_code=student_code,
            reference_code=reference_code,
        )

        assert result.detected is True
        assert result.line == 2
        assert "分支结果" in result.explanation

    def test_source_context_infers_loop_exit_divergence(self):
        student_code = """def solve(i):
    while i < 1:
        i += 1
    return i
"""
        reference_code = """def solve(index):
    while index < 1:
        index += 1
    return index
"""
        student_steps = [
            _step(2, {"i": 0}),
            _step(3, {"i": 1}),
            _step(4, {"i": 1}),
        ]
        reference_steps = [
            _step(2, {"index": 1}),
            _step(4, {"index": 1}),
        ]

        result = detect_first_divergence(
            student_steps=student_steps,
            reference_steps=reference_steps,
            student_code=student_code,
            reference_code=reference_code,
        )

        assert result.detected is True
        assert result.line == 2
        assert "循环结果" in result.explanation

    def test_no_common_keys_skips_step(self):
        """无公共变量的步被跳过。"""
        student_steps = [
            {"line": 1, "vars": {"a": {"type": "int", "value": 1}}, "changed": ["a"]},
            {"line": 2, "vars": {"b": {"type": "int", "value": 2}}, "changed": ["b"]},
        ]
        reference_steps = [
            {"line": 1, "vars": {"x": {"type": "int", "value": 1}}, "changed": ["x"]},
            {"line": 2, "vars": {"y": {"type": "int", "value": 2}}, "changed": ["y"]},
        ]
        result = detect_first_divergence(
            student_steps=student_steps,
            reference_steps=reference_steps,
        )
        assert result.detected is False

    def test_empty_student_steps_returns_reason(self):
        result = detect_first_divergence(student_steps=[], reference_steps=[_step(1, {"a": 1})])
        assert result.detected is False
        assert result.reason != ""

    def test_empty_reference_steps_returns_reason(self):
        result = detect_first_divergence(student_steps=[_step(1, {"a": 1})], reference_steps=[])
        assert result.detected is False
        assert result.reason != ""

    def test_confidence_high_when_divergence_early(self):
        """偏离在前半段 → confidence=high。"""
        student_steps = [_step(1, {"v": 1}), _step(2, {"v": 2}), _step(3, {"v": 3}), _step(4, {"v": 4})]
        reference_steps = [_step(1, {"v": 9}), _step(2, {"v": 2}), _step(3, {"v": 3}), _step(4, {"v": 4})]
        result = detect_first_divergence(student_steps=student_steps, reference_steps=reference_steps)
        assert result.detected is True
        assert result.confidence == "high"

    def test_to_dict_roundtrip(self):
        result = FirstDivergenceResult(detected=True, step_index=3, divergent_variable="mid")
        d = result.to_dict()
        assert d["detected"] is True
        assert d["step_index"] == 3
        assert d["divergent_variable"] == "mid"


class TestSourceLineContext:
    def test_python_roles_and_nested_control_context_are_extracted(self):
        code = """def solve(values):
    total = 0
    for value in values:
        if value > 0:
            total += value
    return total
"""

        contexts = _build_source_line_context(code, "python")

        assert contexts[2].role == "assignment"
        assert contexts[3].role == "loop"
        assert contexts[4].role == "branch"
        assert contexts[5].role == "assignment"
        assert contexts[5].control_path == (
            "function",
            "loop:body",
            "branch:body",
        )
        assert contexts[6].role == "return"

    def test_invalid_python_source_falls_back_to_trace_only_alignment(self):
        steps = [_step(1, {"x": 1}), _step(2, {"x": 2})]
        result = detect_first_divergence(
            student_steps=steps,
            reference_steps=steps,
            student_code="def broken(:",
            reference_code="def broken(:",
        )
        assert result.detected is False


class TestFindReferenceSolution:
    def test_returns_latest_ac_submission_code(self, db_session: Session):
        user = User(username="testuser", hashed_password="x", role="student")
        db_session.add(user)
        db_session.flush()

        old_ac = OjSubmission(
            user_id=user.id,
            problem_slug="binary-search",
            language="python",
            code="def old_solution(): pass",
            verdict="AC",
            passed=5,
            total=5,
            created_at=datetime(2026, 1, 1),
        )
        new_ac = OjSubmission(
            user_id=user.id,
            problem_slug="binary-search",
            language="python",
            code="def new_solution(): pass",
            verdict="AC",
            passed=5,
            total=5,
            created_at=datetime(2026, 8, 1),
        )
        db_session.add_all([old_ac, new_ac])
        db_session.commit()

        ref = find_reference_solution(db_session, "binary-search", language="python")
        assert ref is not None
        assert "new_solution" in ref

    def test_returns_none_when_no_ac_submission(self, db_session: Session):
        ref = find_reference_solution(db_session, "nonexistent-slug")
        assert ref is None

    def test_ignores_wa_submissions(self, db_session: Session):
        user = User(username="testuser2", hashed_password="x", role="student")
        db_session.add(user)
        db_session.flush()

        wa = OjSubmission(
            user_id=user.id,
            problem_slug="some-problem",
            language="python",
            code="def wrong(): pass",
            verdict="WA",
            passed=3,
            total=5,
        )
        db_session.add(wa)
        db_session.commit()

        ref = find_reference_solution(db_session, "some-problem")
        assert ref is None

    def test_ignores_incomplete_ac_record(self, db_session: Session):
        user = User(username="incomplete_ac", hashed_password="x", role="student")
        db_session.add(user)
        db_session.flush()
        db_session.add(OjSubmission(
            user_id=user.id,
            problem_slug="unsafe-reference",
            language="python",
            code="def unverified(): pass",
            verdict="AC",
            passed=0,
            total=0,
        ))
        db_session.commit()
        assert find_reference_solution(db_session, "unsafe-reference") is None

    def test_selects_structurally_compatible_strategy_not_latest(self, db_session: Session):
        user = User(username="strategy_refs", hashed_password="x", role="student")
        db_session.add(user)
        db_session.flush()
        older_two_pointer = OjSubmission(
            user_id=user.id,
            problem_slug="strategy-problem",
            language="python",
            code="def solve(nums):\n    left, right = 0, len(nums)-1\n    while left < right:\n        left += 1\n    return left",
            verdict="AC",
            passed=10,
            total=10,
            created_at=datetime(2026, 1, 1),
        )
        latest_hash = OjSubmission(
            user_id=user.id,
            problem_slug="strategy-problem",
            language="python",
            code="def solve(nums):\n    seen = set()\n    for value in nums:\n        if value in seen:\n            return value\n        seen.add(value)",
            verdict="AC",
            passed=10,
            total=10,
            created_at=datetime(2026, 8, 1),
        )
        db_session.add_all([older_two_pointer, latest_hash])
        db_session.commit()
        student_code = "def attempt(values):\n    l, r = 0, len(values)-1\n    while l < r:\n        l += 1\n    return l"
        ref = find_reference_solution(
            db_session,
            "strategy-problem",
            student_code=student_code,
        )
        assert ref == older_two_pointer.code

    def test_clusters_strategies_and_returns_cluster_canonical(self, db_session: Session):
        user = User(username="clustered_refs", hashed_password="x", role="student")
        db_session.add(user)
        db_session.flush()
        newest_verbose = OjSubmission(
            user_id=user.id,
            problem_slug="cluster-problem",
            language="python",
            code=(
                "def answer(values):\n"
                "    lo = 0\n"
                "    hi = len(values) - 1\n"
                "    while lo < hi:\n"
                "        if values[lo] == values[hi]:\n"
                "            return lo\n"
                "        lo = lo + 1\n"
                "    return -1"
            ),
            verdict="AC",
            passed=12,
            total=12,
            runtime_ms_avg=25,
            created_at=datetime(2026, 8, 3),
        )
        canonical_two_pointer = OjSubmission(
            user_id=user.id,
            problem_slug="cluster-problem",
            language="python",
            code=(
                "def solve(nums):\n"
                "    left, right = 0, len(nums) - 1\n"
                "    while left < right:\n"
                "        if nums[left] == nums[right]:\n"
                "            return left\n"
                "        left += 1\n"
                "    return -1"
            ),
            verdict="AC",
            passed=12,
            total=12,
            runtime_ms_avg=10,
            created_at=datetime(2026, 8, 2),
        )
        older_renamed = OjSubmission(
            user_id=user.id,
            problem_slug="cluster-problem",
            language="python",
            code=(
                "def locate(items):\n"
                "    l, r = 0, len(items) - 1\n"
                "    while l < r:\n"
                "        if items[l] == items[r]:\n"
                "            return l\n"
                "        l += 1\n"
                "    return -1"
            ),
            verdict="AC",
            passed=12,
            total=12,
            runtime_ms_avg=15,
            created_at=datetime(2026, 8, 1),
        )
        hash_strategy = OjSubmission(
            user_id=user.id,
            problem_slug="cluster-problem",
            language="python",
            code=(
                "def solve(nums):\n"
                "    seen = {}\n"
                "    for index, value in enumerate(nums):\n"
                "        if value in seen:\n"
                "            return seen[value]\n"
                "        seen[value] = index\n"
                "    return -1"
            ),
            verdict="AC",
            passed=12,
            total=12,
            runtime_ms_avg=8,
            created_at=datetime(2026, 8, 4),
        )
        db_session.add_all([
            newest_verbose,
            canonical_two_pointer,
            older_renamed,
            hash_strategy,
        ])
        db_session.commit()

        selection = select_reference_solution(
            db_session,
            "cluster-problem",
            student_code=(
                "def attempt(data):\n"
                "    i, j = 0, len(data) - 1\n"
                "    while i < j:\n"
                "        if data[i] == data[j]:\n"
                "            return i\n"
                "        i += 1\n"
                "    return -1"
            ),
        )

        assert selection is not None
        assert selection.cluster_count == 2
        assert selection.cluster_size == 3
        assert selection.candidate_count == 4
        assert selection.code == canonical_two_pointer.code
        assert selection.compatibility is not None

        canonical = select_reference_solution(db_session, "cluster-problem")
        assert canonical is not None
        assert canonical.cluster_size == 3
        assert canonical.code == canonical_two_pointer.code
        assert find_reference_solution(db_session, "cluster-problem") == hash_strategy.code

    def test_duplicate_recent_rows_do_not_hide_older_strategy(self, db_session: Session):
        user = User(username="dedup_refs", hashed_password="x", role="student")
        db_session.add(user)
        db_session.flush()
        repeated_code = "def solve(nums):\n    return sorted(nums)"
        for day in range(1, 31):
            formatting = repeated_code if day % 2 else repeated_code + "  # same solution"
            db_session.add(OjSubmission(
                user_id=user.id,
                problem_slug="dedup-problem",
                language="python",
                code=formatting,
                verdict="AC",
                passed=5,
                total=5,
                created_at=datetime(2026, 8, day),
            ))
        older_loop = OjSubmission(
            user_id=user.id,
            problem_slug="dedup-problem",
            language="python",
            code=(
                "def solve(nums):\n"
                "    total = 0\n"
                "    for value in nums:\n"
                "        total += value\n"
                "    return total"
            ),
            verdict="AC",
            passed=5,
            total=5,
            created_at=datetime(2026, 7, 1),
        )
        db_session.add(older_loop)
        db_session.commit()

        selection = select_reference_solution(
            db_session,
            "dedup-problem",
            student_code=(
                "def attempt(values):\n"
                "    answer = 0\n"
                "    for item in values:\n"
                "        answer += item\n"
                "    return answer"
            ),
        )

        assert selection is not None
        assert selection.candidate_count == 2
        assert selection.code == older_loop.code


class TestRunFirstDivergenceAnalysis:
    def test_returns_null_when_no_ac_submission(self, db_session: Session):
        result = run_first_divergence_analysis(
            db_session,
            slug="no-ac-problem",
            student_code="x = 1",
            student_steps=[_step(1, {"x": 1})],
            language="python",
            run_reference_trace_fn=lambda code, slug, lang: [],
        )
        assert result.detected is False
        assert "insufficient_reference_trace" in result.reason

    def test_returns_null_when_student_equals_reference(self, db_session: Session):
        user = User(username="ref_user", hashed_password="x", role="student")
        db_session.add(user)
        db_session.flush()

        ac_code = "def solve(): return 42"
        ac = OjSubmission(
            user_id=user.id,
            problem_slug="eq-problem",
            language="python",
            code=ac_code,
            verdict="AC",
            passed=1,
            total=1,
        )
        db_session.add(ac)
        db_session.commit()

        result = run_first_divergence_analysis(
            db_session,
            slug="eq-problem",
            student_code=ac_code,
            student_steps=[_step(1, {"x": 1})],
            language="python",
            run_reference_trace_fn=lambda code, slug, lang: [_step(1, {"x": 1})],
        )
        assert result.detected is False
        assert "相同" in result.reason

    def test_returns_null_when_reference_trace_fails(self, db_session: Session):
        user = User(username="ref_user2", hashed_password="x", role="student")
        db_session.add(user)
        db_session.flush()

        ac = OjSubmission(
            user_id=user.id,
            problem_slug="fail-problem",
            language="python",
            code="def solve(): pass",
            verdict="AC",
            passed=1,
            total=1,
        )
        db_session.add(ac)
        db_session.commit()

        def failing_fn(code: str, slug: str, lang: str) -> list:
            raise RuntimeError("trace runner crashed")

        result = run_first_divergence_analysis(
            db_session,
            slug="fail-problem",
            student_code="def wrong(): pass",
            student_steps=[_step(1, {"x": 1})],
            language="python",
            run_reference_trace_fn=failing_fn,
        )
        assert result.detected is False
        assert "运行失败" in result.reason

    def test_returns_null_when_no_trace_fn_provided(self, db_session: Session):
        user = User(username="ref_user3", hashed_password="x", role="student")
        db_session.add(user)
        db_session.flush()

        ac = OjSubmission(
            user_id=user.id,
            problem_slug="no-fn-problem",
            language="python",
            code="def solve(): pass",
            verdict="AC",
            passed=1,
            total=1,
        )
        db_session.add(ac)
        db_session.commit()

        result = run_first_divergence_analysis(
            db_session,
            slug="no-fn-problem",
            student_code="def wrong(): pass",
            student_steps=[_step(1, {"x": 1})],
            language="python",
            run_reference_trace_fn=None,
        )
        assert result.detected is False
        assert "未提供" in result.reason

    def test_full_pipeline_detects_divergence(self, db_session: Session):
        """完整流程：有 AC 提交 → 运行参考解 → 比较发现偏离。"""
        user = User(username="ref_user4", hashed_password="x", role="student")
        db_session.add(user)
        db_session.flush()

        ac = OjSubmission(
            user_id=user.id,
            problem_slug="full-pipeline",
            language="python",
            code="def correct_binary_search(): pass",
            verdict="AC",
            passed=5,
            total=5,
        )
        db_session.add(ac)
        db_session.commit()

        student_steps = [
            _step(1, {"lo": 0, "hi": 6}),
            _step(2, {"lo": 0, "hi": 6, "mid": 3}),
            _step(3, {"lo": 3, "hi": 6, "mid": 3}),
        ]
        reference_steps = [
            _step(1, {"lo": 0, "hi": 6}),
            _step(2, {"lo": 0, "hi": 6, "mid": 3}),
            _step(3, {"lo": 0, "hi": 2, "mid": 1}),
        ]

        def run_ref(code: str, slug: str, lang: str) -> list[dict]:
            return reference_steps

        result = run_first_divergence_analysis(
            db_session,
            slug="full-pipeline",
            student_code="def buggy_binary_search(): pass",
            student_steps=student_steps,
            language="python",
            run_reference_trace_fn=run_ref,
        )
        assert result.detected is True
        assert result.step_index == 2
        assert result.divergent_variable in ("lo", "mid", "hi")
        assert "ac_submission" in result.reference_source
