"""学习路径 graph 模块与 catalog 对齐测试。"""

from __future__ import annotations

from schemas.learning_path import LearningPathReplanRequest, ModuleProgressInput
from services.agents.learning_path import _default_reason, _heuristic_plan
from services.agents.learning_path_catalog import MODULE_CATALOG, MODULE_DEPENDENCIES_RESOLVED


def _all_module_progress() -> list[ModuleProgressInput]:
    return [
        ModuleProgressInput(
            key=m["key"],
            label=m["label"],
            phase=m["phase"],
            available=m["available"],
        )
        for m in MODULE_CATALOG
    ]


def test_graph_catalog_available():
    graph = next(m for m in MODULE_CATALOG if m["key"] == "graph")
    assert graph["available"] is True


def test_graph_dependencies_include_stack_queue_and_tree():
    deps = MODULE_DEPENDENCIES_RESOLVED["graph"]
    assert "stack-queue" in deps
    assert "binary-tree" in deps


def test_heuristic_plan_graph_reason_not_planning():
    result = _heuristic_plan(
        "",
        LearningPathReplanRequest(modules=_all_module_progress(), overall_percent=0),
        {},
    )
    graph_step = next(s for s in result["steps"] if s["module_key"] == "graph")
    assert "课程规划中" not in graph_step["reason"]
    assert "数据结构与算法" in graph_step["reason"]
    assert "BFS/DFS" in graph_step["reason"]


def test_unavailable_module_shows_planning_reason(monkeypatch):
    catalog = [
        {**m, "available": False if m["key"] == "monotonic-stack" else m["available"]}
        for m in MODULE_CATALOG
    ]
    monkeypatch.setattr("services.agents.learning_path.MODULE_CATALOG", catalog)
    reason = _default_reason("monotonic-stack", None)
    assert reason == "课程规划中"
