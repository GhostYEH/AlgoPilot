"""课程知识库检索（BM25 + 同义词扩展，无向量依赖）。"""

from __future__ import annotations

import json
import math
import re
from functools import lru_cache
from pathlib import Path
from typing import TypedDict

_KB_PATH = Path(__file__).resolve().parents[2] / "knowledge_base" / "chunks.json"

# 同义词 → 扩展检索词（小写/中文均可）
SYNONYM_MAP: dict[str, list[str]] = {
    "bst": ["二叉搜索树", "二叉查找树", "binary search tree"],
    "二叉搜索树": ["bst", "binary search tree"],
    "dp": ["动态规划", "dynamic programming"],
    "动态规划": ["dp"],
    "哈希": ["hash", "hash table", "哈希表", "map", "dict"],
    "hash": ["哈希", "哈希表"],
    "双指针": ["two pointers", "对撞指针", "快慢指针"],
    "two pointers": ["双指针"],
    "栈": ["stack", "单调栈"],
    "队列": ["queue", "bfs"],
    "链表": ["linked list", "linked-list"],
    "二叉树": ["binary tree", "binary-tree"],
    "回溯": ["backtracking", "dfs"],
    "贪心": ["greedy"],
    "排序": ["sorting", "sort", "归并排序", "快速排序", "堆排序"],
    "sorting": ["排序", "sort", "merge sort", "quick sort", "heap sort"],
    "图": ["graph", "图论", "bfs", "dfs"],
    "oj": ["在线评测", "编程题"],
}


class KnowledgeChunk(TypedDict, total=False):
    id: str
    chunk_id: str
    module_key: str
    module_id: str
    title: str
    chapter_title: str
    section_title: str
    keywords: list[str]
    content: str
    excerpt: str
    relevance_score: float
    chunk_type: str
    course_id: str
    chapter_id: str
    doc_kind: str
    doc_id: str
    section: str
    source_path: str
    module_keys: list[str]


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    parts = re.findall(r"[\u4e00-\u9fff]{2,}|[a-z0-9]+", text)
    return [p for p in parts if len(p) >= 2]


def _expand_query_tokens(tokens: list[str]) -> list[str]:
    expanded = list(tokens)
    for t in tokens:
        for key, aliases in SYNONYM_MAP.items():
            key_lower = key.lower()
            if t == key_lower or t in key_lower or key_lower in t:
                expanded.extend(_tokenize(" ".join(aliases)))
    return expanded


def _load_legacy_chunks() -> list[KnowledgeChunk]:
    if not _KB_PATH.is_file():
        return []
    raw = json.loads(_KB_PATH.read_text(encoding="utf-8"))
    out: list[KnowledgeChunk] = []
    for item in raw:
        out.append(
            KnowledgeChunk(
                id=item["id"],
                chunk_id=item["id"],
                module_key=item.get("module_key", ""),
                module_id=item.get("module_key", ""),
                title=item["title"],
                chapter_title=item.get("chapter_title") or item["title"].split("·", 1)[0],
                section_title=item.get("section_title")
                or item.get("chunk_type", "")
                or item["title"],
                keywords=item.get("keywords", []),
                content=item["content"],
                excerpt=_excerpt(item["content"]),
                chunk_type=item.get("chunk_type", ""),
                source_path=item.get("source_path") or "knowledge_base/chunks.json",
            )
        )
    return out


def _load_course_chunks() -> list[KnowledgeChunk]:
    try:
        from services.knowledge.course_loader import index_course_chunks

        return index_course_chunks()
    except Exception:
        return []


@lru_cache(maxsize=1)
def _load_chunks() -> list[KnowledgeChunk]:
    """合并 legacy chunks.json 与课程级 Markdown 知识库切片。"""
    legacy = _load_legacy_chunks()
    course = _load_course_chunks()
    if not course:
        return legacy
    seen: set[str] = {c["id"] for c in legacy}
    merged = list(legacy)
    for ch in course:
        if ch["id"] in seen:
            continue
        seen.add(ch["id"])
        merged.append(ch)
    return merged


