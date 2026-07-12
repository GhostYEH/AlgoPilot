from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base, get_db
from main import app
from services.events.event_bus import event_bus


@pytest.fixture
def isolated_db() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(isolated_db: Session) -> Generator[TestClient, None, None]:
    def override_db() -> Generator[Session, None, None]:
        yield isolated_db

    app.dependency_overrides[get_db] = override_db
    event_bus.clear()
    try:
        yield TestClient(app)
    finally:
        event_bus.clear()
        app.dependency_overrides.clear()


def _register(client: TestClient, username: str, **extra) -> tuple[dict, dict[str, str]]:
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "secret123",
            "email": f"{username}@example.com",
            **extra,
        },
    )
    assert response.status_code == 200
    body = response.json()
    return body, {"Authorization": f"Bearer {body['access_token']}"}


def test_progress_memory_and_events_are_isolated_by_account(
    client: TestClient,
    isolated_db: Session,
) -> None:
    user_a, headers_a = _register(client, "isolation_a")
    _user_b, headers_b = _register(client, "isolation_b")

    saved = client.put(
        "/api/me/learning-progress",
        headers=headers_a,
        json={"payload": {"alp-array-section-done-v1": {"theory": True}}},
    )
    assert saved.status_code == 200
    assert client.get("/api/me/learning-progress", headers=headers_b).json()["payload"] == {}

    patched = client.post(
        "/api/orchestrator/persona/patch-from-learning",
        headers=headers_a,
        json={
            "weak_module_keys": [],
            "signals": [
                {
                    "event_type": "section_done",
                    "module_key": "array",
                    "detail": "theory",
                }
            ],
        },
    )
    assert patched.status_code == 200

    recent_a = client.get("/api/memory/recent", headers=headers_a).json()["items"]
    recent_b = client.get("/api/memory/recent", headers=headers_b).json()["items"]
    assert any(item["event_type"] == "section_done" for item in recent_a)
    assert recent_b == []

    published = event_bus.publish(
        isolated_db,
        event_type="on_profile_updated",
        user_id=user_a["user"]["id"],
        payload={"message": "profile updated"},
    )
    event_id = published.event.event_id
    event_bus.clear()

    persisted = client.get(f"/api/events/{event_id}", headers=headers_a)
    assert persisted.status_code == 200
    assert persisted.json()["event_id"] == event_id
    assert client.get(f"/api/events/{event_id}", headers=headers_b).status_code == 404


def test_registration_role_selection_creates_teacher_and_student_accounts(
    client: TestClient,
) -> None:
    teacher_body, teacher_headers = _register(client, "role_teacher", role="teacher")
    assert teacher_body["user"]["role"] == "teacher"

    student_body, student_headers = _register(client, "role_student", role="student")
    assert student_body["user"]["role"] == "student"

    # 教师账号可以访问教师看板
    allowed = client.get("/api/teacher/dashboard-summary", headers=teacher_headers)
    assert allowed.status_code == 200

    # 学生账号无权访问教师看板
    denied = client.get("/api/teacher/dashboard-summary", headers=student_headers)
    assert denied.status_code == 403
