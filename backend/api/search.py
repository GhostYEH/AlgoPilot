"""语义检索 API。"""

from __future__ import annotations

from fastapi import APIRouter, Query

from schemas.search import SemanticSearchResponse, SemanticSearchResult
from services.knowledge.concept_clusters import concept_clusters
from services.knowledge.semantic_search import semantic_search

router = APIRouter()


@router.get("/semantic", response_model=SemanticSearchResponse)
def api_semantic_search(
    q: str = Query(..., min_length=1, description="自然语言检索"),
    scope: str = Query("all", description="all | knowledge | concept | problem"),
    module_key: str = Query("", description="限定模块"),
    difficulty: str = Query("", description="easy | medium | hard"),
    top_k: int = Query(8, ge=1, le=20),
) -> SemanticSearchResponse:
    hits = semantic_search.search(
        q,
        scope=scope,
        module_key=module_key.strip(),
        difficulty=difficulty.strip(),
        top_k=top_k,
    )
    results = [
        SemanticSearchResult(
            id=h.get("id", ""),
            kind=h.get("kind", ""),
            title=h.get("title", ""),
            snippet=h.get("snippet", ""),
            module_key=h.get("module_key", ""),
            concept_ids=h.get("concept_ids") or [],
            node_ids=h.get("node_ids") or [],
            score=round(float(h.get("score") or 0.0), 4),
            slug=h.get("slug", ""),
            difficulty=h.get("difficulty", ""),
        )
        for h in hits
    ]
    node_ids: list[str] = []
    for r in results:
        for nid in r.node_ids:
            if nid and nid not in node_ids:
                node_ids.append(nid)
    return SemanticSearchResponse(query=q, results=results, highlight_node_ids=node_ids)


@router.get("/concept-clusters")
def api_concept_clusters() -> dict[str, str]:
    """概念节点 → 知识簇 ID（社区发现，供路径规划与可视化）。"""
    return concept_clusters()
