"""First Divergence 首次状态偏离检测单元测试。

覆盖场景：
1. 学生与参考解在同一变量首次偏离 → detected=True
2. 学生与参考解完全一致 → detected=False
3. 步数不同但公共步一致 → detected=True (循环次数差异)
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
    _extract_var_value,
    _find_common_keys,
    _format_state,
    _values_equal,
    _vars_at_step,
    detect_first_divergence,
    find_reference_solution,
    run_first_divergence_analysis,
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

    def test_step_count_difference_detected(self):
        """学生多循环一次，公共步一致但步数不同。"""
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
        assert "循环次数" in result.explanation

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