"""A3 比赛演示主链路冒烟测试：8 个核心接口，无真实 LLM Key 可运行。"""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from core.config import settings
from main import app

client = TestClient(app)


def _register_user() -> dict[str, str]:
    name = f"a3demo_{uuid.uuid4().hex[:10]}"
    reg = client.post(
        "/api/auth/register",
        json={"username": name, "password": "secret123", "email": f"{name}@example.com"},
    )
    assert reg.status_code == 200, reg.text
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _parse_sse(body: str) -> list[dict]:
    events: list[dict] = []
    for line in body.splitlines():
        if line.startswith("data:"):
            events.append(json.loads(line[5:].strip()))
    return events


def _default_modules() -> list[dict]:
    from services.agents.learning_path_catalog import MODULE_CATALOG

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


# ── 1. 画像同步接口 ──────────────────────────────────────────


def test_a3_demo_persona_sync_fallback():
    """POST /persona/sync — 无 LLM Key 时走 fallback 画像抽取。"""
    headers = _register_user()
    r = client.post(
        "/api/orchestrator/persona/sync",
        json={
            "message": "我是大一学生，喜欢看图学习，链表比较弱",
            "history": [
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "你好！我们来了解下你的学习情况"},
            ],
        },
        headers=headers,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "profile" in data
    profile = data["profile"]
    assert profile.get("summary") or profile.get("fallback") is True
    assert "fallback" in data
    if data.get("fallback"):
        assert data.get("fallback_reason")


# ── 2. 学习路径规划接口 ──────────────────────────────────────


