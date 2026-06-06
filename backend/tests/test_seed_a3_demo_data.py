"""seed_a3_demo_data 脚本导入与幂等性测试。"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import SessionLocal
from models.db_models import GeneratedResource, StudentLearningMemory, User
from scripts.seed_a3_demo_data import (
    DEMO_SEED_SOURCE,
    DEMO_USERNAME,
    clear_demo_seed_artifacts,
    run_seed,
)


def test_seed_module_imports():
    from scripts import seed_a3_demo_data as mod

    assert mod.DEMO_USERNAME == "a3_demo"
    assert callable(mod.run_seed)


@pytest.fixture
def db() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_seed_idempotent_memory_and_resource_counts(db: Session):
    other = User(
        username=f"other_{uuid.uuid4().hex[:8]}",
        email=f"other_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="hashed",
    )
    db.add(other)
    db.commit()

    first = run_seed(db)
    second = run_seed(db)

    assert first.user_id == second.user_id
    assert first.memories_count == second.memories_count
    assert first.resources_count == second.resources_count
    assert first.memories_count >= 8
    assert first.resources_count == 6
    assert first.evaluation_count >= 1
    assert first.replan_count >= 1
    assert first.mastery_report_id
    assert first.recommended_next_route.startswith("/")

    demo_memories = [
        r
        for r in db.scalars(
            select(StudentLearningMemory).where(
                StudentLearningMemory.user_id == first.user_id
            )
        )
        if (r.evidence_json or {}).get("source") == DEMO_SEED_SOURCE
    ]
    assert len(demo_memories) == first.memories_count

    demo_resources = [
        r
        for r in db.scalars(
            select(GeneratedResource).where(
                GeneratedResource.user_id == first.user_id
            )
        )
        if (r.meta or {}).get("source") == DEMO_SEED_SOURCE
    ]
    assert len(demo_resources) == first.resources_count

    other_memories = db.scalars(
        select(StudentLearningMemory).where(
            StudentLearningMemory.user_id == other.id
        )
    ).all()
    assert other_memories == []

    cleared_mem, cleared_res = clear_demo_seed_artifacts(db, first.user_id)
    assert cleared_mem == first.memories_count
    assert cleared_res == first.resources_count


def test_demo_user_username_stable(db: Session):
    result = run_seed(db)
    user = db.scalar(select(User).where(User.username == DEMO_USERNAME))
    assert user is not None
    assert user.id == result.user_id
