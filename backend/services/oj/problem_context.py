"""OJ 题目与课程章节 / SkillCard 映射。"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

_DEFAULT_COURSE = "data_structures_algorithms"

_SLUG_MODULE_HINTS: dict[str, str] = {
    "two-sum": "hash-table",
    "climbing-stairs": "dp",
    "unique-paths": "dp",
    "unique-paths-ii": "dp",
    "reverse-linked-list": "linked-list",
    "merge-two-sorted-lists": "linked-list",
    "remove-nth-node-from-end-of-list": "linked-list",
    "binary-tree": "binary-tree",
    "valid-parentheses": "stack-queue",
    "trapping-rain-water": "monotonic-stack",
}


@lru_cache(maxsize=1)
def _concept_graph_problems() -> dict[str, dict[str, str]]:
    path = Path(__file__).resolve().parents[2] / "knowledge_base" / "concept_graph.json"
    out: dict[str, dict[str, str]] = {}
    if not path.is_file():
        return out
    try:
        graph = json.loads(path.read_text(encoding="utf-8"))
        for c in graph.get("concepts") or []:
            slug = c.get("slug")
            if slug:
                out[str(slug)] = {
                    "module_key": str(c.get("module_key") or ""),
                    "concept_id": str(c.get("id") or ""),
                }
    except Exception:
        pass
    return out


def _infer_module_key(slug: str, title: str = "") -> str:
    if slug in _SLUG_MODULE_HINTS:
        return _SLUG_MODULE_HINTS[slug]
    cg = _concept_graph_problems().get(slug)
    if cg and cg.get("module_key"):
        return cg["module_key"]
    combined = f"{slug} {title}".lower()
    if re.search(r"linked|list|node|reverse", combined):
        return "linked-list"
    if re.search(r"tree|binary", combined):
        return "binary-tree"
    if re.search(r"graph|bfs|dfs", combined):
        return "graph"
    if re.search(r"climb|unique.*path|dp|背包|coin", combined):
        return "dp"
    if re.search(r"stack|queue|parentheses", combined):
        return "stack-queue"
    if re.search(r"hash|two-sum", combined):
        return "hash-table"
    return ""


def resolve_problem_context(slug: str, *, title: str = "", meta: dict[str, Any] | None = None) -> dict[str, str]:
    """返回 course_id, chapter_id, module_key, skill_id（可为空）。"""
    meta = meta or {}
    course_id = str(meta.get("course_id") or _DEFAULT_COURSE)
    module_key = str(meta.get("module_key") or _infer_module_key(slug, title))
    chapter_id = str(meta.get("chapter_id") or "")
    skill_id = str(meta.get("skill_id") or "")

    if module_key and not chapter_id:
        try:
            from services.knowledge.course_loader import chapter_id_for_module, load_manifest

            chapter_id = chapter_id_for_module(load_manifest(course_id), module_key) or ""
        except Exception:
            pass

    if not skill_id and module_key:
        try:
            from services.skills.recommend import recommend_skill_cards

            cards = recommend_skill_cards(module_key=module_key, topic=title or slug)
            if cards:
                skill_id = cards[0].id
        except Exception:
            pass

    return {
        "course_id": course_id,
        "chapter_id": chapter_id,
        "module_key": module_key,
        "skill_id": skill_id,
    }
