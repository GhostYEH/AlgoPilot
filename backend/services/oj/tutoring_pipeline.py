"""OJ Trace 智能辅导闭环：SkillRouter · Memory · Mastery · 分层提示。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from models.db_models import User
from schemas.oj import OjTutoringPayload, RecommendedResourceHint, SkillCardBrief
from services.oj.error_patterns import ERROR_TYPE_LABELS, ErrorType, classify_error_type
from services.oj.problem_context import resolve_problem_context

_RESOURCE_LABELS: dict[str, str] = {
    "document": "概念文档",
    "mindmap": "思维导图",
    "exercises": "变式题单",
    "code_case": "代码沙盒",
    "trace_animation": "Trace 动画",
    "reading": "拓展阅读",
}


def _build_trace_summary(bug_step_index: int, title: str, analysis: str) -> str:
    snippet = (analysis or title or "").strip()[:400]
    return f"Step {bug_step_index}：{title}。{snippet}"


def _layered_hints(
    *,
    error_type: ErrorType,
    skill_id: str,
    hint_level: int,
    analysis: str,
) -> list[str]:
    hints: list[str] = []
    try:
        from services.skills.registry import SkillRegistry

        card = SkillRegistry().get(skill_id) if skill_id else None
        if card and card.hint_policy.levels:
            for lv in sorted(card.hint_policy.levels, key=lambda x: x.level):
                if lv.level <= hint_level:
                    hints.append(f"L{lv.level}：{lv.policy}")
            if hints:
                return hints[:3]
    except Exception:
        pass

    generic: dict[str, list[str]] = {
        "pointer_update_error": [
            "L1：在纸上画出当前步 head/curr/next 三个指针位置。",
            "L2：检查反转或删除时是否丢失 next 引用。",
            "L3：对照虚拟头结点写法，确认循环不变量。",
        ],
        "initialization_error": [
            "L1：写出 dp/数组 的定义：dp[i] 表示什么？",
            "L2：列出 n=0、n=1 的边界值，手填前两格。",
            "L3：检查循环起点是否使用了未初始化的状态。",
        ],
        "state_transition_error": [
            "L1：用一句话描述状态转移方程，不要写代码。",
            "L2：找一组手算样例，逐步验证转移方向。",
            "L3：确认是否混用了「选/不选」与「完全背包」遍历顺序。",
        ],
        "boundary_condition_error": [
            "L1：列出题目所有边界输入（空、单元素、最大值）。",
            "L2：对照 Trace 关键步，看是否在边界处提前返回。",
        ],
        "time_complexity_issue": [
            "L1：估算循环嵌套层数与 n 的关系。",
            "L2：检查是否存在重复子问题可记忆化。",
        ],
    }
    return generic.get(error_type, [
        "L1：阅读诊断摘要，定位 Step 附近变量变化。",
        f"L2：{analysis[:120] or '对照题目不变量检查逻辑。'}",
    ])[:3]


def _recommended_resources(
    skill_id: str,
    module_key: str,
    chapter_id: str,
    *,
    slug: str = "",
    error_type: ErrorType = "unknown",
) -> list[RecommendedResourceHint]:
    if slug == "reverse-linked-list" and error_type == "pointer_update_error":
        return [
            RecommendedResourceHint(
                resource_type="trace_animation",
                topic="指针更新动画",
                reason="逐帧对比 prev / curr / nxt，识别后继保存时机",
                chapter_id=chapter_id,
            ),
            RecommendedResourceHint(
                resource_type="exercises",
                topic="边界条件练习",
                reason="覆盖空链表、单节点与双节点反转",
                chapter_id=chapter_id,
            ),
            RecommendedResourceHint(
                resource_type="reading",
                topic="错题复盘卡",
                reason="记录断链步骤、循环不变量与修复顺序",
                chapter_id=chapter_id,
            ),
        ]

    out: list[RecommendedResourceHint] = []
    try:
        from services.skills.registry import SkillRegistry

        card = SkillRegistry().get(skill_id) if skill_id else None
        types = list(card.recommended_resources[:4]) if card else ["document", "exercises", "trace_animation"]
        topic = card.name if card else (module_key or "本章")
        for rt in types:
            out.append(
                RecommendedResourceHint(
                    resource_type=rt,
                    topic=topic,
                    reason=f"SkillCard 推荐 · {_RESOURCE_LABELS.get(rt, rt)}",
                    chapter_id=chapter_id,
                )
            )
    except Exception:
        out = [
            RecommendedResourceHint(
                resource_type="document",
                topic=module_key or "算法",
                reason="课程知识点复习",
                chapter_id=chapter_id,
            )
        ]
    return out


def _fallback_path_adjustment_hint(
    *,
    slug: str,
    error_type: ErrorType,
    module_key: str,
) -> str:
    if slug == "reverse-linked-list" and error_type == "pointer_update_error":
        return (
            "LearningPathAgent 建议：将“链表三指针循环不变量与断链风险”巩固节点"
            "前置到当前路径，完成 Trace 动画和空链表/单节点/双节点练习后，再继续后续模块。"
        )
    if error_type == "boundary_condition_error":
        return (
            f"LearningPathAgent 建议：在{module_key or '当前模块'}前插入边界条件巩固节点，"
            "完成空输入、单元素与极值用例后再继续原路径。"
        )
    if error_type == "recursion_base_case_error":
        return (
            "LearningPathAgent 建议：前置递归终止条件与区间定义巩固节点，"
            "通过最小规模用例后再恢复原学习路径。"
        )
    return ""


def apply_oj_tutoring(
    db: Session | None,
    user: User | None,
    *,
    slug: str,
    problem: dict[str, Any],
    bug_step_index: int = 0,
    diagnosis_title: str = "",
    detailed_analysis: str = "",
    edge_category: str = "",
    edge_verdict: str = "",
    judge_verdict: str = "",
    code: str = "",
    write_memory: bool = True,
) -> OjTutoringPayload:
    ctx = resolve_problem_context(slug, title=str(problem.get("title") or ""), meta=problem)
    trace_summary = _build_trace_summary(bug_step_index, diagnosis_title, detailed_analysis)
    error_type = classify_error_type(
        slug=slug,
        title=str(problem.get("title") or ""),
        analysis=detailed_analysis,
        trace_summary=trace_summary,
        edge_category=edge_category,
        verdict=edge_verdict or judge_verdict,
        code=code,
    )
    error_pattern_text = ERROR_TYPE_LABELS.get(error_type, error_type)

    matched_skill: SkillCardBrief | None = None
    skill_id = ctx.get("skill_id") or ""
    try:
        from services.skills.recommend import recommend_skill_cards

        cards = recommend_skill_cards(
            module_key=ctx.get("module_key") or "",
            topic=str(problem.get("title") or slug),
            error_pattern=error_pattern_text,
            trace_summary=trace_summary,
            oj_verdict=edge_verdict or judge_verdict or "WA",
            consecutive_failures=2,
        )
        if cards:
            c = cards[0]
            matched_skill = SkillCardBrief(
                id=c.id,
                name=c.name,
                chapter_id=c.chapter_id,
                description=c.description[:200],
            )
            skill_id = c.id
    except Exception:
        pass

    hint_level = 1
    repeated_failure = False
    if user and db:
        try:
            from services.memory.memory_service import MemoryService

            recent = MemoryService(db).list_recent(
                user.id,
                course_id=ctx["course_id"],
                chapter_id=ctx.get("chapter_id") or "",
                limit=10,
            )
            fails = sum(1 for m in recent if m.event_type in ("oj_submit_fail", "oj_diagnosis"))
            hint_level = min(3, 1 + fails // 2)
            repeated_failure = fails >= 2 or hint_level >= 2
        except Exception:
            pass

    layered = _layered_hints(
        error_type=error_type,
        skill_id=skill_id,
        hint_level=hint_level,
        analysis=detailed_analysis,
    )
    resources = _recommended_resources(
        skill_id,
        ctx.get("module_key") or "",
        ctx.get("chapter_id") or "",
        slug=slug,
        error_type=error_type,
    )

    memory_event_id: int | None = None
    mastery_summary = ""
    path_hint = _fallback_path_adjustment_hint(
        slug=slug,
        error_type=error_type,
        module_key=ctx.get("module_key") or "",
    )
    memory_recorded = False
    mastery_updated = False
    persona_updated = False
    persona_patch_summary = ""
    persona_patch_warning = ""

    if user and db and write_memory:
        try:
            from services.memory.memory_service import record_oj_diagnosis

            row = record_oj_diagnosis(
                db,
                user.id,
                problem_slug=slug,
                diagnosis={
                    "bug_step_index": bug_step_index,
                    "diagnosis_title": diagnosis_title,
                    "detailed_analysis": detailed_analysis,
                    "source": "oj_tutoring_pipeline",
                    "error_type": error_type,
                },
                module_key=ctx.get("module_key") or "",
                skill_id=skill_id,
                edge_category=edge_category,
                error_type=error_type,
            )
            memory_event_id = row.id
            memory_recorded = True
        except Exception:
            pass

        try:
            from services.agents.persona_learning import apply_oj_diagnosis_patch

            patch_result = apply_oj_diagnosis_patch(
                db,
                user.id,
                course_id=ctx["course_id"],
                chapter_id=ctx.get("chapter_id") or "",
                skill_id=skill_id,
                problem_slug=slug,
                error_type=error_type,
                error_pattern_label=error_pattern_text,
                trace_summary=trace_summary,
                hint_level=hint_level,
                module_key=ctx.get("module_key") or "",
                repeated_failure=repeated_failure,
                mastery_delta=-1,
            )
            persona_updated = patch_result.updated
            persona_patch_summary = patch_result.summary
            persona_patch_warning = patch_result.warning
        except Exception as exc:
            persona_updated = False
            persona_patch_warning = f"画像 patch 失败：{exc}"

        overview = None
        try:
            from services.mastery.mastery_service import MasteryService

            overview = MasteryService(db).recalculate(
                user.id,
                course_id=ctx["course_id"],
                chapter_id=ctx.get("chapter_id") or "",
            )
            mastery_summary = (
                f"掌握度 {overview.overall_score}（{overview.overall_level}）"
                f"{' · 章节已更新' if ctx.get('chapter_id') else ''}"
            )
            mastery_updated = True
            if overview.overall_score < 45:
                path_hint = "LearningPathAgent：建议插入巩固节点后再进入下一章"
            elif overview.overall_score >= 60:
                path_hint = "掌握度达标，可继续路径规划中的下一模块"
            else:
                path_hint = "建议完成推荐资源与变式题后再前进"
        except Exception:
            mastery_summary = "掌握度重算已排队（详见我的学习）"

        if overview is not None:
            try:
                from services.events.event_bus import event_bus

                event_bus.publish(
                    db,
                    event_type="on_mastery_recalculated",
                    user_id=user.id,
                    chapter_id=ctx.get("chapter_id") or "",
                    payload={
                        "module_key": ctx.get("module_key") or "",
                        "problem_slug": slug,
                        "error_type": error_type,
                        "error_pattern": error_pattern_text,
                        "mastery_score": overview.overall_score,
                        "mastery_level": overview.overall_level,
                    },
                )
            except Exception:
                pass

    return OjTutoringPayload(
        course_id=ctx["course_id"],
        chapter_id=ctx.get("chapter_id") or "",
        skill_id=skill_id,
        module_key=ctx.get("module_key") or "",
        matched_skill=matched_skill,
        error_pattern=error_type,
        error_pattern_label=error_pattern_text,
        bug_step_index=bug_step_index,
        trace_summary=trace_summary[:2000],
        hint_level=hint_level,
        layered_hints=layered,
        recommended_resources=resources,
        memory_event_id=memory_event_id,
        mastery_update_summary=mastery_summary,
        path_adjustment_hint=path_hint,
        memory_recorded=memory_recorded,
        mastery_updated=mastery_updated,
        persona_updated=persona_updated,
        persona_patch_summary=persona_patch_summary,
        persona_patch_warning=persona_patch_warning,
    )