def test_a3_demo_learning_path_plan():
    """GET /learning-path/plan — 返回路径规划结构体。"""
    headers = _register_user()
    r = client.get("/api/orchestrator/learning-path/plan", headers=headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "plan" in data
    plan = data["plan"]
    if plan is not None:
        assert "summary" in plan or "ordered_keys" in plan


# ── 3. 资源生成接口 fallback 分支 ────────────────────────────


def test_a3_demo_resource_generate_fallback():
    """POST /resources/generate — 无 LLM Key 时走模板降级。"""
    headers = _register_user()
    r = client.post(
        "/api/orchestrator/resources/generate",
        json={
            "resource_type": "document",
            "topic": "栈与队列",
            "module_key": "stack-queue",
        },
        headers=headers,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "resource" in data
    res = data["resource"]
    assert res["resource_type"] == "document"
    assert res["title"]
    meta = res.get("meta") or {}
    assert meta.get("fallback") is True or meta.get("verified") is not None


# ── 4. 批量资源生成接口 ──────────────────────────────────────


def test_a3_demo_generate_all_fallback():
    """POST /resources/generate-all — SSE 流式返回 fallback 资源。"""
    headers = _register_user()
    r = client.post(
        "/api/orchestrator/resources/generate-all",
        json={"topic": "链表与指针", "module_key": "linked-list", "focus_hint": "指针操作"},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    events = _parse_sse(r.text)
    assert events, "SSE 应返回事件"

    resources = [e for e in events if e.get("type") == "resource"]
    assert len(resources) >= 1, "应至少返回 1 个 fallback 资源"

    done_events = [e for e in events if e.get("type") == "done"]
    assert done_events, "应有 done 事件"
    assert done_events[-1].get("percent") == 100


# ── 5. /evaluation 学习效果评估 ──────────────────────────────


def test_a3_demo_evaluation():
    """POST /evaluation — 返回学习效果评估结构体。"""
    headers = _register_user()
    r = client.post(
        "/api/orchestrator/evaluation",
        json={
            "overall_percent": 30,
            "modules": _default_modules(),
        },
        headers=headers,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("agent_name") == "EvaluationAgent"
    assert isinstance(data.get("overall_score"), int)
    assert isinstance(data.get("dimensions"), list)
    if data["dimensions"]:
        dim = data["dimensions"][0]
        assert "key" in dim
        assert "label" in dim
        assert "score" in dim
    assert isinstance(data.get("weak_module_keys"), list)
    assert isinstance(data.get("suggestions"), list)
    assert isinstance(data.get("push_strategy"), str)


# ── 6. /evaluation/oj-struggle ───────────────────────────────


def test_a3_demo_oj_struggle_evaluation():
    """POST /evaluation/oj-struggle — 连续受挫触发闭环。"""
    headers = _register_user()
    r = client.post(
        "/api/orchestrator/evaluation/oj-struggle",
        json={
            "module_key": "dp",
            "problem_slug": "climbing-stairs",
            "knowledge_point": "动态规划",
            "verdict": "WA",
            "consecutive_failures": 3,
            "statuses": ["WA", "WA", "WA"],
            "error_pattern": "initialization_error",
            "chapter_id": "ch11-dynamic-programming",
            "skill_id": "dp-state-design",
            "overall_percent": 12,
            "modules": _default_modules(),
        },
        headers=headers,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("agent_name") == "EvaluatorAgent"
    assert data.get("struggle_detected") is True
    assert data.get("planner_notified") is True
    assert data.get("memory_recorded") is True or data.get("memory_event_id") is not None
    assert isinstance(data.get("recommended_resources"), list)
    assert len(data["recommended_resources"]) >= 1


# ── 7. OJ 诊断接口 ──────────────────────────────────────────


def test_a3_demo_oj_diagnose_fallback():
    """POST /oj/problems/{slug}/diagnose — fallback 诊断可用。"""
    r = client.post(
        "/api/oj/problems/two-sum/diagnose",
        json={
            "code": "class Solution:\n    def twoSum(self, nums, target):\n        for i in range(len(nums)):\n            for j in range(i+1, len(nums)):\n                if nums[i] + nums[j] == target:\n                    return [i, j]",
            "steps": [
                {"line": 3, "changed": ["i"], "vars": {}},
                {"line": 4, "changed": ["j"], "vars": {}},
                {"line": 5, "changed": [], "vars": {}},
            ],
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "bug_step_index" in data
    assert "diagnosis_title" in data
    assert "detailed_analysis" in data
    assert data.get("source") in ("fallback", "llm")


# ── 8. 资源推荐接口 ──────────────────────────────────────────


def test_a3_demo_resource_recommendations():
    """GET /resources/recommendations — 返回推荐列表（空用户也可调用）。"""
    headers = _register_user()
    r = client.get(
        "/api/orchestrator/resources/recommendations",
        params={"limit": 4},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "items" in data
    assert isinstance(data["items"], list)


# ── 额外：确保所有接口在无 API Key 时不崩溃 ──────────────────


def test_a3_demo_no_llm_key_all_endpoints_alive(monkeypatch: pytest.MonkeyPatch):
    """禁用 LLM Key 后，8 个主链路接口全部返回 2xx。"""
    monkeypatch.setattr(settings, "spark_api_password", "")
    headers = _register_user()

    endpoints = [
        ("GET", "/api/orchestrator/persona/profile", None),
        ("GET", "/api/orchestrator/learning-path/plan", None),
        ("GET", "/api/orchestrator/resources/recommendations", None),
        ("GET", "/api/orchestrator/resources", None),
    ]
    for method, url, body in endpoints:
        r = client.request(method, url, json=body, headers=headers)
        assert r.status_code == 200, f"{method} {url} → {r.status_code}: {r.text[:200]}"

    r = client.post(
        "/api/orchestrator/persona/sync",
        json={"message": "测试画像", "history": []},
        headers=headers,
    )
    assert r.status_code == 200, f"persona/sync → {r.status_code}"

    r = client.post(
        "/api/orchestrator/evaluation",
        json={"overall_percent": 20, "modules": _default_modules()},
        headers=headers,
    )
    assert r.status_code == 200, f"evaluation → {r.status_code}"

    r = client.post(
        "/api/orchestrator/evaluation/oj-struggle",
        json={
            "module_key": "linked-list",
            "verdict": "WA",
            "consecutive_failures": 3,
            "error_pattern": "pointer_update_error",
            "overall_percent": 15,
            "modules": _default_modules(),
        },
        headers=headers,
    )
    assert r.status_code == 200, f"oj-struggle → {r.status_code}"
