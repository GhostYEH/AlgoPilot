"""POST /evaluation/oj-struggle 专项测试（无真实 LLM Key）。"""

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
from services.agents.learning_path_catalog import MODULE_CATALOG
from services.memory.memory_service import MemoryService

client = TestClient(app)


def _default_modules() -> list[dict[str, Any]]:
    return [
        {
            "key": m["key"],
            "label": m["label"],
            "phase": m["phase"],
            "available": m["available"],
            "percent": 10 if m["key"] in ("dp", "graph") else 0,
            "done_count": 0,
            "total_count": 5,
        }
        for m in MODULE_CATALOG
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
    name = f"struggle_{uuid.uuid4().hex[:10]}"
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


def _post_oj_struggle(headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    resp = client.post(
        "/api/orchestrator/evaluation/oj-struggle",
        headers=headers,
        json=payload,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _assert_struggle_closed_loop(body: dict[str, Any], *, strong: bool) -> None:
    assert body.get("agent_name") == "EvaluatorAgent"
    assert body.get("course_id") == "data_structures_algorithms"

    matched = body.get("matched_skill")
    skill_cards = body.get("recommended_skill_cards") or []
    assert matched is not None or len(skill_cards) >= 1, "应返回 matched_skill 或 recommended_skill_cards"
    primary_id = (matched or skill_cards[0]).get("id")
    assert primary_id

    assert body.get("error_pattern")
    assert body.get("error_pattern_label")

    actions = body.get("recommended_actions") or []
    remediation = body.get("remediation_label") or body.get("remediation_module_key")
    assert actions or remediation or not strong, "强干预或观察态应含 recommended_actions 或巩固建议"

    resources = body.get("recommended_resources") or []
    assert len(resources) >= 1
    assert resources[0].get("resource_type")

    memory_ok = body.get("memory_recorded") is True or body.get("memory_event_id") is not None
    assert memory_ok, "应写入 StudentMemory"

    mastery_ok = body.get("mastery_updated") is True or bool(body.get("mastery_update_summary"))
    assert mastery_ok, "应返回掌握度更新信息"

    path_hint = (body.get("path_adjustment_suggestion") or "").strip()
    if strong:
        assert body.get("struggle_detected") is True
        assert body.get("planner_notified") is True
        assert remediation, "强干预应返回路径巩固模块"
        assert path_hint or body.get("plan_summary"), "强干预应含路径调整建议"
    else:
        assert body.get("struggle_detected") is False
        assert body.get("planner_notified") is False


@pytest.mark.parametrize(
    "payload",
    [
        {
            "module_key": "dp",
            "problem_slug": "climbing-stairs",
            "knowledge_point": "动态规划",
            "verdict": "WA",
            "consecutive_failures": 3,
            "statuses": ["WA", "WA", "WA"],
            "error_pattern": "initialization_error",
            "course_id": "data_structures_algorithms",
            "chapter_id": "ch11-dynamic-programming",
            "skill_id": "dp-state-design",
            "recent_trace_summary": "dp[0] 未初始化，状态转移依赖未定义边界",
            "overall_percent": 12,
        },
        {
            "module_key": "graph",
            "problem_slug": "number-of-islands",
            "knowledge_point": "图论",
            "verdict": "TLE",
            "consecutive_failures": 4,
            "statuses": ["WA", "WA", "TLE"],
            "error_pattern": "BFS visited 未标记导致重复入队",
            "course_id": "data_structures_algorithms",
            "chapter_id": "ch06-graph",
            "skill_id": "graph-bfs-dfs",
            "recent_trace_summary": "queue 持续增长，visited 集合为空，结点重复入队",
            "overall_percent": 8,
        },
    ],
)
def test_oj_struggle_strong_intervention(
    auth_headers: dict[str, str],
    db: Session,
    payload: dict[str, Any],
):
    """连续 WA/RE/TLE >=3 时触发完整学情闭环。"""
    body = _post_oj_struggle(
        auth_headers,
        {**payload, "modules": _default_modules()},
    )
    _assert_struggle_closed_loop(body, strong=True)

    expected_skill = payload["skill_id"]
    skill_ids = {body.get("matched_skill", {}).get("id")} | {
        c.get("id") for c in body.get("recommended_skill_cards") or []
    }
    assert expected_skill in skill_ids

    user_id = _user_id_from_token(auth_headers)
    memory_id = body.get("memory_event_id")
    assert memory_id is not None
    recent = MemoryService(db).list_recent(user_id, limit=15)
    assert any(m.id == memory_id and m.event_type == "evaluation_struggle" for m in recent)

    assert body.get("chapter_id") == payload["chapter_id"]
    assert any(
        payload["module_key"] in (body.get("remediation_module_key") or "")
        or payload["knowledge_point"] in (body.get("remediation_label") or "")
        or body.get("path_updated") is not None
        for _ in [0]
    )


def test_oj_struggle_below_threshold_observation_only(auth_headers: dict[str, str]):
    """连续失败 <3 时不触发强干预，仅返回观察建议。"""
    body = _post_oj_struggle(
        auth_headers,
        {
            "module_key": "dp",
            "problem_slug": "climbing-stairs",
            "knowledge_point": "动态规划",
            "verdict": "WA",
            "consecutive_failures": 2,
            "statuses": ["WA", "WA"],
            "error_pattern": "state_transition_error",
            "chapter_id": "ch11-dynamic-programming",
            "skill_id": "dp-state-design",
            "modules": _default_modules(),
        },
    )
    _assert_struggle_closed_loop(body, strong=False)
    joined_logs = " ".join(
        f"{log.get('action', '')} {log.get('detail', '')}" for log in body.get("agent_logs") or []
    )
    assert "未达降级阈值" in joined_logs or "学情监测" in joined_logs
    assert not body.get("remediation_module_key")


def test_oj_struggle_ac_clears_intervention(auth_headers: dict[str, str]):
    """AC  verdict 不触发路径降级干预。"""
    body = _post_oj_struggle(
        auth_headers,
        {
            "module_key": "graph",
            "problem_slug": "number-of-islands",
            "knowledge_point": "图论",
            "verdict": "AC",
            "consecutive_failures": 5,
            "statuses": ["WA", "WA", "WA", "WA", "AC"],
            "error_pattern": "",
            "chapter_id": "ch06-graph",
            "modules": _default_modules(),
        },
    )
    assert body.get("struggle_detected") is False
    assert body.get("planner_notified") is False
    assert not body.get("remediation_module_key")
    assert not body.get("path_updated")


def test_oj_struggle_fallback_without_llm(auth_headers: dict[str, str]):
    """LLM 不可用时仍返回可解释的启发式 fallback。"""
    with patch("services.agents.learning_path.chat_completion", new_callable=AsyncMock) as mock_llm:
        mock_llm.side_effect = RuntimeError("no api key")
        body = _post_oj_struggle(
            auth_headers,
            {
                "module_key": "graph",
                "problem_slug": "number-of-islands",
                "knowledge_point": "图论",
                "verdict": "WA",
                "consecutive_failures": 3,
                "statuses": ["WA", "WA", "WA"],
                "error_pattern": "visited 重复入队",
                "chapter_id": "ch06-graph",
                "skill_id": "graph-bfs-dfs",
                "recent_trace_summary": "DFS visited 未标记，结点重复递归",
                "modules": _default_modules(),
            },
        )

    assert body.get("struggle_detected") is True
    assert body.get("plan_summary") or body.get("remediation_label")
    assert body.get("agent_logs")
    _assert_struggle_closed_loop(body, strong=True)
    joined = " ".join(body.get("recommended_actions") or []) + body.get("mastery_update_summary", "")
    assert joined.strip()
