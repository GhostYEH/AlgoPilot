"""Agent 输出 strict schema。"""

from __future__ import annotations

import pytest

from schemas.agent_outputs import validate_quiz_payload
from services.agents.resource_roles import GraphAgent


def test_quiz_strict_accepts_valid() -> None:
    out, issues = validate_quiz_payload(
        {
            "questions": [
                {
                    "type": "choice",
                    "stem": "测试题",
                    "options": ["A", "B"],
                    "hint": "提示",
                    "focus": "边界",
                    "difficulty": "easy",
                }
            ]
        }
    )
    assert out is not None
    assert not issues


def test_quiz_strict_rejects_extra_fields() -> None:
    out, issues = validate_quiz_payload(
        {
            "questions": [
                {
                    "type": "choice",
                    "stem": "x",
                    "options": ["A", "B"],
                    "unknown_field": True,
                }
            ]
        }
    )
    assert out is None
    assert issues


def test_graph_agent_normalizes_mindmap_tail_annotations() -> None:
    raw = """mindmap
  root((数据结构与算法))
    课程定位：高校计算机类专业核心课，讲授抽象数据类型
     1. ch06-graph: 图与BFS/DFS
---
**依据知识库**：course:data_structures_algorithms:syllabus
内容校验通过
"""

    content = GraphAgent().normalize_output(raw, hints=type("Hints", (), {"learning_goals": "数据结构与算法"})())

    assert content.startswith("mindmap\n  root((数据结构与算法))")
    assert "---" not in content
    assert "依据知识库" not in content
    assert "内容校验" not in content
    assert "课程定位" in content
    assert "图与BFSDFS" in content


def test_graph_agent_converts_flowchart_to_mindmap_root_syntax() -> None:
    raw = 'flowchart TD\n  root["栈与队列"] --> bfs["BFS 队列"]'
    content = GraphAgent().normalize_output(raw, hints=type("Hints", (), {"learning_goals": "栈与队列"})())

    assert content.startswith("mindmap\n  root((栈与队列))")
    assert "flowchart" not in content


@pytest.mark.asyncio
async def test_graph_agent_rebuilds_generic_map_around_focus(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_chat_completion(*args, **kwargs):
        return """mindmap
  root((数据结构与算法))
    课程定位
    章节一览
    与平台模块映射
    实验项目"""

    monkeypatch.setattr("services.agents.resource_roles.chat_completion", fake_chat_completion)
    title, content, meta = await GraphAgent().generate(
        topic="数据结构与算法",
        profile_block="学习目标：掌握算法",
        module_key="",
        focus_hint="侧重双指针",
        chunks=[],
    )

    assert "双指针" in title
    assert content.startswith("mindmap\n  root((双指针))")
    assert "左右指针" in content
    assert "快慢指针" in content
    assert "课程定位" not in content
    assert meta["mindmap_rebuilt"] is True
