"""generate-all 多智能体批量管线集成测试（Mock LLM，无需 API Key）。

运行：cd backend && python -m scripts.test_generate_all_integration
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base
from models.db_models import GeneratedResource, StudentProfile, User
from schemas.resources import CORE_RESOURCE_PIPELINE, PARALLEL_PHASES
from services.agents.resources import ResourceAgents
from services.agents.verifier import verifier_agent
from services.knowledge.retriever import retriever
from services.orchestrator.core import orchestrator

# --- Mock 产物（满足 PipelineContext 解析与安全审查）---

_MOCK_DOCUMENT = json.dumps(
    {
        "domain_narrative": {
            "headline": "测试栈场景",
            "story": "在星际港口，货物需按后进先出规则装卸。",
            "illustration_hint": "霓虹港口",
        },
        "structure_logic": {
            "learning_objectives": ["理解 LIFO"],
            "abstract_model": "入栈出栈序列",
            "data_structures": ["栈"],
            "algorithm_outline": "push / pop",
            "time_complexity": "O(1)",
            "space_complexity": "O(n)",
            "correctness_proof": "栈操作均摊 O(1)。",
            "pitfalls": ["空栈 pop"],
        },
    },
    ensure_ascii=False,
)

_MOCK_MINDMAP = 'flowchart TD\n  root["栈"] --> push["入栈"]\n  push --> pop["出栈"]'

_MOCK_EXERCISES = json.dumps(
    {
        "questions": [
            {
                "type": "choice",
                "stem": "栈的特点是？",
                "options": ["FIFO", "LIFO", "随机", "排序"],
                "hint": "后进先出",
                "focus": "LIFO",
                "difficulty": "easy",
            },
            {
                "type": "choice",
                "stem": "空栈 pop 会导致？",
                "options": ["下溢", "溢出", "O(n)", "无影响"],
                "hint": "边界",
                "focus": "边界",
                "difficulty": "easy",
            },
            {
                "type": "fill",
                "stem": "入栈时间复杂度为 ___",
                "hint": "O(1)",
                "focus": "复杂度",
                "difficulty": "medium",
            },
        ]
    },
    ensure_ascii=False,
)

_MOCK_SCENARIO = json.dumps(
    {
        "domain_narrative": {
            "headline": "港口调度",
            "story": "指挥官需按规则调度集装箱。",
            "mission": "完成装卸任务",
            "illustration_hint": "码头",
        },
        "structure_logic": {
            "problem_formalization": "维护栈结构",
            "data_structures": ["栈"],
            "code_framework": "def solve():\n    # TODO: 实现栈\n    pass\n",
            "step_hints": ["定义栈", "处理 push", "处理 pop"],
            "time_complexity": "O(n)",
            "space_complexity": "O(n)",
            "correctness_proof": "每元素入栈出栈各一次。",
        },
    },
    ensure_ascii=False,
)

_MOCK_TRACE = json.dumps(
    {
        "title": "栈演示",
        "code": "stack=[]\nfor i in range(3):\n    stack.append(i)\nprint(len(stack))\n",
        "stdin": "",
        "stdout": "3\n",
        "narration_hint": "观察栈长度变化",
        "steps": [],
        "verdict": "SKIPPED",
        "trace_source": "mock",
    },
    ensure_ascii=False,
)

_MOCK_BY_TYPE: dict[str, str] = {
    "document": _MOCK_DOCUMENT,
    "mindmap": _MOCK_MINDMAP,
    "exercises": _MOCK_EXERCISES,
    "code_case": _MOCK_SCENARIO,
    "trace_animation": _MOCK_TRACE,
}

_generate_calls: list[tuple[str, str]] = []


async def _mock_generate_with_context(
    resource_type: str,
    *,
    topic: str,
    profile_block: str,
    module_key: str = "",
    focus_hint: str = "",
    chunks: list,
) -> tuple[str, str, dict]:
    _generate_calls.append((resource_type, focus_hint or ""))
    content = _MOCK_BY_TYPE[resource_type]
    fmt = "trace_json" if resource_type == "trace_animation" else "mock"
    meta = {
        "format": fmt,
        "verified": True,
        "trace_verdict": "SKIPPED" if resource_type == "trace_animation" else None,
    }
    return f"Mock · {resource_type}", content, meta


async def _mock_verify(content: str, chunks: list, *, topic: str = "") -> tuple[bool, str, list, str]:
    return True, content, ["mock-chunk-1"], ""


def _parse_sse_lines(chunks: list[str]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for chunk in chunks:
        for line in chunk.splitlines():
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))
    return events


def _setup_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return session_factory


async def _run_test() -> None:
    global _generate_calls
    _generate_calls = []

    session_factory = _setup_memory_db()
    db = session_factory()

    import core.database as db_module

    original_session_local = db_module.SessionLocal
    db_module.SessionLocal = session_factory

    user = User(username="test_generate_all", email="tga@test.local", hashed_password="x")
    db.add(user)
    db.commit()
    db.refresh(user)

    profile = StudentProfile(
        user_id=user.id,
        summary="集成测试用户",
        dimensions={
            "knowledge_base": "了解数组",
            "learning_goals": "掌握栈",
            "error_preference": "空栈边界",
        },
    )
    db.add(profile)
    db.commit()

    sse_chunks: list[str] = []

    with (
        patch.object(ResourceAgents, "generate_with_context", _mock_generate_with_context),
        patch.object(verifier_agent, "verify", _mock_verify),
        patch.object(retriever, "search", return_value=[]),
    ):
        async for line in orchestrator.generate_all_resources_stream(
            db,
            user,
            topic="栈",
            module_key="stack",
            focus_hint="集成测试",
        ):
            sse_chunks.append(line)

    db_module.SessionLocal = original_session_local

    events = _parse_sse_lines(sse_chunks)
    resource_events = [e for e in events if e.get("type") == "resource"]
    done_events = [e for e in events if e.get("type") == "done"]
    collab_events = [e for e in events if e.get("type") == "collaboration"]
    progress_parallel = [
        e for e in events if e.get("type") == "progress" and e.get("parallel") is True
    ]

    assert len(resource_events) == len(CORE_RESOURCE_PIPELINE), (
        f"期望 {len(CORE_RESOURCE_PIPELINE)} 条 resource 事件，实际 {len(resource_events)}"
    )
    got_types = [e["resource"]["resource_type"] for e in resource_events]
    assert set(got_types) == set(CORE_RESOURCE_PIPELINE)

    assert done_events, "缺少 done 事件"
    assert done_events[-1].get("percent") == 100
    assert done_events[-1].get("partial_failure") is not True

    assert progress_parallel, "Phase 2 应标记 parallel=true"
    assert len(progress_parallel) == 2

    # 协作摘要：Phase 2 的 mindmap / exercises 应收到 ConceptAgent 摘要
    phase2_calls = [c for c in _generate_calls if c[0] in ("mindmap", "exercises")]
    assert len(phase2_calls) == 2
    for rtype, hint in phase2_calls:
        assert "ConceptAgent" in hint or "讲解摘要" in hint, (
            f"{rtype} 未携带 document 协作上下文: {hint[:120]!r}"
        )

    # code_case 应携带 QuizAgent 考查侧重（在 exercises 之后）
    code_call = next(c for c in _generate_calls if c[0] == "code_case")
    assert "QuizAgent" in code_call[1] or "考查侧重" in code_call[1]

    # SSE 增量：各 collaboration 批次的日志条数之和应等于 done 全量条数
    batched_logs: list[dict] = []
    for ev in collab_events:
        batched_logs.extend(ev.get("agent_logs") or [])
    final_logs = done_events[-1].get("agent_logs") or []
    assert len(batched_logs) == len(final_logs), (
        f"增量日志条数 {len(batched_logs)} != done 全量 {len(final_logs)}"
    )

    # 落库：五类各一条（并行 Session 亦写入同一 engine）
    rows = db.query(GeneratedResource).filter(GeneratedResource.user_id == user.id).all()
    assert len(rows) == 5
    assert {r.resource_type for r in rows} == set(CORE_RESOURCE_PIPELINE)

    # 拓扑与常量一致
    flat = [t for phase in PARALLEL_PHASES for t in phase]
    assert flat == CORE_RESOURCE_PIPELINE

    # TraceAgent：应跳过 ContentVerifier 文本校验（由 trace_runner 负责）
    trace_skips = [
        e
        for e in events
        if e.get("type") == "workflow"
        and e.get("resource_type") == "trace_animation"
        and e.get("stage") == "content_verify"
        and e.get("status") == "skipped"
    ]
    assert trace_skips, "TraceAgent 应跳过 ContentVerifier 文本校验"

    db.close()
    print("generate-all integration: OK")
    print("  resources:", got_types)
    print("  agent_log entries:", len(final_logs))
    print("  db rows:", len(rows))


def main() -> int:
    try:
        asyncio.run(_run_test())
        return 0
    except Exception as exc:
        print("FAILED:", exc)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
