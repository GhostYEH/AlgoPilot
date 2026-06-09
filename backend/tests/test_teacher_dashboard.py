from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from api.deps import get_current_user
from core.database import Base, get_db
from main import app
from models.db_models import GeneratedResource, StudentLearningMemory, StudentProfile, User


@pytest.fixture
def dashboard_db() -> Generator[Session, None, None]:
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


def _request_summary(db: Session, current_user: User) -> dict:
    def override_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: current_user
    try:
        response = TestClient(app).get("/api/teacher/dashboard-summary")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    return response.json()


def test_dashboard_summary_uses_demo_fallback_without_class_data(
    dashboard_db: Session,
) -> None:
    teacher = User(
        username="teacher_demo",
        hashed_password="not-used",
        role="teacher",
    )
    dashboard_db.add(teacher)
    dashboard_db.commit()

    data = _request_summary(dashboard_db, teacher)

    assert data["is_demo"] is True
    assert data["overview"]["student_count"] > 0
    assert len(data["teaching_suggestions"]) == 3
    assert len(data["reinforcement_packs"]) == 3
    assert {item["label"] for item in data["error_types"]} == {
        "边界条件错误",
        "指针更新错误",
        "复杂度过高",
        "空栈/空指针",
    }


def test_dashboard_summary_aggregates_existing_learning_records(
    dashboard_db: Session,
) -> None:
    teacher = User(username="teacher_real", hashed_password="not-used", role="teacher")
    student_a = User(username="student_a", hashed_password="not-used", role="student")
    student_b = User(username="student_b", hashed_password="not-used", role="student")
    dashboard_db.add_all([teacher, student_a, student_b])
    dashboard_db.flush()

    dashboard_db.add_all(
        [
            StudentProfile(
                user_id=student_a.id,
                summary="",
                dimensions={
                    "_mastery_cache": {
                        "_course": {"mastery_score": 60},
                    }
                },
                chat_history=[],
            ),
            StudentProfile(
                user_id=student_b.id,
                summary="",
                dimensions={
                    "_evaluation_history": [
                        {"overall_score": 80},
                    ]
                },
                chat_history=[],
            ),
            GeneratedResource(
                user_id=student_a.id,
                resource_type="document",
                agent_name="ConceptAgent",
                title="链表补强",
                content="content",
                meta={"module_key": "linked-list"},
            ),
            StudentLearningMemory(
                user_id=student_a.id,
                course_id="data_structures_algorithms",
                chapter_id="ch02-linear-list",
                skill_id="linear-list-operation",
                problem_slug="reverse-linked-list",
                event_type="oj_submit_fail",
                observed_error_pattern="指针更新错误，next 指针覆盖导致断链",
                failed_strategy="WA",
                evidence_json={
                    "module_key": "linked-list",
                    "verdict": "WA",
                    "error_type": "pointer_update_error",
                },
            ),
            StudentLearningMemory(
                user_id=student_b.id,
                course_id="data_structures_algorithms",
                chapter_id="ch11-dynamic-programming",
                skill_id="dp-state-design",
                problem_slug="climbing-stairs",
                event_type="oj_submit_fail",
                observed_error_pattern="边界初始化遗漏",
                failed_strategy="WA",
                evidence_json={
                    "module_key": "dp",
                    "verdict": "WA",
                    "error_type": "boundary_condition_error",
                },
            ),
            StudentLearningMemory(
                user_id=student_b.id,
                course_id="data_structures_algorithms",
                chapter_id="ch11-dynamic-programming",
                skill_id="dp-state-design",
                problem_slug="climbing-stairs",
                event_type="oj_submit_success",
                observed_error_pattern="",
                failed_strategy="",
                evidence_json={"module_key": "dp", "verdict": "AC"},
            ),
        ]
    )
    dashboard_db.commit()

    data = _request_summary(dashboard_db, teacher)

    assert data["is_demo"] is False
    assert data["overview"] == {
        "student_count": 2,
        "profile_count": 2,
        "average_mastery": 70.0,
        "resource_count": 1,
        "oj_submission_count": 3,
    }
    assert {item["module_key"] for item in data["weak_knowledge_points"]} == {
        "linked-list",
        "dp",
    }
    assert len(data["teaching_suggestions"]) == 3
    assert len(data["reinforcement_packs"]) == 3
