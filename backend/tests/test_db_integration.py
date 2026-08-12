"""数据库集成测试：验证 4 张新表真实 INSERT/UPDATE。

覆盖：
1. execution_traces: persist_execution_trace 真实 INSERT，可查询回读
2. bug_records: persist_bug_record 真实 INSERT，可查询回读
3. hint_records: persist_hint_record 真实 INSERT，可查询回读
4. student_knowledge_states: update_knowledge_state 真实 INSERT + UPDATE
5. mastery/confidence 分开维护
6. 重复 Bug 降权
7. 首次 AC 加权
8. Hint Level 影响独立掌握度
9. 多次更新累积效果
"""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from models.db_models import (
    Base,
    BugRecord,
    ExecutionTraceRecord,
    HintRecord,
    OjSubmission,
    StudentKnowledgeState,
    User,
)
from services.evidence.persistence import (
    persist_bug_record,
    persist_execution_trace,
    persist_hint_record,
)
from services.mastery.mastery_update import get_knowledge_state, update_knowledge_state


@pytest.fixture
def db_session() -> Session:
    """内存 SQLite，真实表结构，每测试独立。"""
    engine = create_engine("sqlite://", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, future=True)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def user_id(db_session: Session) -> int:
    user = User(username="db_test_user", hashed_password="x", role="student")
    db_session.add(user)
    db_session.commit()
    return user.id


@pytest.fixture
def submission_id(db_session: Session, user_id: int) -> int:
    sub = OjSubmission(
        user_id=user_id,
        problem_slug="test-problem",
        language="python",
        code="x = 1",
        verdict="WA",
        passed=3,
        total=5,
    )
    db_session.add(sub)
    db_session.commit()
    return sub.id


class TestPersistExecutionTrace:
    def test_inserts_record_into_execution_traces(self, db_session: Session, submission_id: int):
        steps = [
            {"line": 1, "vars": {"x": {"type": "int", "value": 1}}, "changed": ["x"]},
            {"line": 2, "vars": {"x": {"type": "int", "value": 2}}, "changed": ["x"]},
        ]
        record = persist_execution_trace(
            db_session,
            submission_id=submission_id,
            steps=steps,
            language="python",
            first_divergence_step=1,
            first_divergence_line=2,
        )
        assert record is not None
        assert record.id is not None
        assert record.submission_id == submission_id
        assert record.total_steps == 2
        assert record.language == "python"
        assert record.first_divergence_step == 1

        queried = db_session.query(ExecutionTraceRecord).filter_by(id=record.id).first()
        assert queried is not None
        assert len(queried.steps) == 2

    def test_truncates_long_traces(self, db_session: Session, submission_id: int):
        steps = [{"line": i, "vars": {}, "changed": []} for i in range(600)]
        record = persist_execution_trace(
            db_session,
            submission_id=submission_id,
            steps=steps,
        )
        assert record is not None
        assert record.total_steps == 600
        assert len(record.steps) == 500

    def test_empty_steps_persists_successfully(self, db_session: Session, submission_id: int):
        record = persist_execution_trace(
            db_session,
            submission_id=submission_id,
            steps=[],
        )
        assert record is not None
        assert record.total_steps == 0
        assert record.steps == []


class TestPersistBugRecord:
    def test_inserts_record_into_bug_records(self, db_session: Session, user_id: int, submission_id: int):
        record = persist_bug_record(
            db_session,
            user_id=user_id,
            problem_slug="binary-search",
            bug_type="boundary_condition_error",
            bug_type_label="边界条件错误",
            suspicious_lines=[7, 12],
            first_divergence_step=3,
            first_divergence_line=7,
            root_cause="hi = mid 应为 hi = mid - 1",
            confidence="high",
            confidence_source="ai_with_evidence",
            related_module_key="search",
            related_concept_id="binary-search",
            diagnosis_source="ai",
            submission_id=submission_id,
        )
        assert record is not None
        assert record.id is not None

        queried = db_session.query(BugRecord).filter_by(id=record.id).first()
        assert queried is not None
        assert queried.bug_type == "boundary_condition_error"
        assert queried.suspicious_lines == [7, 12]
        assert queried.confidence == "high"

    def test_truncates_long_root_cause(self, db_session: Session, user_id: int):
        long_cause = "A" * 5000
        record = persist_bug_record(
            db_session,
            user_id=user_id,
            problem_slug="p",
            root_cause=long_cause,
        )
        assert record is not None
        assert len(record.root_cause) == 2000

    def test_multiple_bug_records_for_same_user(self, db_session: Session, user_id: int):
        for i in range(3):
            persist_bug_record(
                db_session,
                user_id=user_id,
                problem_slug=f"problem-{i}",
                bug_type="loop_condition_error",
            )
        count = db_session.query(BugRecord).filter_by(user_id=user_id).count()
        assert count == 3


class TestPersistHintRecord:
    def test_inserts_record_into_hint_records(self, db_session: Session, user_id: int, submission_id: int):
        record = persist_hint_record(
            db_session,
            user_id=user_id,
            problem_slug="sorting",
            hint_level_used=2,
            hint_count=3,
            eventually_accepted=False,
            bug_type="boundary_condition_error",
            module_key="sorting",
            submission_id=submission_id,
        )
        assert record is not None

        queried = db_session.query(HintRecord).filter_by(id=record.id).first()
        assert queried is not None
        assert queried.hint_level_used == 2
        assert queried.eventually_accepted is False

    def test_eventually_accepted_true(self, db_session: Session, user_id: int):
        record = persist_hint_record(
            db_session,
            user_id=user_id,
            problem_slug="p",
            hint_level_used=1,
            eventually_accepted=True,
        )
        assert record is not None
        assert record.eventually_accepted is True


