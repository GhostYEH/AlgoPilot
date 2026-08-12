"""执行轨迹大小限制测试。

验证：
1. 超长 trace 被截断到 max_steps
2. total_steps 记数仍记录原始长度
3. 数据库不过度膨胀
4. 响应不无限增长
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from models.db_models import Base, OjSubmission, User
from services.evidence.persistence import (
    _MAX_TRACE_STEPS_PERSIST,
    persist_execution_trace,
)


@pytest.fixture
def db_session() -> Session:
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, future=True)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def submission_id(db_session: Session) -> int:
    user = User(username="trace_test_user", hashed_password="x", role="student")
    db_session.add(user)
    db_session.flush()
    sub = OjSubmission(
        user_id=user.id,
        problem_slug="test",
        language="python",
        code="x=1",
        verdict="WA",
        passed=0,
        total=1,
    )
    db_session.add(sub)
    db_session.commit()
    return sub.id


class TestTraceSizeLimits:
    def test_max_steps_constant_is_reasonable(self):
        assert _MAX_TRACE_STEPS_PERSIST == 500
        assert _MAX_TRACE_STEPS_PERSIST > 0

    def test_trace_under_limit_not_truncated(self, db_session: Session, submission_id: int):
        steps = [{"line": i, "vars": {}, "changed": []} for i in range(100)]
        record = persist_execution_trace(
            db_session,
            submission_id=submission_id,
            steps=steps,
        )
        assert record is not None
        assert len(record.steps) == 100
        assert record.total_steps == 100

    def test_trace_over_limit_truncated(self, db_session: Session, submission_id: int):
        steps = [{"line": i, "vars": {}, "changed": []} for i in range(1000)]
        record = persist_execution_trace(
            db_session,
            submission_id=submission_id,
            steps=steps,
        )
        assert record is not None
        assert len(record.steps) == _MAX_TRACE_STEPS_PERSIST
        assert record.total_steps == 1000

    def test_empty_trace_handled(self, db_session: Session, submission_id: int):
        record = persist_execution_trace(
            db_session,
            submission_id=submission_id,
            steps=[],
        )
        assert record is not None
        assert record.total_steps == 0
        assert record.steps == []

    def test_large_payload_does_not_crash(self, db_session: Session, submission_id: int):
        """大 payload 不导致 OOM 或异常。"""
        steps = [
            {"line": i, "vars": {f"var_{j}": {"type": "int", "value": j} for j in range(50)}, "changed": []}
            for i in range(2000)
        ]
        record = persist_execution_trace(
            db_session,
            submission_id=submission_id,
            steps=steps,
        )
        assert record is not None
        assert len(record.steps) == _MAX_TRACE_STEPS_PERSIST

    def test_db_size_bounded(self, db_session: Session, submission_id: int):
        """多次持久化大 trace 不导致数据库过度膨胀。"""
        for _ in range(10):
            steps = [{"line": i, "vars": {}, "changed": []} for i in range(1000)]
            persist_execution_trace(
                db_session,
                submission_id=submission_id,
                steps=steps,
            )

        from models.db_models import ExecutionTraceRecord

        all_records = db_session.query(ExecutionTraceRecord).all()
        for rec in all_records:
            assert len(rec.steps) <= _MAX_TRACE_STEPS_PERSIST