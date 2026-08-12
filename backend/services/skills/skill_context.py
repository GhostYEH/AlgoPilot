"""将 SkillCard 格式化为资源生成 / 辅导 Agent 上下文。"""

from __future__ import annotations

from services.skills.models import SkillCard, SkillCardSummary


def skill_card_summary(card: SkillCard) -> SkillCardSummary:
    return SkillCardSummary(
        id=card.id,
        name=card.name,
        course_id=card.course_id,
        chapter_id=card.chapter_id,
        description=card.description[:280],
    )


def format_skill_prompt_block(card: SkillCard, *, resource_type: str = "") -> str:
    """供 Orchestrator 注入 focus_hint / 协作上下文。"""
    mistakes = "\n".join(
        f"- [{m.severity}] {m.text}" + (f"（线索：{m.detector_hint}）" if m.detector_hint else "")
        for m in card.common_mistakes[:6]
    )
    strat = card.resource_strategy.for_resource_type(resource_type) or card.resource_strategy.default
    if not strat:
        strat = "紧扣本章技能目标，禁止编造题号与外链。"

    hint_lines = "\n".join(
        f"  L{lv.level}：{lv.policy}" for lv in card.hint_policy.levels[:4]
    )
    trace = "；".join(card.trace_focus[:5]) or "（无特别 Trace 关注点）"
    eval_rules = "\n".join(f"- {r.rule_id}：{r.description}" for r in card.evaluation_rules[:4])

    return "\n".join(
        [
            f"【Learning SkillCard · {card.name} · id={card.id}】",
            f"课程 {card.course_id} · 章节 {card.chapter_id or '通用'}",
            f"策略摘要：{card.description[:200]}",
            f"常见误区：\n{mistakes}",
            f"本资源生成策略（{resource_type or '通用'}）：{strat}",
            f"辅导提示策略（禁止直接给完整可提交代码={card.hint_policy.forbid_full_solution}）：\n{hint_lines}",
            f"Trace 观察重点：{trace}",
            f"评估规则：\n{eval_rules}",
            f"推荐资源类型：{', '.join(card.recommended_resources[:8])}",
            f"推荐练习：{', '.join(card.recommended_problems[:6]) or '（见课内题单）'}",
        ]
    )


def skill_card_meta_payload(card: SkillCard, *, score: float = 0.0, reasons: list[str] | None = None) -> dict:
    return {
        "skill_id": card.id,
        "skill_name": card.name,
        "course_id": card.course_id,
        "chapter_id": card.chapter_id,
        "score": round(score, 2),
        "match_reasons": reasons or [],
        "recommended_resources": list(card.recommended_resources),
        "recommended_problems": list(card.recommended_problems),
    }
