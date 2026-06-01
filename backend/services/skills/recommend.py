"""为评估 / OJ 受挫等场景推荐 SkillCard。"""

from __future__ import annotations

from services.knowledge.course_loader import chapter_id_for_module, load_manifest
from services.skills.models import SkillCardSummary, SkillRouteRequest
from services.skills.skill_context import skill_card_summary
from services.skills.skill_router import get_skill_router

_MODULE_TOPIC_HINT: dict[str, str] = {
    "dp": "动态规划",
    "binary-tree": "二叉树遍历",
    "graph": "图的 BFS",
    "linked-list": "链表",
    "array": "线性表",
    "hash-table": "二分 哈希",
    "greedy": "贪心",
    "backtracking": "回溯",
    "stack-queue": "栈 队列",
    "string": "字符串 滑动窗口",
    "two-pointers": "双指针",
    "monotonic-stack": "单调栈",
    "heap": "堆 优先队列",
    "union-find": "并查集 连通分量",
}


def build_route_request(
    *,
    module_key: str = "",
    knowledge_point: str = "",
    topic: str = "",
    error_pattern: str = "",
    trace_summary: str = "",
    profile_block: str = "",
    profile_summary: str = "",
    oj_verdict: str = "",
    consecutive_failures: int = 0,
    user_query: str = "",
) -> SkillRouteRequest:
    chapter_id = ""
    try:
        chapter_id = chapter_id_for_module(load_manifest(), module_key) or ""
    except Exception:
        pass
    topic_combined = topic or knowledge_point or _MODULE_TOPIC_HINT.get(module_key, "")
    return SkillRouteRequest(
        course_id="data_structures_algorithms",
        chapter_id=chapter_id,
        module_key=module_key,
        topic=topic_combined,
        user_query=user_query,
        profile_block=profile_block,
        profile_summary=profile_summary,
        oj_verdict=oj_verdict,
        error_pattern=error_pattern,
        trace_summary=trace_summary,
        consecutive_failures=consecutive_failures,
        top_k=3,
    )


def recommend_skill_cards(
    *,
    module_key: str = "",
    knowledge_point: str = "",
    topic: str = "",
    error_pattern: str = "",
    trace_summary: str = "",
    profile_block: str = "",
    profile_summary: str = "",
    oj_verdict: str = "",
    consecutive_failures: int = 0,
    user_query: str = "",
) -> list[SkillCardSummary]:
    req = build_route_request(
        module_key=module_key,
        knowledge_point=knowledge_point,
        topic=topic,
        error_pattern=error_pattern,
        trace_summary=trace_summary,
        profile_block=profile_block,
        profile_summary=profile_summary,
        oj_verdict=oj_verdict,
        consecutive_failures=consecutive_failures,
        user_query=user_query,
    )
    result = get_skill_router().route(req)
    out: list[SkillCardSummary] = []
    if result.primary:
        out.append(result.primary)
    seen = {s.id for s in out}
    for m in result.matches:
        if m.skill_id in seen:
            continue
        from services.skills.registry import get_registry

        card = get_registry().get(m.skill_id)
        if card:
            out.append(skill_card_summary(card))
            seen.add(m.skill_id)
    return out[:3]


def recommend_for_weak_modules(
    weak_module_keys: list[str],
    *,
    profile_block: str = "",
) -> list[SkillCardSummary]:
    merged: list[SkillCardSummary] = []
    seen: set[str] = set()
    for mk in weak_module_keys:
        for s in recommend_skill_cards(module_key=mk, profile_block=profile_block):
            if s.id not in seen:
                merged.append(s)
                seen.add(s.id)
    return merged[:5]
