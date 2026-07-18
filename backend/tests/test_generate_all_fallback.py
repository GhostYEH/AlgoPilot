"""generate-all 无 LLM Key 时的模板降级测试。"""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from core.config import settings
from main import app

client = TestClient(app)

REQUIRED_FALLBACK_TYPES = {"document", "mindmap", "code_case", "trace_animation", "reading"}


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
    observable = [
        e
        for e in workflow_stages
        if e.get("agent_name") in {
            "ProfilingAgent",
            "LearningPathAgent",
            "KnowledgeRetriever",
            "ContentVerifierAgent",
            "SafetyAgent",
            "EvaluationAgent",
        }
    ]
    assert observable
    required_fields = {
        "agent_id",
        "agent_name",
        "stage",
        "status",
        "message",
        "timestamp",
        "duration_ms",
        "validation_result",
    }
    assert all(required_fields.issubset(event) for event in observable)
    assert all(
        event["status"] in {"waiting", "running", "success", "retry", "failed", "skipped"}
        for event in observable
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
        assert 2 <= len(meta.get("sources") or []) <= 5
        assert res.get("sources") == meta.get("sources")
        verifier = meta.get("content_verification") or {}
        assert {"passed", "warnings", "grounded_terms", "unsupported_claims"}.issubset(
            verifier
        )
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
    assert "domain_narrative" in content or "模板降级" in content
    assert meta["fallback"] is True
    assert meta["generated_by"] == "TemplateFallbackAgent"


def test_template_fallback_mindmap_outputs_mindmap_syntax():
    from services.agents.template_fallback import generate_fallback_resource
    from services.knowledge.retriever import retriever

    chunks = retriever.search("图 BFS DFS", module_key="graph", top_k=3)
    _, content, meta = generate_fallback_resource(
        "mindmap",
        topic="图",
        profile_block="",
        module_key="graph",
        focus_hint="侧重 BFS/DFS",
        chunks=chunks,
        fallback_reason="单元测试",
    )

    assert content.startswith("mindmap\n  root((")
    assert "遍历算法" in content
    assert "BFS" in content
    assert "flowchart" not in content
    assert "-->" not in content
    assert meta["format"] == "mermaid"


def test_template_fallback_quiz_has_five_topic_aligned_questions():
    from services.agents.template_fallback import generate_fallback_resource

    chunks = [
        {"id": "k1", "title": "链表反转", "content": "先保存后继节点，再更新 next 指针。"},
        {"id": "k2", "title": "边界", "content": "空链表与单节点链表需要单独验证。"},
        {"id": "k3", "title": "复杂度", "content": "迭代反转时间复杂度 O(n)，额外空间 O(1)。"},
    ]
    _, content, _ = generate_fallback_resource(
        "exercises",
        topic="链表反转",
        profile_block="易错点偏好：指针更新顺序",
        module_key="linked-list",
        chunks=chunks,
        fallback_reason="单元测试",
    )

    questions = json.loads(content)["questions"]
    assert len(questions) == 5
    assert [q["type"] for q in questions] == ["choice", "choice", "choice", "fill", "fill"]
    assert all("链表反转" in q["stem"] for q in questions)
    assert all(q.get("answer") for q in questions)
    assert all(q.get("explanation") for q in questions)
    assert all(q["answer"] in q["options"] for q in questions[:3])


def test_template_fallback_reading_items_are_renderable_cards():
    from services.agents.template_fallback import generate_fallback_resource

    chunks = [{"id": "k1", "title": "队列与 BFS", "content": "BFS 使用队列按层访问顶点。"}]
    _, content, _ = generate_fallback_resource(
        "reading",
        topic="图的广度优先搜索",
        profile_block="",
        module_key="graph",
        chunks=chunks,
        fallback_reason="单元测试",
    )

    levels = json.loads(content)["levels"]
    assert levels
    assert all(isinstance(item, dict) for level in levels for item in level["items"])
    assert all(item.get("title") and item.get("why") and item.get("task") for level in levels for item in level["items"])


def test_generate_resource_stream_fallback_without_llm_key(monkeypatch: pytest.MonkeyPatch):
    """单类资源 SSE 真流式：事件按顺序到达、百分比单调递增、中文无乱码。"""
    monkeypatch.setattr(settings, "spark_api_password", "")
    headers = _register_user()

    r = client.post(
        "/api/orchestrator/resources/generate?stream=true",
        json={
            "resource_type": "document",
            "topic": "栈与队列",
            "module_key": "stack-queue",
            "focus_hint": "BFS 队列应用",
        },
        headers=headers,
    )
    assert r.status_code == 200
    events = _parse_sse(r.text)
    assert events, "SSE 应返回事件"

    # 首事件：progress 0%
    assert events[0].get("type") == "progress"
    assert events[0].get("percent") == 0

    # 末尾两事件：resource(100%) 与 done(100%)
    assert events[-1].get("type") == "done"
    assert events[-1].get("percent") == 100
    assert events[-2].get("type") == "resource"
    assert events[-2].get("percent") == 100

    # 中间 workflow 事件百分比应单调不减（真流式 emit 时实时打标）
    wf = [e for e in events if e.get("type") == "workflow"]
    if wf:
        percents = [e.get("percent", 0) for e in wf]
        assert percents == sorted(percents), f"百分比非单调: {percents}"

    # 中文无乱码：主题与 focus_hint 必须原样保留
    body = r.text
    assert "栈与队列" in body
    assert "BFS 队列应用" in body
    # 不应出现 ensure_ascii=True 导致的 \u 转义
    assert "\\u6808" not in body  # '栈' 的 ASCII 转义
    assert "\\u961f" not in body  # '队' 的 ASCII 转义

    # resource 事件携带完整资源对象
    res = events[-2].get("resource") or {}
    assert res.get("resource_type") == "document"
    assert res.get("title")
    assert res.get("content")
    meta = res.get("meta") or {}
    assert meta.get("fallback") is True
    assert meta.get("generated_by") == "TemplateFallbackAgent"
