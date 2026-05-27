"""概念图社区发现（Label Propagation，无 networkx 依赖）。"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_GRAPH_PATH = Path(__file__).resolve().parents[2] / "knowledge_base" / "concept_graph.json"


@lru_cache(maxsize=1)
def _load_edges() -> list[tuple[str, str]]:
    if not _GRAPH_PATH.is_file():
        return []
    data = json.loads(_GRAPH_PATH.read_text(encoding="utf-8"))
    edges: list[tuple[str, str]] = []
    for c in data.get("concepts") or []:
        cid = c.get("id")
        if not cid:
            continue
        for pre in c.get("prerequisites") or []:
            edges.append((pre, cid))
    for e in data.get("pattern_edges") or []:
        s, t = e.get("source"), e.get("target")
        if s and t:
            edges.append((s, t))
    return edges


def concept_clusters(max_iter: int = 12) -> dict[str, str]:
    """返回 concept_id -> cluster_id（模块级前缀 cluster）。"""
    edges = _load_edges()
    nodes: set[str] = set()
    for a, b in edges:
        nodes.add(a)
        nodes.add(b)
    if not nodes:
        return {}

    parent = {n: n for n in nodes}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for a, b in edges:
        union(a, b)

    # label propagation 细化
    labels = {n: find(n) for n in nodes}
    adj: dict[str, set[str]] = {n: set() for n in nodes}
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)

    for _ in range(max_iter):
        changed = False
        order = sorted(nodes)
        for n in order:
            neighbors = adj[n]
            if not neighbors:
                continue
            votes: dict[str, int] = {}
            for nb in neighbors:
                lab = labels[nb]
                votes[lab] = votes.get(lab, 0) + 1
            best = max(votes, key=lambda k: (votes[k], k))
            if labels[n] != best:
                labels[n] = best
                changed = True
        if not changed:
            break

    graph = json.loads(_GRAPH_PATH.read_text(encoding="utf-8")) if _GRAPH_PATH.is_file() else {}
    module_of: dict[str, str] = {}
    for c in graph.get("concepts") or []:
        module_of[c["id"]] = c.get("module_key", "misc")
    for p in graph.get("problems") or []:
        module_of[p["id"]] = p.get("module_key", "misc")

    cluster_modules: dict[str, dict[str, int]] = {}
    for nid, lab in labels.items():
        mk = module_of.get(nid, "misc")
        cluster_modules.setdefault(lab, {})
        cluster_modules[lab][mk] = cluster_modules[lab].get(mk, 0) + 1

    readable: dict[str, str] = {}
    for nid, lab in labels.items():
        mods = cluster_modules.get(lab) or {}
        top_mod = max(mods, key=lambda k: (mods[k], k)) if mods else "misc"
        readable[nid] = f"cluster-{top_mod}-{lab[:6]}"

    return readable


def modules_by_cluster_priority(module_keys: list[str]) -> list[str]:
    """同簇模块在拓扑序中尽量相邻（用于路径启发式）。"""
    clusters = concept_clusters()
    if not clusters:
        return module_keys

    graph = json.loads(_GRAPH_PATH.read_text(encoding="utf-8")) if _GRAPH_PATH.is_file() else {}
    cluster_to_modules: dict[str, list[str]] = {}
    for c in graph.get("concepts") or []:
        cid = c.get("id")
        mk = c.get("module_key")
        if not cid or not mk or mk not in module_keys:
            continue
        cl = clusters.get(cid, "")
        cluster_to_modules.setdefault(cl, [])
        if mk not in cluster_to_modules[cl]:
            cluster_to_modules[cl].append(mk)

    seen: set[str] = set()
    ordered: list[str] = []
    for cl in sorted(cluster_to_modules):
        for mk in cluster_to_modules[cl]:
            if mk in module_keys and mk not in seen:
                ordered.append(mk)
                seen.add(mk)
    for mk in module_keys:
        if mk not in seen:
            ordered.append(mk)
    return ordered