def clear_chunks_cache() -> None:
    _load_chunks.cache_clear()
    try:
        from services.knowledge.course_loader import clear_course_caches

        clear_course_caches()
    except Exception:
        pass


class _BM25Index:
    """Okapi BM25 轻量实现。"""

    def __init__(self, docs: list[list[str]], *, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.docs = docs
        self.n = len(docs)
        self.doc_lens = [len(d) for d in docs]
        self.avgdl = sum(self.doc_lens) / self.n if self.n else 0.0
        self.df: dict[str, int] = {}
        for doc in docs:
            for term in set(doc):
                self.df[term] = self.df.get(term, 0) + 1

    def score(self, query: list[str], doc_idx: int) -> float:
        doc = self.docs[doc_idx]
        dl = self.doc_lens[doc_idx]
        tf_map: dict[str, int] = {}
        for t in doc:
            tf_map[t] = tf_map.get(t, 0) + 1
        s = 0.0
        for term in query:
            if term not in tf_map:
                continue
            tf = tf_map[term]
            df = self.df.get(term, 0)
            idf = math.log((self.n - df + 0.5) / (df + 0.5) + 1.0)
            denom = tf + self.k1 * (1 - self.b + self.b * dl / max(self.avgdl, 1e-9))
            s += idf * (tf * (self.k1 + 1)) / denom
        return s


class KnowledgeRetriever:
    def __init__(self) -> None:
        self._index: _BM25Index | None = None
        self._chunk_ids: list[str] = []

    def _ensure_index(self, chunks: list[KnowledgeChunk]) -> None:
        if self._index is not None and len(self._chunk_ids) == len(chunks):
            return
        doc_tokens: list[list[str]] = []
        self._chunk_ids = []
        for ch in chunks:
            text = " ".join(
                [ch["title"], " ".join(ch.get("keywords", [])), ch["content"]]
            )
            doc_tokens.append(_tokenize(text))
            self._chunk_ids.append(ch["id"])
        self._index = _BM25Index(doc_tokens) if doc_tokens else None

    def search(
        self,
        query: str,
        *,
        module_key: str = "",
        course_id: str = "",
        chapter_id: str = "",
        top_k: int = 4,
    ) -> list[KnowledgeChunk]:
        chunks = _load_chunks()
        if not chunks:
            return []
        self._ensure_index(chunks)

        q_tokens = _expand_query_tokens(_tokenize(query))
        if module_key:
            q_tokens.extend(_tokenize(module_key.replace("-", " ")))
        if chapter_id:
            q_tokens.extend(_tokenize(chapter_id.replace("-", " ")))

        pool: list[KnowledgeChunk] = chunks
        if chapter_id:
            scoped = [c for c in chunks if c.get("chapter_id") == chapter_id]
            if scoped:
                pool = scoped
        elif module_key:
            scoped = [
                c
                for c in chunks
                if c["module_key"] == module_key
                or module_key in (c.get("module_keys") or [])
            ]
            if scoped:
                pool = scoped
        if course_id:
            scoped_course = [c for c in pool if c.get("course_id") == course_id]
            if scoped_course:
                pool = scoped_course

        if not self._index:
            return [_retrieval_result(ch, 0.0, 0.0) for ch in chunks[:top_k]]

        id_to_idx = {cid: i for i, cid in enumerate(self._chunk_ids)}
        scored: list[tuple[float, KnowledgeChunk]] = []
        for ch in pool:
            idx = id_to_idx.get(ch["id"])
            if idx is None:
                continue
            score = self._index.score(q_tokens, idx)
            if module_key and (
                ch["module_key"] == module_key
                or module_key in (ch.get("module_keys") or [])
            ):
                score += 1.5
            if chapter_id and ch.get("chapter_id") == chapter_id:
                score += 2.0
            if course_id and ch.get("course_id") == course_id:
                score += 0.5
            if module_key and not ch["module_key"] and not ch.get("module_keys"):
                score += 0.3
            scored.append((score, ch))

        scored.sort(key=lambda x: (-x[0], x[1]["id"]))
        if not scored and module_key:
            scored = [(1.0, c) for c in chunks if c["module_key"] == module_key]
        if not scored:
            scored = [(0.0, chunks[0])] if chunks else []

        seen: set[str] = set()
        out: list[KnowledgeChunk] = []
        max_score = max((score for score, _ in scored), default=0.0)
        for score, ch in scored:
            if ch["id"] in seen:
                continue
            seen.add(ch["id"])
            out.append(_retrieval_result(ch, score, max_score))
            if len(out) >= top_k:
                break
        return out


def _excerpt(content: str, limit: int = 240) -> str:
    text = re.sub(r"\s+", " ", str(content or "")).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _retrieval_result(
    chunk: KnowledgeChunk,
    score: float,
    max_score: float,
) -> KnowledgeChunk:
    result = KnowledgeChunk(**chunk)
    result["chunk_id"] = str(chunk.get("chunk_id") or chunk.get("id") or "")
    result["module_id"] = str(
        chunk.get("module_id") or chunk.get("module_key") or ""
    )
    result["chapter_title"] = str(
        chunk.get("chapter_title")
        or str(chunk.get("title") or "").split("·", 1)[0]
    )
    result["section_title"] = str(
        chunk.get("section_title")
        or chunk.get("section")
        or chunk.get("chunk_type")
        or chunk.get("title")
        or ""
    )
    result["source_path"] = str(
        chunk.get("source_path") or "knowledge_base/chunks.json"
    )
    result["excerpt"] = str(chunk.get("excerpt") or _excerpt(chunk.get("content", "")))
    result["relevance_score"] = (
        round(max(0.0, min(1.0, score / max_score)), 4) if max_score > 0 else 0.0
    )
    return result


def build_source_records(
    chunks: list[KnowledgeChunk],
    *,
    max_sources: int = 5,
) -> list[dict[str, str | float]]:
    """将检索命中转换为可持久化、可直接展示的课程来源。"""
    sources: list[dict[str, str | float]] = []
    seen: set[str] = set()
    for chunk in chunks:
        chunk_id = str(chunk.get("chunk_id") or chunk.get("id") or "")
        if not chunk_id or chunk_id in seen:
            continue
        seen.add(chunk_id)
        sources.append(
            {
                "chunk_id": chunk_id,
                "module_id": str(
                    chunk.get("module_id") or chunk.get("module_key") or ""
                ),
                "chapter_title": str(
                    chunk.get("chapter_title")
                    or str(chunk.get("title") or "").split("·", 1)[0]
                ),
                "section_title": str(
                    chunk.get("section_title")
                    or chunk.get("section")
                    or chunk.get("chunk_type")
                    or chunk.get("title")
                    or ""
                ),
                "source_path": str(
                    chunk.get("source_path") or "knowledge_base/chunks.json"
                ),
                "relevance_score": float(chunk.get("relevance_score") or 0.0),
                "excerpt": str(
                    chunk.get("excerpt") or _excerpt(chunk.get("content", ""))
                ),
            }
        )
        if len(sources) >= max_sources:
            break
    return sources


def format_context_block(chunks: list[KnowledgeChunk]) -> str:
    if not chunks:
        return "（知识库暂无匹配片段，请仅基于通用计科算法常识回答，勿编造具体题号与外链。）"
    lines = ["以下片段来自本平台《数据结构与算法》知识库，生成内容须与之保持一致，勿编造库外题号/URL："]
    for ch in chunks:
        meta_parts = []
        if ch.get("course_id"):
            meta_parts.append(f"course_id={ch['course_id']}")
        if ch.get("chapter_id"):
            meta_parts.append(f"chapter_id={ch['chapter_id']}")
        meta = f" ({', '.join(meta_parts)})" if meta_parts else ""
        lines.append(f"- [{ch['id']}]{meta} {ch['title']}：{ch['content']}")
    return "\n".join(lines)


def primary_course_context(chunks: list[KnowledgeChunk]) -> dict[str, str]:
    """供资源生成 meta 使用的课程上下文（取首个含 course_id 的片段）。"""
    for ch in chunks:
        if ch.get("course_id"):
            return {
                "course_id": str(ch["course_id"]),
                "chapter_id": str(ch.get("chapter_id") or ""),
            }
    return {"course_id": "", "chapter_id": ""}


retriever = KnowledgeRetriever()
