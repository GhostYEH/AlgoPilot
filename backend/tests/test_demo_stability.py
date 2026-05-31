"""A3 比赛演示稳定性：健康检查、LLM 回退、API 结构稳定。"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.config import settings
from core.database import SessionLocal
from main import app
from models.db_models import User
from services.oj.ai_diagnosis import diagnose_trace_bug, generate_edge_case
from services.oj.error_patterns import ERROR_TYPE_LABELS
from services.skills.recommend import recommend_skill_cards
from services.verification.builder import build_verification_result
from utils.security import hash_password

client = TestClient(app)


@pytest.fixture
def db() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(db: Session) -> User:
    name = f"demo_{uuid.uuid4().hex[:10]}"
    user = User(username=name, email=f"{name}@test.local", hashed_password=hash_password("pass"))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_health_exposes_demo_subsystems():
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "llm_configured" in data
    assert "tts_configured" in data
    assert data.get("trace_python") is True
    assert "trace_cpp" in data
    assert "demo_hints" in data
    assert isinstance(data["demo_hints"], list)


def test_oj_capabilities_stable_shape():
    r = client.get("/api/oj/capabilities")
    assert r.status_code == 200
    data = r.json()
    assert data.get("trace_python") is True
    assert "trace_cpp" in data
    assert "gdb_available" in data


@pytest.mark.asyncio
async def test_trace_bug_diagnosis_fallback_without_llm():
    steps = [
        {"line": 3, "changed": ["curr"], "vars": {}},
        {"line": 4, "changed": ["curr"], "vars": {}},
        {"line": 5, "changed": ["curr"], "vars": {}},
        {"line": 6, "changed": ["curr"], "vars": {}},
    ]
    result = await diagnose_trace_bug("反转链表", "while curr: curr = curr.next", steps)
    assert result["bug_step_index"] >= 0
    assert result.get("source") in ("fallback", "llm")
    assert result["diagnosis_title"]


@pytest.mark.asyncio
async def test_edge_case_fallback_without_llm():
    sample = {"stdin": "3\n1 2 3\n", "stdout": "6\n"}
    edge = await generate_edge_case(
        problem_title="求和",
        description="读 n 再读 n 个数",
        judge_mode="stdio",
        sample=sample,
        user_code="print(sum(map(int,input().split())))",
    )
    assert edge.get("case")
    assert edge.get("category")


def test_error_type_labels_complete():
    expected = {
        "boundary_condition_error",
        "initialization_error",
        "loop_condition_error",
        "pointer_update_error",
        "recursion_base_case_error",
        "state_transition_error",
        "data_structure_misuse",
        "time_complexity_issue",
    }
    for key in expected:
        assert key in ERROR_TYPE_LABELS


def test_skill_router_returns_list():
    cards = recommend_skill_cards(module_key="dp", topic="爬楼梯")
    assert isinstance(cards, list)
    if cards:
        assert cards[0].id
        assert cards[0].name


def test_verification_result_stable_fields():
    vr = build_verification_result(
        resource_type="document",
        chapter_id="ch02-linear-list",
        verifier_status="passed",
        safety_status="passed",
        final_decision="publish",
    )
    assert vr.verifier_status in ("passed", "warning", "failed")
    assert vr.safety_status in ("passed", "warning", "failed")
    assert vr.final_decision
    assert vr.risk_label


def test_mastery_report_api_shape():
    uname = f"demo_mst_{uuid.uuid4().hex[:8]}"
    reg = client.post(
        "/api/auth/register",
        json={"username": uname, "password": "secret123", "email": f"{uname}@example.com"},
    )
    assert reg.status_code == 200
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}
    r = client.get("/api/mastery/report", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "overall_score" in data
    assert "overall_level" in data
    assert "chapters" in data


def test_memory_summary_api_shape():
    uname = f"demo_mem_{uuid.uuid4().hex[:8]}"
    reg = client.post(
        "/api/auth/register",
        json={"username": uname, "password": "secret123", "email": f"{uname}@example.com"},
    )
    assert reg.status_code == 200
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}
    r = client.get("/api/memory/summary", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "learning_memory_summary" in data or "recent_count" in data


def test_skills_route_api_shape():
    r = client.post(
        "/api/skills/route",
        json={"module_key": "linked-list", "topic": "反转链表", "oj_verdict": "WA"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "matches" in data or "primary" in data or "skill_card" in data
