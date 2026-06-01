"""学习效果统计与导出 — analytics/effectiveness 测试。"""

from __future__ import annotations

import csv
import io
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.database import SessionLocal
from main import app
from models.db_models import User
from services.analytics.effectiveness import (
    EffectivenessResponse,
    build_csv_rows,
    compute_effectiveness,
)
from services.memory.memory_service import MemoryService
from services.memory.schemas import MemoryEventInput
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
    name = f"eff_{uuid.uuid4().hex[:10]}"
    user = User(username=name, email=f"{name}@example.com", hashed_password=hash_password("pass"))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_empty_user_returns_partial(db: Session, test_user: User):
    result = compute_effectiveness(db, test_user.id)
    assert isinstance(result, EffectivenessResponse)
    assert result.partial is True
    assert len(result.rows) == 0
    assert "student_memory" in result.missing_fields


def test_oj_failure_and_resource_complete_produces_delta(db: Session, test_user: User):
    svc = MemoryService(db)
    for i in range(3):
        svc.record_event(
            test_user.id,
            MemoryEventInput(
                event_type="oj_submit_fail",
                chapter_id="ch11-dynamic-programming",
                skill_id="dp-state-design",
                problem_slug=f"dp-prob-{i}",
                observed_error_pattern="初始化错误 dp 边界",
                mastery_delta=-1,
                evidence_json={"verdict": "WA"},
            ),
        )
    svc.record_event(
        test_user.id,
        MemoryEventInput(
            event_type="resource_complete",
            chapter_id="ch11-dynamic-programming",
            skill_id="dp-state-design",
            successful_hint="递归基线条件要写清",
            mastery_delta=2,
            evidence_json={"correct": True},
        ),
    )
    result = compute_effectiveness(db, test_user.id, chapter_id="ch11-dynamic-programming")
    assert len(result.rows) >= 1
    row = result.rows[0]
    assert row.oj_attempts == 3
    assert row.oj_failures == 3
    assert row.resource_completion_count == 1
    assert row.mastery_delta != 0
    assert row.latest_error_pattern != ""


def test_csv_format_correct(db: Session, test_user: User):
    svc = MemoryService(db)
    svc.record_event(
        test_user.id,
        MemoryEventInput(
            event_type="oj_submit_fail",
            chapter_id="ch02-linear-list",
            skill_id="linear-list-operation",
            problem_slug="linked-list-reverse",
            observed_error_pattern="指针移动错误",
            mastery_delta=-1,
        ),
    )
    svc.record_event(
        test_user.id,
        MemoryEventInput(
            event_type="resource_complete",
            chapter_id="ch02-linear-list",
            skill_id="linear-list-operation",
            mastery_delta=1,
        ),
    )
    result = compute_effectiveness(db, test_user.id)
    csv_rows = build_csv_rows(result)
    assert len(csv_rows) >= 2
    assert csv_rows[0][0] == "user_id"
    assert csv_rows[1][0] == str(test_user.id)

    buf = io.StringIO()
    writer = csv.writer(buf)
    for row in csv_rows:
        writer.writerow(row)
    buf.seek(0)
    reader = csv.reader(buf)
    parsed = list(reader)
    assert len(parsed) >= 2
    assert parsed[0][0] == "user_id"


def test_csv_no_sensitive_data(db: Session, test_user: User):
    svc = MemoryService(db)
    svc.record_event(
        test_user.id,
        MemoryEventInput(
            event_type="resource_complete",
            chapter_id="ch05-tree-binary-tree",
            mastery_delta=1,
        ),
    )
    result = compute_effectiveness(db, test_user.id)
    csv_rows = build_csv_rows(result)
    header = csv_rows[0]
    for col in header:
        assert col not in ("username", "email", "hashed_password")


def test_api_effectiveness_endpoint():
    client = TestClient(app)
    uname = f"effapi_{uuid.uuid4().hex[:8]}"
    reg = client.post(
        "/api/auth/register",
        json={"username": uname, "password": "secret123", "email": f"{uname}@example.com"},
    )
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/analytics/effectiveness", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "rows" in body
    assert "partial" in body
    assert "missing_fields" in body


def test_api_csv_export():
    client = TestClient(app)
    uname = f"effcsv_{uuid.uuid4().hex[:8]}"
    reg = client.post(
        "/api/auth/register",
        json={"username": uname, "password": "secret123", "email": f"{uname}@example.com"},
    )
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/analytics/effectiveness/export.csv", headers=headers)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")
    content = resp.text
    assert "user_id" in content
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    assert len(rows) >= 1


def test_trace_diagnosis_counted(db: Session, test_user: User):
    svc = MemoryService(db)
    svc.record_event(
        test_user.id,
        MemoryEventInput(
            event_type="oj_diagnosis",
            chapter_id="ch05-tree-binary-tree",
            skill_id="tree-traversal",
            successful_hint="检查递归终止条件",
            mastery_delta=0,
        ),
    )
    svc.record_event(
        test_user.id,
        MemoryEventInput(
            event_type="trace_diagnosis",
            chapter_id="ch05-tree-binary-tree",
            skill_id="tree-traversal",
            mastery_delta=0,
        ),
    )
    result = compute_effectiveness(db, test_user.id, chapter_id="ch05-tree-binary-tree")
    assert len(result.rows) >= 1
    row = result.rows[0]
    assert row.trace_diagnosis_count == 2
    assert row.hint_count == 1


def test_improvement_summary_not_empty(db: Session, test_user: User):
    svc = MemoryService(db)
    svc.record_event(
        test_user.id,
        MemoryEventInput(
            event_type="oj_submit_fail",
            chapter_id="ch06-graph",
            skill_id="graph-bfs-dfs",
            observed_error_pattern="BFS 队列未去重",
            mastery_delta=-1,
        ),
    )
    svc.record_event(
        test_user.id,
        MemoryEventInput(
            event_type="resource_complete",
            chapter_id="ch06-graph",
            skill_id="graph-bfs-dfs",
            mastery_delta=2,
        ),
    )
    result = compute_effectiveness(db, test_user.id)
    assert len(result.rows) >= 1
    assert result.rows[0].improvement_summary != ""
    assert "掌握度" in result.rows[0].improvement_summary or "OJ" in result.rows[0].improvement_summary
