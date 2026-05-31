"""StudentLearningMemory 写入、摘要与画像证据链测试。"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.database import SessionLocal
from main import app
from models.db_models import StudentProfile, User
from services.memory.memory_service import (
    MemoryService,
    record_oj_diagnosis,
    record_oj_submit_failure,
)
from services.memory.memory_summarizer import get_summary_payload
from services.memory.schemas import MemoryEventInput
from services.orchestrator.core import _profile_to_response
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
    name = f"mem_{uuid.uuid4().hex[:10]}"
    user = User(username=name, email=f"{name}@test.local", hashed_password=hash_password("pass"))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_record_event_and_summary(db: Session, test_user: User):
    svc = MemoryService(db)
    event = svc.record_event(
        test_user.id,
        MemoryEventInput(
            event_type="quiz_complete",
            chapter_id="ch02-linear-list",
            skill_id="linked-list-pointer",
            observed_error_pattern="头插法指针丢失",
            trace_summary="第 3 步 next 未更新",
            mastery_delta=-1,
            evidence_json={"persona_dimension": "error_preference"},
        ),
    )
    assert event.id > 0
    assert event.event_type == "quiz_complete"

    payload = get_summary_payload(db, test_user.id, limit=5)
    assert payload["recent_count"] >= 1
    assert "learning_memory_summary" in payload
    assert len(payload.get("weak_patterns") or []) >= 0
    assert "error_preference" in (payload.get("dimension_evidence") or {})


def test_oj_diagnosis_writes_memory(db: Session, test_user: User):
    row = record_oj_diagnosis(
        db,
        test_user.id,
        problem_slug="two-sum",
        diagnosis={
            "bug_step_index": 2,
            "diagnosis_title": "边界未处理空数组",
            "detailed_analysis": "边界条件：输入为空时未提前返回",
            "source": "trace_diagnosis",
        },
        edge_category="edge",
    )
    assert row.event_type == "oj_diagnosis"
    assert "边界" in row.observed_error_pattern
    assert row.evidence_json.get("bug_step_index") == 2
    assert row.trace_summary.startswith("Step 2")


def test_oj_submit_failure_pattern(db: Session, test_user: User):
    row = record_oj_submit_failure(
        db,
        test_user.id,
        problem_slug="reverse-linked-list",
        verdict="TLE",
        message="Time Limit Exceeded",
    )
    assert row is not None
    assert "TLE" in row.observed_error_pattern or "超时" in row.observed_error_pattern


def test_profile_response_includes_evidence(db: Session, test_user: User):
    record_oj_submit_failure(
        db,
        test_user.id,
        problem_slug="valid-palindrome",
        verdict="WA",
        message="边界条件错误",
    )
    profile = StudentProfile(user_id=test_user.id, summary="测试画像", dimensions={})
    db.add(profile)
    db.commit()

    resp = _profile_to_response(profile, db=db, user_id=test_user.id)
    assert isinstance(resp.dimension_evidence, dict)
    assert resp.update_reason or resp.recent_evidence
    assert len(resp.recent_evidence) <= 3


def test_memory_api_write_and_summary():
    client = TestClient(app)
    uname = f"memuser_{uuid.uuid4().hex[:8]}"
    reg = client.post(
        "/api/auth/register",
        json={"username": uname, "password": "secret123", "email": f"{uname}@example.com"},
    )
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/api/memory/events",
        headers=headers,
        json={
            "event_type": "resource_complete",
            "chapter_id": "ch05-tree-binary-tree",
            "skill_id": "tree-traversal",
            "observed_error_pattern": "中序遍历递归栈溢出",
            "successful_hint": "改用迭代+显式栈",
            "mastery_delta": 1,
        },
    )
    assert created.status_code == 200
    assert created.json()["event"]["event_type"] == "resource_complete"

    summary = client.get("/api/memory/summary", headers=headers)
    assert summary.status_code == 200
    body = summary.json()
    assert body["recent_count"] >= 1
    assert body["learning_memory_summary"]

    persona = client.get("/api/orchestrator/persona/profile", headers=headers)
    assert persona.status_code == 200
    pdata = persona.json()
    assert "dimension_evidence" in pdata
    assert "update_reason" in pdata
    assert "recent_evidence" in pdata
