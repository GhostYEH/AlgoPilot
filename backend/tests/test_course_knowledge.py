"""课程级知识库 data_structures_algorithms 加载与 RAG 检索测试。"""

from __future__ import annotations

import pytest

from services.knowledge.course_loader import (
    get_course_summary,
    index_course_chunks,
    list_registered_courses,
    load_manifest,
    validate_prerequisite_graph,
)
from services.knowledge.retriever import clear_chunks_cache, retriever


@pytest.fixture(autouse=True)
def _fresh_kb_cache():
    clear_chunks_cache()
    yield
    clear_chunks_cache()


def test_course_registered():
    courses = list_registered_courses()
    assert "data_structures_algorithms" in courses


def test_course_manifest_parses():
    manifest = load_manifest("data_structures_algorithms")
    assert manifest["course_id"] == "data_structures_algorithms"
    assert manifest["course_name"] == "数据结构与算法"
    assert len(manifest.get("chapters") or []) >= 14
    ch = next(c for c in manifest["chapters"] if c["id"] == "ch11-dynamic-programming")
    assert "dp" in ch.get("module_keys", [])
    assert "ch09-recursion-divide-conquer" in ch.get("prerequisites", [])


def test_prerequisite_graph_valid():
    manifest = load_manifest()
    errors = validate_prerequisite_graph(manifest)
    assert errors == [], f"先修图错误: {errors}"


def test_course_chunks_indexed():
    summary = get_course_summary()
    assert summary["course_id"] == "data_structures_algorithms"
    assert summary["chunk_count"] > 50
    assert summary["prerequisite_errors"] == []

    chunks = index_course_chunks()
    ids = {c["id"] for c in chunks}
    assert any("ch11-dynamic-programming" in cid for cid in ids)
    assert any(c.get("course_id") == "data_structures_algorithms" for c in chunks)


def test_retriever_finds_dynamic_programming():
    hits = retriever.search("动态规划 状态转移", module_key="dp", top_k=5)
    assert hits
    text = " ".join(h["content"] for h in hits)
    assert "动态规划" in text or "DP" in text.upper() or "dp" in text.lower()
    assert any(
        h.get("chapter_id") == "ch11-dynamic-programming" or "动态规划" in h["title"]
        for h in hits
    )


def test_retriever_finds_binary_tree_traversal():
    hits = retriever.search("二叉树遍历 中序", module_key="binary-tree", top_k=5)
    assert hits
    joined = " ".join(h["title"] + h["content"] for h in hits)
    assert "遍历" in joined or "二叉树" in joined


def test_retriever_finds_graph_bfs():
    hits = retriever.search("图的 BFS 广度优先", module_key="graph", top_k=5)
    assert hits
    joined = " ".join(h["title"] + h["content"] for h in hits)
    assert "BFS" in joined or "广度" in joined or "图的 BFS" in joined


def test_kb_no_graph_planning_text():
    from services.knowledge.retriever import _load_chunks

    chunks = _load_chunks()
    all_text = " ".join(c["content"] for c in chunks)
    assert "图论（规划中）" not in all_text


def test_retriever_finds_bfs_graph_chunk():
    hits = retriever.search("BFS", module_key="graph", top_k=5)
    assert hits
    joined = " ".join(h["title"] + h["content"] for h in hits)
    assert "BFS" in joined
    assert any(h.get("module_key") == "graph" or "graph" in (h.get("module_keys") or []) for h in hits)


def test_retriever_finds_dfs_visited_error():
    hits = retriever.search("DFS visited 重复入队", module_key="graph", top_k=5)
    assert hits
    joined = " ".join(h["title"] + h["content"] for h in hits).lower()
    assert "visited" in joined or "访问" in joined
    assert "重复" in joined or "入队" in joined or "tle" in joined


def test_chapter_metadata_on_chunks():
    hits = retriever.search(
        "回溯 剪枝",
        course_id="data_structures_algorithms",
        chapter_id="ch12-backtracking",
        top_k=3,
    )
    assert hits
    assert all(h.get("course_id") == "data_structures_algorithms" for h in hits if h.get("course_id"))
    assert all(h.get("chapter_id") == "ch12-backtracking" for h in hits)
