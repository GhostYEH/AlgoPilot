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
    "图": ["graph", "图论", "bfs", "dfs"],
    "oj": ["在线评测", "编程题"],
}


class KnowledgeChunk(TypedDict, total=False):
    id: str
    module_key: str
    title: str
    keywords: list[str]
    content: str
    chunk_type: str


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    parts = re.findall(r"[\u4e00-\u9fff]{2,}|[a-z0-9]+", text)
    return [p for p in parts if len(p) >= 2]


def _expand_query_tokens(tokens: list[str]) -> list[str]:
    expanded = list(tokens)
    for t in tokens:
        for key, aliases in SYNONYM_MAP.items():
            if t == key.lower() or t in key.lower():
                expanded.extend(_tokenize(" ".join(aliases)))
    return expanded


@lru_cache(maxsize=1)
def _load_chunks() -> list[KnowledgeChunk]:
    if not _KB_PATH.is_file():
        return []
    raw = json.loads(_KB_PATH.read_text(encoding="utf-8"))
    out: list[KnowledgeChunk] = []
    for item in raw:
        out.append(
            KnowledgeChunk(
                id=item["id"],
                module_key=item.get("module_key", ""),
                title=item["title"],
                keywords=item.get("keywords", []),
                content=item["content"],
                chunk_type=item.get("chunk_type", ""),
            )
        )
    return out


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
        top_k: int = 4,
    ) -> list[KnowledgeChunk]:
        chunks = _load_chunks()
        if not chunks:
            return []
        self._ensure_index(chunks)

        q_tokens = _expand_query_tokens(_tokenize(query))
        if module_key:
            q_tokens.extend(_tokenize(module_key.replace("-", " ")))

        pool: list[KnowledgeChunk] = chunks
        if module_key:
            scoped = [c for c in chunks if c["module_key"] == module_key]
            if scoped:
                pool = scoped

        if not self._index:
            return chunks[:top_k]

        id_to_idx = {cid: i for i, cid in enumerate(self._chunk_ids)}
        scored: list[tuple[float, KnowledgeChunk]] = []
        for ch in pool:
            idx = id_to_idx.get(ch["id"])
            if idx is None:
                continue
            score = self._index.score(q_tokens, idx)
            if module_key and ch["module_key"] == module_key:
                score += 1.5
            if module_key and not ch["module_key"]:
                score += 0.3
            scored.append((score, ch))

        scored.sort(key=lambda x: (-x[0], x[1]["id"]))
        if not scored and module_key:
            scored = [(1.0, c) for c in chunks if c["module_key"] == module_key]
        if not scored:
            scored = [(0.0, chunks[0])] if chunks else []

        seen: set[str] = set()
        out: list[KnowledgeChunk] = []
        for _, ch in scored:
            if ch["id"] in seen:
                continue
            seen.add(ch["id"])
            out.append(ch)
            if len(out) >= top_k:
                break
        return out


def format_context_block(chunks: list[KnowledgeChunk]) -> str:
    if not chunks:
        return "（知识库暂无匹配片段，请仅基于通用计科算法常识回答，勿编造具体题号与外链。）"
    lines = ["以下片段来自本平台《数据结构与算法》知识库，生成内容须与之保持一致，勿编造库外题号/URL："]
    for ch in chunks:
        lines.append(f"- [{ch['id']}] {ch['title']}：{ch['content']}")
    return "\n".join(lines)


retriever = KnowledgeRetriever()
