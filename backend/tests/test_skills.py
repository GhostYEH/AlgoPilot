"""Learning SkillCard 加载、路由与 API 结构测试。"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app
from services.skills.registry import SkillRegistry, clear_registry_cache
from services.skills.skill_router import SkillRouter
from services.skills.models import SkillRouteRequest


@pytest.fixture(autouse=True)
def _fresh_registry():
    clear_registry_cache()
    yield
    clear_registry_cache()


def test_yaml_cards_load():
    reg = SkillRegistry()
    assert len(reg) >= 13
    card = reg.get("dp-state-design")
    assert card is not None
    assert card.chapter_id == "ch11-dynamic-programming"
    assert len(card.common_mistakes) >= 1
    assert card.resource_strategy.document


def test_router_dp_wa_init_error():
    router = SkillRouter()
    req = SkillRouteRequest(
        topic="动态规划 状态转移",
        module_key="dp",
        oj_verdict="WA",
        error_pattern="初始化错误，dp[0] 边界没写",
        trace_summary="dp 数组第一步全零",
        consecutive_failures=3,
    )
    res = router.route(req)
    assert res.primary is not None
    assert res.primary.id == "dp-state-design"
    assert res.matches[0].score >= 30


def test_router_tree_recursion_error():
    router = SkillRouter()
    req = SkillRouteRequest(
        topic="二叉树遍历 中序",
        module_key="binary-tree",
        error_pattern="递归错误 空指针",
        trace_summary="递归进入 null 结点未返回",
        oj_verdict="RE",
        consecutive_failures=2,
    )
    res = router.route(req)
    assert res.primary is not None
    assert res.primary.id == "tree-traversal"


def test_api_list_and_get_stable():
    client = TestClient(app)
    r = client.get("/api/skills")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 13
    first = data[0]
    assert {"id", "name", "course_id", "chapter_id", "description"} <= set(first.keys())

    r2 = client.get("/api/skills/dp-state-design")
    assert r2.status_code == 200
    body = r2.json()
    assert body["id"] == "dp-state-design"
    assert "hint_policy" in body
    assert "resource_strategy" in body


def test_api_route_structure():
    client = TestClient(app)
    r = client.post(
        "/api/skills/route",
        json={
            "topic": "图的 BFS",
            "module_key": "graph",
            "error_pattern": "重复入队",
            "top_k": 2,
        },
    )
    assert r.status_code == 200
    payload = r.json()
    assert "primary" in payload
    assert "matches" in payload
    assert payload["primary"]["id"] == "graph-bfs-dfs"