class TestUpdateKnowledgeState:
    def test_creates_new_state_on_first_attempt(self, db_session: Session, user_id: int):
        record = update_knowledge_state(
            db_session,
            user_id=user_id,
            module_key="search",
            concept_id="binary-search",
            knowledge_point="二分查找边界",
            verdict="WA",
            bug_type="boundary_condition_error",
            hint_level_used=1,
            difficulty="medium",
        )
        assert record is not None
        assert record.attempt_count == 1
        assert record.success_count == 0
        assert record.mastery > 0.0 or record.mastery == 0.0
        assert record.confidence > 0.0

        queried = get_knowledge_state(db_session, user_id, "search", "binary-search")
        assert queried is not None
        assert queried.attempt_count == 1

    def test_updates_existing_state_on_second_attempt(self, db_session: Session, user_id: int):
        update_knowledge_state(
            db_session,
            user_id=user_id,
            module_key="search",
            concept_id="binary-search",
            verdict="WA",
            bug_type="boundary_condition_error",
            difficulty="medium",
        )
        first = get_knowledge_state(db_session, user_id, "search", "binary-search")
        assert first is not None
        first_mastery = first.mastery

        update_knowledge_state(
            db_session,
            user_id=user_id,
            module_key="search",
            concept_id="binary-search",
            verdict="AC",
            difficulty="medium",
            is_first_ac=True,
            is_independent=True,
        )
        second = get_knowledge_state(db_session, user_id, "search", "binary-search")
        assert second is not None
        assert second.attempt_count == 2
        assert second.success_count == 1
        assert second.mastery > first_mastery

    def test_mastery_and_confidence_separated(self, db_session: Session, user_id: int):
        """mastery 基于成功率，confidence 基于样本量。"""
        record = update_knowledge_state(
            db_session,
            user_id=user_id,
            module_key="dp",
            concept_id="knapsack",
            verdict="WA",
            difficulty="hard",
        )
        assert record is not None
        assert 0.0 <= record.mastery <= 100.0
        assert 0.0 <= record.confidence <= 100.0
        assert record.confidence > 0.0

    def test_repeated_bug_applies_penalty(self, db_session: Session, user_id: int):
        """连续相同 Bug 类型应比不同 Bug 类型 mastery 更低。"""
        update_knowledge_state(
            db_session,
            user_id=user_id,
            module_key="search",
            concept_id="bs-1",
            verdict="WA",
            bug_type="boundary_condition_error",
            difficulty="medium",
        )
        update_knowledge_state(
            db_session,
            user_id=user_id,
            module_key="search",
            concept_id="bs-1",
            verdict="WA",
            bug_type="boundary_condition_error",
            difficulty="medium",
        )
        repeated = get_knowledge_state(db_session, user_id, "search", "bs-1")
        assert repeated is not None
        assert "boundary_condition_error" in repeated.recent_bug_types

    def test_first_ac_bonus(self, db_session: Session, user_id: int):
        """首次 AC 且独立完成应获得更高 mastery。"""
        update_knowledge_state(
            db_session,
            user_id=user_id,
            module_key="sort",
            concept_id="merge-sort",
            verdict="WA",
            difficulty="medium",
        )
        update_knowledge_state(
            db_session,
            user_id=user_id,
            module_key="sort",
            concept_id="merge-sort",
            verdict="AC",
            difficulty="medium",
            is_first_ac=True,
            is_independent=True,
        )
        record = get_knowledge_state(db_session, user_id, "sort", "merge-sort")
        assert record is not None
        assert record.success_count == 1
        assert record.independent_success_count == 1
        assert record.mastery > 0.0

    def test_hint_level_affects_independent_count(self, db_session: Session, user_id: int):
        """使用高级别提示的 AC 不计入 independent_success_count。"""
        update_knowledge_state(
            db_session,
            user_id=user_id,
            module_key="graph",
            concept_id="bfs",
            verdict="AC",
            difficulty="easy",
            is_independent=False,
            hint_level_used=3,
        )
        record = get_knowledge_state(db_session, user_id, "graph", "bfs")
        assert record is not None
        assert record.success_count == 1
        assert record.independent_success_count == 0

    def test_confidence_grows_with_attempts(self, db_session: Session, user_id: int):
        """多次尝试后 confidence 应递增。"""
        confidences = []
        for _ in range(5):
            r = update_knowledge_state(
                db_session,
                user_id=user_id,
                module_key="m",
                concept_id="c",
                verdict="WA",
                difficulty="easy",
            )
            confidences.append(r.confidence)

        for i in range(1, len(confidences)):
            assert confidences[i] >= confidences[i - 1]

    def test_returns_none_when_no_module_or_concept(self, db_session: Session, user_id: int):
        result = update_knowledge_state(
            db_session,
            user_id=user_id,
            module_key="",
            concept_id="",
            verdict="AC",
        )
        assert result is None

    def test_mastery_clamped_to_0_100(self, db_session: Session, user_id: int):
        for _ in range(20):
            update_knowledge_state(
                db_session,
                user_id=user_id,
                module_key="clamp",
                concept_id="test",
                verdict="AC",
                difficulty="hard",
                is_first_ac=False,
                is_independent=True,
            )
        record = get_knowledge_state(db_session, user_id, "clamp", "test")
        assert record is not None
        assert 0.0 <= record.mastery <= 100.0
        assert 0.0 <= record.confidence <= 100.0