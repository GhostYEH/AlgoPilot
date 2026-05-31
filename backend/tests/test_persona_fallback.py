"""PersonaChat 无 LLM Key 时的 TemplatePersonaFallbackAgent 测试。"""

from __future__ import annotations

import json
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from core.config import settings
from main import app
from schemas.persona import ChatHistoryItem
from services.agents.persona_fallback import (
    GENERATED_BY,
    extract_persona_fallback,
    should_use_persona_fallback,
)

client = TestClient(app)


def _register_user() -> dict[str, str]:
    name = f"persona_{uuid.uuid4().hex[:10]}"
    reg = client.post(
        "/api/auth/register",
        json={"username": name, "password": "pass123", "email": f"{name}@example.com"},
    )
    assert reg.status_code == 200, reg.text
    return {"Authorization": f"Bearer {reg.json()['access_token']}"}


def _parse_sse(body: str) -> list[dict]:
    events: list[dict] = []
    for block in body.split("\n\n"):
        for line in block.split("\n"):
            if line.startswith("data:"):
                events.append(json.loads(line[5:].strip()))
    return events


def test_extract_persona_fallback_keyword_rules():
    history = [
        ChatHistoryItem(
            role="user",
            content="我是大一计科，想准备蓝桥杯，数组链表比较薄弱，遇到 WA 会坚持再试",
        ),
        ChatHistoryItem(role="assistant", content="好的"),
        ChatHistoryItem(
            role="user",
            content="更喜欢看动画和图示学习，递归和边界经常错",
        ),
    ]
    summary, dims, confidence, missing, scores, dim_evidence, update_reason, recent = (
        extract_persona_fallback(history)
    )
    assert summary
    assert dims.knowledge_base
    assert dims.learning_goals
    assert dims.cognitive_style or dims.error_preference
    assert len(scores) == 6
    assert all(1 <= scores[k] <= 10 for k in scores)
    assert update_reason
    assert dim_evidence or recent
    assert confidence.get("knowledge_base") == "explicit" or dims.knowledge_base


@pytest.mark.parametrize("spark_password", ["", "请替换为你的星火APIPassword"])
def test_persona_chat_sse_without_llm_key(monkeypatch: pytest.MonkeyPatch, spark_password: str):
    monkeypatch.setattr(settings, "spark_api_password", spark_password)
    assert should_use_persona_fallback()

    headers = _register_user()
    resp = client.post(
        "/api/orchestrator/persona/chat",
        headers=headers,
        json={
            "message": "我是大一计科，想刷蓝桥杯，链表比较弱",
            "history": [],
        },
    )
    assert resp.status_code == 200, resp.text
    events = _parse_sse(resp.text)
    assert any(e.get("type") == "token" for e in events)
    done = next(e for e in events if e.get("type") == "done")
    assert done.get("content")
    meta = done.get("meta") or {}
    assert meta.get("fallback") is True
    assert meta.get("generated_by") == GENERATED_BY
    assert "离线画像引导模式" in done["content"]
    assert "TemplatePersonaFallbackAgent" in done["content"]


def test_persona_sync_without_llm_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "spark_api_password", "")
    headers = _register_user()
    history = [
        {"role": "user", "content": "我是大二软件工程，目标就业面试，动态规划和图论较弱"},
        {"role": "assistant", "content": "收到"},
    ]
    resp = client.post(
        "/api/orchestrator/persona/sync",
        headers=headers,
        json={
            "message": "遇到 TLE 会求助同学，喜欢动手写代码",
            "history": history,
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("fallback") is True
    profile = body["profile"]
    dims = profile["dimensions"]
    for key in (
        "knowledge_base",
        "cognitive_style",
        "coding_ability",
        "learning_goals",
        "error_preference",
        "grit_level",
    ):
        assert key in dims
    assert profile.get("dimension_scores")
    assert len(profile["dimension_scores"]) == 6
    evidence_ok = bool(profile.get("dimension_evidence")) or bool(profile.get("recent_evidence"))
    assert evidence_ok or profile.get("update_reason")
    assert profile.get("fallback") is True
    assert profile.get("generated_by") == GENERATED_BY


async def _mock_persona_stream(*_args, **_kwargs):
    yield "你好！请继续介绍你的学习目标与薄弱模块。"


def test_persona_chat_with_mock_llm_does_not_fallback(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "spark_api_password", "test-key-for-mock")
    assert not should_use_persona_fallback()

    headers = _register_user()
    with patch("services.agents.base.chat_completion_stream", _mock_persona_stream):
        resp = client.post(
            "/api/orchestrator/persona/chat",
            headers=headers,
            json={"message": "我是计科大一", "history": []},
        )
    assert resp.status_code == 200, resp.text
    done = next(e for e in _parse_sse(resp.text) if e.get("type") == "done")
    meta = done.get("meta") or {}
    assert meta.get("fallback") is not True
    assert "离线画像引导模式" not in done.get("content", "")
