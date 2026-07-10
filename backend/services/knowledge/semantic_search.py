"""混合语义检索：BM25 + TF-IDF 余弦 + 概念图谱关键词匹配。"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, TypedDict

from services.knowledge.retriever import KnowledgeRetriever, _tokenize
from services.oj.problem_store import list_problems

_KB_DIR = Path(__file__).resolve().parents[2] / "knowledge_base"
_CONCEPT_PATH = _KB_DIR / "concept_graph.json"


class SearchHit(TypedDict, total=False):
    id: str
    kind: str
    title: str
    snippet: str
    module_key: str
    concept_ids: list[str]
    node_ids: list[str]
    score: float
    slug: str
    difficulty: str


def _load_concept_graph() -> dict[str, Any]:
    if not _CONCEPT_PATH.is_file():
        return {"concepts": [], "problems": [], "pattern_edges": []}
    return json.loads(_CONCEPT_PATH.read_text(encoding="utf-8"))


def _tfidf_vectors(docs: list[list[str]]) -> tuple[list[dict[str, float]], dict[str, float]]:
    n = len(docs)
    df: dict[str, int] = {}
    for doc in docs:
        for term in set(doc):
            df[term] = df.get(term, 0) + 1
    idf = {t: math.log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}

    vecs: list[dict[str, float]] = []
    for doc in docs:
        tf: dict[str, int] = {}
        for t in doc:
            tf[t] = tf.get(t, 0) + 1
        denom = len(doc) or 1
        vec = {t: (c / denom) * idf.get(t, 0.0) for t, c in tf.items()}
        vecs.append(vec)
    return vecs, idf


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(v * b.get(k, 0.0) for k, v in a.items())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return dot / (na * nb)


class SemanticSearchService:
    def __init__(self) -> None:
        self._retriever = KnowledgeRetriever()

    def search(
        self,
        query: str,
        *,
        scope: str = "all",
        module_key: str = "",
        difficulty: str = "",
        top_k: int = 8,
    ) -> list[SearchHit]:
        q = query.strip()
        if not q:
            return []

        hits: list[SearchHit] = []
        q_tokens = _tokenize(q)

        if scope in ("all", "knowledge"):
            hits.extend(self._search_chunks(q, q_tokens, module_key=module_key, top_k=top_k))

        if scope in ("all", "concept", "problem"):
            hits.extend(self._search_concept_graph(q, q_tokens, module_key=module_key, difficulty=difficulty))

        if scope in ("all", "problem"):
            hits.extend(self._search_problems(q, q_tokens, difficulty=difficulty))

        hits.sort(key=lambda h: h.get("score", 0.0), reverse=True)
        seen: set[str] = set()
        deduped: list[SearchHit] = []
        for h in hits:
            key = f"{h.get('kind')}:{h.get('id')}"
            if key in seen:
                continue
            seen.add(key)
            deduped.append(h)
            if len(deduped) >= top_k:
                break
        return deduped

    def _search_chunks(
        self, query: str, q_tokens: list[str], *, module_key: str, top_k: int
    ) -> list[SearchHit]:
        chunks = self._retriever.search(query, module_key=module_key, top_k=top_k)
        out: list[SearchHit] = []
        for i, ch in enumerate(chunks):
            mk = ch.get("module_key", "")
            out.append(
                SearchHit(
                    id=ch["id"],
                    kind="chunk",
                    title=ch.get("title", ""),
                    snippet=(ch.get("content") or "")[:160],
                    module_key=mk,
                    concept_ids=[],
                    node_ids=[mk] if mk else [],
                    score=1.0 - i * 0.05,
                )
            )
        return out

    def _search_concept_graph(
        self,
        query: str,
        q_tokens: list[str],
        *,
        module_key: str,
        difficulty: str,
    ) -> list[SearchHit]:
        graph = _load_concept_graph()
        docs: list[list[str]] = []
        meta: list[dict[str, Any]] = []

        for c in graph.get("concepts") or []:
            if module_key and c.get("module_key") != module_key:
                continue
            text = " ".join(
                [c.get("label", ""), c.get("description", ""), " ".join(c.get("keywords") or [])]
            )
            docs.append(_tokenize(text))
            meta.append({**c, "kind": "concept", "node_ids": [c["id"], c.get("module_key", "")]})

        for p in graph.get("problems") or []:
            if module_key and p.get("module_key") != module_key:
                continue
            if difficulty and p.get("difficulty") != difficulty:
                continue
            text = " ".join(
                [p.get("label", ""), p.get("slug", ""), " ".join(p.get("keywords") or [])]
            )
            docs.append(_tokenize(text))
            node_ids = [p["id"]] + list(p.get("concept_ids") or []) + [p.get("module_key", "")]
            meta.append({**p, "kind": "problem", "node_ids": [x for x in node_ids if x]})

        if not docs:
            return []

        vecs, idf = _tfidf_vectors(docs)
        q_vec = {t: (q_tokens.count(t) / max(len(q_tokens), 1)) * idf.get(t, 0.0) for t in set(q_tokens)}

        out: list[SearchHit] = []
        ql = query.lower()
        for i, m in enumerate(meta):
            cos = _cosine(q_vec, vecs[i])
            kw_boost = 0.0
            for kw in m.get("keywords") or []:
                if kw.lower() in ql or kw in query:
                    kw_boost += 0.15
            if m.get("label", "") in query:
                kw_boost += 0.2
            score = cos * 0.7 + kw_boost
            if score < 0.08 and not kw_boost:
                continue
            snippet = m.get("description") or m.get("slug") or m.get("label", "")
            out.append(
                SearchHit(
                    id=m["id"],
                    kind=m["kind"],
                    title=m.get("label", m.get("id", "")),
                    snippet=str(snippet)[:160],
                    module_key=m.get("module_key", ""),
                    concept_ids=list(m.get("concept_ids") or ([m["id"]] if m["kind"] == "concept" else [])),
                    node_ids=list(m.get("node_ids") or []),
                    score=score,
                    slug=m.get("slug", ""),
                    difficulty=m.get("difficulty", ""),
                )
            )
        return out

    def _search_problems(
        self, query: str, q_tokens: list[str], *, difficulty: str
    ) -> list[SearchHit]:
        items = list_problems(q=query)
        out: list[SearchHit] = []
        ql = query.lower()
        for i, p in enumerate(items[:12]):
            diff = p.get("difficulty", "medium")
            if difficulty and diff != difficulty:
                continue
            slug = p.get("slug", "")
            title = p.get("title") or slug
            score = 0.5 - i * 0.03
            if ql in slug.lower() or ql in title.lower():
                score += 0.3
            out.append(
                SearchHit(
                    id=f"oj-{slug}",
                    kind="oj_problem",
                    title=title,
                    snippet=slug,
                    module_key="",
                    concept_ids=[],
                    node_ids=[slug],
                    score=score,
                    slug=slug,
                    difficulty=diff,
                )
            )
        return out


semantic_search = SemanticSearchService()
