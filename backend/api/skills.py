"""Learning SkillCard API。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from schemas.skills import (
    SkillCardSummary,
    SkillRouteMatch,
    SkillRouteRequest,
    SkillRouteResponse,
)
from services.skills.models import SkillCard, SkillRouteRequest as SvcSkillRouteRequest
from services.skills.registry import get_registry
from services.skills.skill_context import skill_card_summary
from services.skills.skill_router import get_skill_router

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", response_model=list[SkillCardSummary])
def list_skills(
    course_id: str = "data_structures_algorithms",
) -> list[SkillCardSummary]:
    reg = get_registry()
    return [
        SkillCardSummary.model_validate(skill_card_summary(c).model_dump())
        for c in reg.list_cards(course_id=course_id)
    ]


@router.get("/{skill_id}", response_model=SkillCard)
def get_skill(skill_id: str) -> SkillCard:
    card = get_registry().get(skill_id)
    if card is None:
        raise HTTPException(status_code=404, detail=f"技能卡不存在: {skill_id}")
    return card


@router.post("/route", response_model=SkillRouteResponse)
def route_skill(body: SkillRouteRequest) -> SkillRouteResponse:
    """根据课程章节、画像、OJ 错误等情境匹配技能卡。"""
    result = get_skill_router().route(SvcSkillRouteRequest(**body.model_dump()))
    primary = (
        SkillCardSummary.model_validate(result.primary.model_dump())
        if result.primary
        else None
    )
    matches = [
        SkillRouteMatch(
            skill_id=m.skill_id,
            name=m.name,
            score=m.score,
            reasons=m.reasons,
        )
        for m in result.matches
    ]
    skill_full = result.skill_card.model_dump() if result.skill_card else None
    return SkillRouteResponse(primary=primary, matches=matches, skill_card=skill_full)
