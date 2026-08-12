"""SkillRouter：根据学习情境匹配最相关的 SkillCard。"""

from __future__ import annotations

import re

from services.skills.models import (
    SkillCard,
    SkillRouteMatch,
    SkillRouteRequest,
    SkillRouteResponse,
)
from services.skills.registry import SkillRegistry, get_registry
from services.skills.skill_context import skill_card_summary


def _haystack(req: SkillRouteRequest) -> str:
    return " ".join(
        [
            req.topic,
            req.user_query,
            req.error_pattern,
            req.trace_summary,
            req.profile_summary,
            req.profile_block,
            req.module_key,
            req.chapter_id,
        ]
    ).lower()


def _score_card(card: SkillCard, req: SkillRouteRequest, text: str) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []

    if req.chapter_id and req.chapter_id == card.chapter_id:
        score += 42.0
        reasons.append(f"章节匹配 {req.chapter_id}")

    if req.module_key and req.module_key in card.triggers.module_keys:
        score += 38.0
        reasons.append(f"模块匹配 {req.module_key}")

    for cid in card.triggers.chapter_ids:
        if cid and cid == req.chapter_id:
            score += 25.0
            reasons.append(f"触发章节 {cid}")

    for kw in card.triggers.keywords:
        k = kw.lower().strip()
        if len(k) >= 2 and k in text:
            score += 14.0
            reasons.append(f"关键词「{kw}」")

    for pat in card.triggers.error_patterns:
        p = pat.lower().strip()
        if len(p) >= 2 and (p in text or p in req.error_pattern.lower()):
            score += 20.0
            reasons.append(f"错误模式「{pat}」")

    if req.oj_verdict and req.oj_verdict.upper() in {v.upper() for v in card.triggers.oj_verdicts}:
        score += 8.0
        reasons.append(f"判题结果 {req.oj_verdict}")

    min_fail = card.triggers.min_consecutive_failures
    if min_fail > 0 and req.consecutive_failures >= min_fail:
        score += 12.0
        reasons.append(f"连续失败≥{min_fail}")

    # 技能卡 id 与 topic 子串（如 dp-state-design 与「动态规划」）
    id_tokens = re.findall(r"[a-z]+", card.id.lower())
    for tok in id_tokens:
        if len(tok) >= 3 and tok in text:
            score += 4.0

    # 画像薄弱点
    for mk in card.triggers.module_keys:
        if mk and mk in req.profile_block:
            score += 6.0
            reasons.append(f"画像提及模块 {mk}")

    return score, reasons


class SkillRouter:
    def __init__(self, registry: SkillRegistry | None = None) -> None:
        self._registry = registry or get_registry()

    def route(self, req: SkillRouteRequest) -> SkillRouteResponse:
        text = _haystack(req)
        pool = self._registry.list_cards(course_id=req.course_id or "")
        if not pool:
            pool = self._registry.list_cards()
        if req.module_key:
            compatible = [
                card for card in pool if req.module_key in card.triggers.module_keys
            ]
            if compatible:
                pool = compatible

        scored: list[tuple[float, SkillCard, list[str]]] = []
        for card in pool:
            s, reasons = _score_card(card, req, text)
            if s > 0:
                scored.append((s, card, reasons))

        scored.sort(key=lambda x: (-x[0], x[1].id))
        top = scored[: req.top_k]

        matches = [
            SkillRouteMatch(
                skill_id=card.id,
                name=card.name,
                score=round(s, 2),
                reasons=reasons[:6],
            )
            for s, card, reasons in top
        ]

        primary_card = top[0][1] if top else None
        primary_summary = skill_card_summary(primary_card) if primary_card else None

        return SkillRouteResponse(
            primary=primary_summary,
            matches=matches,
            skill_card=primary_card,
        )


_router: SkillRouter | None = None


def get_skill_router() -> SkillRouter:
    global _router
    if _router is None:
        _router = SkillRouter()
    return _router
