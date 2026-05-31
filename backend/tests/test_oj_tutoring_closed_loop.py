"""智能辅导闭环集成测试：OJ Trace → SkillCard → Memory → Mastery → Persona Patch。

通过 HTTP API + mock LLM 诊断，不依赖真实 SPARK_API_PASSWORD。
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.orm import Session

from core.config import settings
from core.database import SessionLocal
from main import app
from models.db_models import User
from services.mastery.mastery_service import MasteryService
from services.memory.memory_service import MemoryService
from services.oj.error_patterns import ERROR_TYPE_LABELS
from utils.security import hash_password

client = TestClient(app)

LINKED_LIST_DIAGNOSIS: dict[str, Any] = {
    "bug_step_index": 2,
    "diagnosis_title": "指针未更新",
    "detailed_analysis": "curr.next 未保存导致链表断链，指针停滞未移动",
    "source": "fallback",
}

DP_DIAGNOSIS: dict[str, Any] = {
    "bug_step_index": 3,
    "diagnosis_title": "dp 边界未初始化",
    "detailed_analysis": "首行首列 dp 初始化遗漏，状态转移方程依赖未定义边界",
    "source": "fallback",
}

TRACE_STEPS = [
    {
        "line": 3,
        "changed": ["curr"],
        "vars": {"curr": {"type": "ListNode", "value": "node@1"}},
    },
    {
        "line": 4,
        "changed": ["curr", "prev"],
        "vars": {
            "curr": {"type": "ListNode", "value": "node@2"},
            "prev": {"type": "ListNode", "value": "node@1"},
        },
    },
    {
        "line": 5,
        "changed": ["curr"],
        "vars": {"curr": {"type": "ListNode", "value": "node@2"}},
    },
]


@pytest.fixture
def db() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def auth_headers() -> dict[str, str]:
    name = f"loop_{uuid.uuid4().hex[:10]}"
    reg = client.post(
        "/api/auth/register",
        json={"username": name, "password": "pass123", "email": f"{name}@example.com"},
    )
    assert reg.status_code == 200, reg.text
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _user_id_from_token(headers: dict[str, str]) -> int:
    token = headers["Authorization"].split()[-1]
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    return int(payload["sub"])


def _assert_tutoring_closed_loop(
    tutoring: dict[str, Any],
    *,
    allowed_error_patterns: set[str],
    expected_module_key: str,
) -> None:
    assert tutoring, "tutoring 不应为空"
    assert tutoring.get("course_id") == "data_structures_algorithms"

    matched = tutoring.get("matched_skill")
    assert matched is not None, "SkillRouter 应命中 SkillCard"
    assert matched.get("id"), "matched_skill.id 不应为空"
    assert matched.get("name")

    error_pattern = tutoring.get("error_pattern") or ""
    assert error_pattern in ERROR_TYPE_LABELS, f"error_pattern 应在枚举内，实际 {error_pattern!r}"
    assert error_pattern in allowed_error_patterns

    assert tutoring.get("error_pattern_label")
    assert tutoring.get("trace_summary")

    memory_ok = tutoring.get("memory_recorded") is True or tutoring.get("memory_event_id") is not None
    assert memory_ok, "应写入 StudentMemory"

    assert tutoring.get("mastery_update_summary"), "mastery_update_summary 应存在"
    assert tutoring.get("mastery_updated") is True

    assert "persona_updated" in tutoring
    persona_updated = tutoring.get("persona_updated")
    persona_summary = (tutoring.get("persona_patch_summary") or "").strip()
    persona_warning = (tutoring.get("persona_patch_warning") or "").strip()
    assert persona_summary or persona_warning or persona_updated is False, (
        "persona_patch_summary 或 persona_patch_warning 或明确 persona_updated=false"
    )
    assert tutoring.get("profile_updated") == persona_updated

    resources = tutoring.get("recommended_resources") or []
    assert len(resources) >= 1, "recommended_resources 不应为空"
    assert resources[0].get("resource_type")

    assert tutoring.get("module_key") == expected_module_key
    assert tutoring.get("chapter_id")
    assert len(tutoring.get("layered_hints") or []) >= 1


@pytest.mark.parametrize(
    "slug, code, diagnosis, allowed_errors, module_key, chapter_hint",
    [
        (
            "reverse-linked-list",
            "def reverseList(head):\n    curr = head\n    while curr:\n        curr = curr.next\n    return head",
            LINKED_LIST_DIAGNOSIS,
            {"pointer_update_error", "loop_condition_error"},
            "linked-list",
            "ch02",
        ),
        (
            "climbing-stairs",
            "def climbStairs(n):\n    dp = [0]*n\n    for i in range(2,n):\n        dp[i]=dp[i-1]+dp[i-2]\n    return dp[n-1]",
            DP_DIAGNOSIS,
            {"initialization_error", "state_transition_error", "boundary_condition_error"},
            "dp",
            "ch11",
        ),
    ],
)
def test_oj_trace_tutoring_closed_loop_via_api(
    auth_headers: dict[str, str],
    db: Session,
    slug: str,
    code: str,
    diagnosis: dict[str, Any],
    allowed_errors: set[str],
    module_key: str,
    chapter_hint: str,
):
    """POST /api/oj/problems/{slug}/diagnose：非 AC 场景下 Trace 诊断触发完整辅导闭环。"""
    with patch("api.oj.diagnose_trace_bug", new_callable=AsyncMock, return_value=diagnosis):
        resp = client.post(
            f"/api/oj/problems/{slug}/diagnose",
            headers=auth_headers,
            json={
                "code": code,
                "language": "python",
                "steps": TRACE_STEPS,
                "problem_description": "集成测试题目描述",
            },
        )

    if resp.status_code == 404:
        pytest.skip(f"{slug} 未在 OJ catalog 中")

    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body.get("bug_step_index") == diagnosis["bug_step_index"]
    assert body.get("diagnosis_title")
    assert body.get("detailed_analysis")
    assert body.get("source")

    tutoring = body.get("tutoring")
    _assert_tutoring_closed_loop(
        tutoring,
        allowed_error_patterns=allowed_errors,
        expected_module_key=module_key,
    )
    assert chapter_hint in (tutoring.get("chapter_id") or "")

    user_id = _user_id_from_token(auth_headers)
    memory_id = tutoring.get("memory_event_id")
    assert memory_id is not None

    recent = MemoryService(db).list_recent(user_id, limit=10)
    assert any(m.id == memory_id and m.event_type == "oj_diagnosis" for m in recent)

    overview = MasteryService(db).recalculate(
        user_id,
        course_id="data_structures_algorithms",
        chapter_id=tutoring.get("chapter_id") or "",
    )
    assert overview.report is not None
    assert overview.report.recommended_actions


def test_oj_closed_loop_service_orchestration_without_llm(db: Session):
    """直接调用 tutoring pipeline，验证编排层字段（无 HTTP、无 LLM）。"""
    from services.oj.tutoring_pipeline import apply_oj_tutoring

    name = f"svc_{uuid.uuid4().hex[:8]}"
    user = User(username=name, email=f"{name}@example.com", hashed_password=hash_password("x"))
    db.add(user)
    db.commit()
    db.refresh(user)

    tutoring = apply_oj_tutoring(
        db,
        user,
        slug="reverse-linked-list",
        problem={"title": "反转链表", "description": "反转单链表", "module_key": "linked-list"},
        bug_step_index=2,
        diagnosis_title="指针未更新",
        detailed_analysis="curr.next 未保存，链表断链",
        edge_verdict="WA",
        code="while curr: curr = curr.next",
    )

    payload = tutoring.model_dump()
    _assert_tutoring_closed_loop(
        payload,
        allowed_error_patterns={"pointer_update_error", "loop_condition_error"},
        expected_module_key="linked-list",
    )
