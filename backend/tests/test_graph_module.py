"""graph 图论模块专项一致性测试（课程 / SkillCard / 路径 / 知识库）。"""

from __future__ import annotations

import pytest

from services.agents.learning_path import _default_reason
from services.agents.learning_path_catalog import MODULE_CATALOG, MODULE_DEPENDENCIES_RESOLVED
from services.knowledge.course_loader import (
    chapter_id_for_module,
    index_course_chunks,
    load_manifest,
)
from services.knowledge.retriever import clear_chunks_cache, retriever
from services.skills.models import SkillRouteRequest
from services.skills.registry import SkillRegistry, clear_registry_cache
from services.skills.skill_router import SkillRouter


@pytest.fixture(autouse=True)
def _fresh_caches():
    clear_registry_cache()
    clear_chunks_cache()
    yield
    clear_registry_cache()
    clear_chunks_cache()


def test_manifest_includes_graph_chapter():
    manifest = load_manifest("data_structures_algorithms")
    aliases = manifest.get("module_key_aliases") or {}
    assert aliases.get("graph") == "ch06-graph"

    ch = next(c for c in manifest["chapters"] if c["id"] == "ch06-graph")
    assert ch["title"]
    assert "graph" in ch.get("module_keys", [])
    assert chapter_id_for_module(manifest, "graph") == "ch06-graph"


def test_graph_learning_outcomes_include_bfs_dfs():
    manifest = load_manifest()
    ch = next(c for c in manifest["chapters"] if c["id"] == "ch06-graph")
    joined = " ".join(ch.get("learning_outcomes") or [])
    assert "BFS" in joined
    assert "DFS" in joined
    assert "邻接" in joined or "连通" in joined


def test_course_chunks_index_graph_chapter():
    chunks = index_course_chunks("data_structures_algorithms")
    graph_chunks = [c for c in chunks if c.get("chapter_id") == "ch06-graph"]
    assert graph_chunks, "ch06-graph 应被索引为课程切片"
    joined = " ".join(c["content"] for c in graph_chunks)
    assert "BFS" in joined or "广度" in joined
    assert "DFS" in joined or "深度" in joined


def test_skill_registry_loads_graph_bfs_dfs():
    card = SkillRegistry().get("graph-bfs-dfs")
    assert card is not None
    assert card.id == "graph-bfs-dfs"
    assert card.chapter_id == "ch06-graph"
    assert card.course_id == "data_structures_algorithms"
    assert len(card.common_mistakes) >= 1
    assert any("visited" in m.text.lower() for m in card.common_mistakes)


def test_skill_router_graph_bfs_visited_wa():
    router = SkillRouter()
    req = SkillRouteRequest(
        topic="图 BFS visited 重复访问 WA",
        module_key="graph",
        oj_verdict="WA",
        error_pattern="visited 重复入队",
        trace_summary="queue 持续增长，visited 未标记",
        consecutive_failures=3,
    )
    res = router.route(req)
    assert res.primary is not None
    assert res.primary.id == "graph-bfs-dfs"
    assert res.matches
    assert res.matches[0].skill_id == "graph-bfs-dfs"


def test_learning_path_catalog_graph_available():
    graph = next(m for m in MODULE_CATALOG if m["key"] == "graph")
    assert graph["available"] is True
    assert graph["label"] == "图论"
    assert graph["phase"] == "advanced"


def test_learning_path_graph_dependencies_match_course():
    deps = MODULE_DEPENDENCIES_RESOLVED["graph"]
    assert "stack-queue" in deps
    assert "binary-tree" in deps
    assert "dp" not in deps


def test_learning_path_graph_default_reason_not_planning():
    reason = _default_reason("graph", None)
    assert "课程规划中" not in reason
    assert "数据结构与算法" in reason
    assert "BFS" in reason or "DFS" in reason


def test_kb_search_bfs_dfs_visited_returns_graph():
    hits = retriever.search("BFS DFS visited", module_key="graph", top_k=6)
    assert hits
    joined = " ".join(h["title"] + h["content"] for h in hits).lower()
    assert "bfs" in joined or "广度" in joined
    assert "visited" in joined or "访问" in joined or "入队" in joined
    assert any(
        h.get("module_key") == "graph"
        or "graph" in (h.get("module_keys") or [])
        or h.get("chapter_id") == "ch06-graph"
        for h in hits
    )


def test_kb_no_graph_planning_stale_text():
    from services.knowledge.retriever import _load_chunks

    all_text = " ".join(c["content"] for c in _load_chunks())
    assert "图论（规划中）" not in all_text
