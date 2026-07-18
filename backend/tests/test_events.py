"""Learning EventBus 测试。"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.database import SessionLocal
from main import app
from models.db_models import LearningEventLog, OjSubmission, User
from api.oj import _count_consecutive_failures
from services.events.event_bus import EventBus, event_bus
from services.events.handlers import register_handlers
from utils.security import hash_password


@pytest.fixture
def db() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(db: Session) -> User:
    name = f"evt_{uuid.uuid4().hex[:10]}"
    user = User(username=name, email=f"{name}@example.com", hashed_password=hash_password("pass"))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_publish_invokes_handlers(db: Session, test_user: User):
    event_bus.clear()
    register_handlers(event_bus)
    pub = event_bus.publish(
        db,
        event_type="on_oj_submission_failed",
        user_id=test_user.id,
        payload={
            "problem_slug": "two-sum",
            "verdict": "WA",
            "message": "边界条件错误",
            "error_pattern": "边界条件错误",
        },
    )
    assert pub.ok
    assert "OjFailurePipeline" in pub.event.handled_by
    assert any(log.agent == "StudentMemory" for log in pub.event.agent_logs)
    assert any(log.agent == "MasteryAgent" for log in pub.event.agent_logs)


def test_handler_error_does_not_break_publish(db: Session, test_user: User):
    bus = EventBus()
    register_handlers(bus)

    def boom(_db, event):
        raise RuntimeError("handler exploded")

    bus.subscribe("on_quiz_completed", "BoomHandler", boom)
    pub = bus.publish(
        db,
        event_type="on_quiz_completed",
        user_id=test_user.id,
        payload={"mastery_delta": 1},
    )
    assert pub.event.status in ("partial", "failed")
    assert any("BoomHandler" in err for err in pub.event.handler_errors)
    assert pub.event.event_id
    assert pub.persisted is True
    assert db.get(LearningEventLog, pub.event.event_id) is not None


def test_publish_reports_event_store_failure(db: Session, test_user: User, monkeypatch: pytest.MonkeyPatch):
    bus = EventBus()

    def fail_persist(_db, _event):
        raise RuntimeError("event store unavailable")

    monkeypatch.setattr(bus, "_persist", fail_persist)
    pub = bus.publish(
        db,
        event_type="on_quiz_completed",
        user_id=test_user.id,
    )
    assert pub.ok is False
    assert pub.persisted is False


def test_consecutive_failures_are_not_truncated(db: Session, test_user: User):
    slug = f"long-streak-{uuid.uuid4().hex}"
    db.add_all(
        [
            OjSubmission(
                user_id=test_user.id,
                problem_slug=slug,
                verdict="WA",
                cases=[],
            )
            for _ in range(25)
        ]
    )
    db.commit()
    assert _count_consecutive_failures(db, test_user.id, slug) == 26


def test_event_log_queryable_via_api(db: Session, test_user: User):
    event_bus.clear()
    register_handlers(event_bus)
    pub = event_bus.publish(
        db,
        event_type="on_resource_generated",
        user_id=test_user.id,
        payload={
            "resource_type": "document",
            "title": "测试教案",
            "verified": True,
            "safety_passed": True,
            "agent_logs": [
                {"agent": "ContentVerifierAgent", "action": "verify_pass", "detail": "ok"},
            ],
        },
    )
    client = TestClient(app)
    token = None
    reg = client.post(
        "/api/auth/register",
        json={
            "username": f"evtapi_{uuid.uuid4().hex[:6]}",
            "password": "secret123",
            "email": f"e{uuid.uuid4().hex[:6]}@example.com",
        },
    )
    if reg.status_code == 200:
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        listed = client.get("/api/events/recent", headers=headers)
        assert listed.status_code == 200

    got = event_bus.get(pub.event.event_id)
    assert got is not None
    assert got.event_type == "on_resource_generated"


def test_oj_failed_chains_memory_mastery_skill(db: Session, test_user: User):
    event_bus.clear()
    register_handlers(event_bus)
    pub = event_bus.publish(
        db,
        event_type="on_oj_submission_failed",
        user_id=test_user.id,
        payload={
            "problem_slug": "climbing-stairs",
            "verdict": "WA",
            "message": "初始化错误 dp 边界",
            "error_pattern": "初始化错误",
            "module_key": "dp",
        },
    )
    agents = {log.agent for log in pub.event.agent_logs}
    assert "StudentMemory" in agents
    assert "MasteryAgent" in agents
    assert "SkillRouter" in agents or "recommended_skill_cards" in pub.event.payload
    assert pub.event.payload.get("mastery_score") is not None
