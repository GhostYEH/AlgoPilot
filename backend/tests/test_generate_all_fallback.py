"""generate-all 无 LLM Key 时的模板降级测试。"""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from core.config import settings
from main import app

client = TestClient(app)

REQUIRED_FALLBACK_TYPES = {"document", "mindmap", "exercises", "code_case", "reading"}


def _register_user() -> dict[str, str]:
    name = f"fb_{uuid.uuid4().hex[:10]}"
    reg = client.post(
        "/api/auth/register",
        json={"username": name, "password": "secret123", "email": f"{name}@example.com"},
    )
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _parse_sse(body: str) -> list[dict]:
    events: list[dict] = []
    for line in body.splitlines():
        if line.startswith("data:"):
            events.append(json.loads(line[5:].strip()))
    return events


def test_generate_all_fallback_without_llm_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "spark_api_password", "")
    headers = _register_user()

    r = client.post(
        "/api/orchestrator/resources/generate-all",
        json={"topic": "栈与队列", "module_key": "stack-queue", "focus_hint": "BFS 队列"},
        headers=headers,
    )
    assert r.status_code == 200
    events = _parse_sse(r.text)
    assert events, "SSE 应返回事件"

    assert events[0].get("type") == "progress"
    assert events[0].get("percent") == 0

    workflow_stages = [e for e in events if e.get("type") == "workflow"]
    assert any(e.get("stage") == "llm_check" for e in workflow_stages)
    assert any(
        e.get("agent") == "TemplateFallbackAgent" or e.get("stage") == "fallback_mode"
        for e in workflow_stages
    )

    resources = [e for e in events if e.get("type") == "resource"]
    assert len(resources) >= len(REQUIRED_FALLBACK_TYPES)

    types_seen: set[str] = set()
    for ev in resources:
        res = ev.get("resource") or {}
        meta = res.get("meta") or {}
        assert meta.get("fallback") is True
        assert meta.get("fallback_reason")
        assert meta.get("generated_by") == "TemplateFallbackAgent"
        assert isinstance(meta.get("grounded_chunks"), list)
        types_seen.add(res.get("resource_type"))

    assert REQUIRED_FALLBACK_TYPES.issubset(types_seen)

    done = [e for e in events if e.get("type") == "done"]
    assert done
    assert done[-1].get("percent") == 100
    assert done[-1].get("fallback_mode") is True


def test_template_fallback_unit():
    from services.agents.template_fallback import generate_fallback_resource
    from services.knowledge.retriever import retriever

    chunks = retriever.search("栈 队列", module_key="stack-queue", top_k=3)
    title, content, meta = generate_fallback_resource(
        "document",
        topic="栈与队列",
        profile_block="",
        module_key="stack-queue",
        chunks=chunks,
        fallback_reason="单元测试",
    )
    assert title.startswith("[模板]")
    assert "模板降级" in content
    assert meta["fallback"] is True
    assert meta["generated_by"] == "TemplateFallbackAgent"
