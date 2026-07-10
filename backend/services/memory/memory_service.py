"""StudentLearningMemory 写入与查询。"""

from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from models.db_models import StudentLearningMemory
from services.memory.schemas import MemoryEventInput, MemoryEventRecord

_EVENT_LABELS: dict[str, str] = {
    "oj_submit_fail": "OJ 提交未通过",
    "oj_submit_success": "OJ 提交通过",
    "oj_diagnosis": "AI 深度诊断",
    "trace_diagnosis": "Trace 轨迹诊断",
    "evaluation_struggle": "连续作答受挫",
    "path_adjusted": "路径动态重排",
    "resource_complete": "资源学习完成",
    "quiz_complete": "练习测验完成",
    "section_done": "小节学习完成",
    "skill_recommended": "推荐技能卡",
    "gamified_practice_complete": "游戏化练习完成",
}

_MODULE_TO_CHAPTER: dict[str, str] = {
    "dp": "ch11-dynamic-programming",
    "graph": "ch06-graph",
    "binary-tree": "ch05-tree-binary-tree",
    "linked-list": "ch02-linear-list",
    "array": "ch02-linear-list",
    "hash-table": "ch07-search",
    "greedy": "ch10-greedy",
    "backtracking": "ch12-backtracking",
}


class MemoryService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def record_event(
        self,
        user_id: int,
        payload: MemoryEventInput,
    ) -> MemoryEventRecord:
        row = StudentLearningMemory(
            user_id=user_id,
            course_id=payload.course_id or "data_structures_algorithms",
            chapter_id=payload.chapter_id or "",
            skill_id=payload.skill_id or "",
            problem_slug=payload.problem_slug or "",
            event_type=payload.event_type,
            observed_error_pattern=(payload.observed_error_pattern or "")[:500],
            trace_summary=(payload.trace_summary or "")[:2000],
            failed_strategy=(payload.failed_strategy or "")[:500],
            successful_hint=(payload.successful_hint or "")[:500],
            mastery_delta=int(payload.mastery_delta),
            evidence_json=dict(payload.evidence_json or {}),
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return MemoryEventRecord.from_orm_row(row)

    def list_recent(
        self,
        user_id: int,
        *,
        course_id: str = "",
        chapter_id: str = "",
        skill_id: str = "",
        limit: int = 20,
    ) -> list[MemoryEventRecord]:
        q = select(StudentLearningMemory).where(StudentLearningMemory.user_id == user_id)
        if course_id:
            q = q.where(StudentLearningMemory.course_id == course_id)
        if chapter_id:
            q = q.where(StudentLearningMemory.chapter_id == chapter_id)
        if skill_id:
            q = q.where(StudentLearningMemory.skill_id == skill_id)
        q = q.order_by(desc(StudentLearningMemory.created_at)).limit(min(limit, 100))
        rows = self._db.scalars(q).all()
        return [MemoryEventRecord.from_orm_row(r) for r in rows]

    def aggregate_weak_patterns(
        self,
        user_id: int,
        *,
        course_id: str = "data_structures_algorithms",
        limit: int = 5,
    ) -> list[str]:
        rows = self.list_recent(user_id, course_id=course_id, limit=50)
        counts: dict[str, int] = {}
        for r in rows:
            key = (r.observed_error_pattern or r.failed_strategy or "").strip()
            if not key or len(key) < 4:
                continue
            counts[key] = counts.get(key, 0) + 1
        ranked = sorted(counts.items(), key=lambda x: -x[1])
        return [k[:80] for k, _ in ranked[:limit]]



def resolve_chapter_id(module_key: str = "", chapter_id: str = "") -> str:
    if chapter_id:
        return chapter_id
    if module_key:
        try:
            from services.knowledge.course_loader import chapter_id_for_module, load_manifest

            return chapter_id_for_module(load_manifest(), module_key) or ""
        except Exception:
            return _MODULE_TO_CHAPTER.get(module_key, "")
    return ""


def resolve_skill_id_for_context(
    *,
    module_key: str = "",
    topic: str = "",
    error_pattern: str = "",
    trace_summary: str = "",
) -> str:
    try:
        from services.skills.recommend import recommend_skill_cards

        cards = recommend_skill_cards(
            module_key=module_key,
            topic=topic,
            error_pattern=error_pattern,
            trace_summary=trace_summary,
            consecutive_failures=2,
        )
        if cards:
            return cards[0].id
    except Exception:
        pass
    return ""


def record_oj_submit_failure(
    db: Session,
    user_id: int,
    *,
    problem_slug: str,
    verdict: str,
    message: str = "",
    module_key: str = "",
    consecutive_failures: int = 1,
) -> MemoryEventRecord | None:
    if verdict == "AC":
        return None
    pattern = _verdict_to_pattern(verdict, message)
    skill_id = resolve_skill_id_for_context(
        module_key=module_key,
        error_pattern=pattern,
        topic=problem_slug,
    )
    svc = MemoryService(db)
    return svc.record_event(
        user_id,
        MemoryEventInput(
            event_type="oj_submit_fail",
            problem_slug=problem_slug,
            chapter_id=resolve_chapter_id(module_key),
            skill_id=skill_id,
            observed_error_pattern=pattern,
            failed_strategy=message[:500] if message else verdict,
            mastery_delta=-1,
            evidence_json={
                "verdict": verdict,
                "consecutive_failures": consecutive_failures,
                "persona_dimension": "coding_ability",
            },
        ),
    )


def record_oj_diagnosis(
    db: Session,
    user_id: int,
    *,
    problem_slug: str,
    diagnosis: dict,
    module_key: str = "",
    skill_id: str = "",
    edge_category: str = "",
    error_type: str = "",
) -> MemoryEventRecord:
    bug_idx = diagnosis.get("bug_step_index", 0)
    title = str(diagnosis.get("diagnosis_title") or "")
    analysis = str(diagnosis.get("detailed_analysis") or "")
    trace_summary = f"Step {bug_idx}：{title}。{analysis[:400]}"
    pattern = _infer_pattern_from_diagnosis(analysis, edge_category)
    err_type = error_type or str(diagnosis.get("error_type") or "")
    try:
        from services.agents.persona_learning import dimensions_for_error_type

        persona_dims = dimensions_for_error_type(err_type) if err_type else ["error_preference"]
    except Exception:
        persona_dims = ["error_preference"]
    if not skill_id:
        skill_id = resolve_skill_id_for_context(
            module_key=module_key,
            error_pattern=pattern,
            trace_summary=trace_summary,
            topic=problem_slug,
        )
    svc = MemoryService(db)
    return svc.record_event(
        user_id,
        MemoryEventInput(
            event_type="oj_diagnosis",
            problem_slug=problem_slug,
            chapter_id=resolve_chapter_id(module_key),
            skill_id=skill_id,
            observed_error_pattern=pattern or err_type,
            trace_summary=trace_summary[:2000],
            evidence_json={
                "bug_step_index": bug_idx,
                "diagnosis_title": title,
                "diagnosis_source": diagnosis.get("source", ""),
                "edge_category": edge_category,
                "error_type": err_type,
                "persona_dimension": persona_dims[0] if persona_dims else "error_preference",
                "persona_dimensions": persona_dims,
            },
        ),
    )


def record_evaluation_struggle(
    db: Session,
    user_id: int,
    *,
    module_key: str,
    knowledge_point: str,
    verdict: str,
    error_pattern: str,
    consecutive_failures: int,
    skill_ids: list[str] | None = None,
) -> MemoryEventRecord:
    skill_id = (skill_ids or [None])[0] or ""
    if not skill_id:
        skill_id = resolve_skill_id_for_context(
            module_key=module_key,
            topic=knowledge_point,
            error_pattern=error_pattern,
        )
    svc = MemoryService(db)
    return svc.record_event(
        user_id,
        MemoryEventInput(
            event_type="evaluation_struggle",
            chapter_id=resolve_chapter_id(module_key),
            skill_id=skill_id or "",
            observed_error_pattern=error_pattern or f"连续{consecutive_failures}次{verdict}",
            failed_strategy=knowledge_point or module_key,
            mastery_delta=-2,
            evidence_json={
                "verdict": verdict,
                "consecutive_failures": consecutive_failures,
                "module_key": module_key,
                "recommended_skill_ids": skill_ids or [],
                "persona_dimension": "grit_level",
            },
        ),
    )


def _verdict_to_pattern(verdict: str, message: str) -> str:
    v = (verdict or "").upper()
    msg = (message or "").lower()
    if v == "TLE":
        return "超时 TLE，可能复杂度过高或死循环"
    if v == "RE":
        return "运行时错误 RE，常见空指针/越界/递归过深"
    if v == "CE":
        return "编译错误 CE"
    if "边界" in msg or "boundary" in msg:
        return "边界条件错误"
    if "初始化" in msg:
        return "初始化错误"
    return f"答案错误 WA（{message[:60]}）" if message else "答案错误 WA"


def _infer_pattern_from_diagnosis(analysis: str, edge_category: str) -> str:
    text = f"{analysis} {edge_category}".lower()
    if "边界" in text or "empty" in text or "空" in text:
        return "边界条件问题"
    if "初始化" in text or "下标" in text:
        return "初始化或下标错误"
    if "递归" in text or "栈" in text:
        return "递归/栈相关问题"
    if "指针" in text or "next" in text:
        return "指针移动错误"
    if "循环" in text or "死循环" in text:
        return "循环未收敛或逻辑未推进"
    return "逻辑偏离题意"


def record_gamified_practice(
    db: Session,
    user_id: int,
    *,
    game_id: str,
    level: str,
    module_key: str = "",
    success: bool = True,
    score: int = 0,
    attempts: int = 1,
    time_spent_seconds: int = 0,
    evidence_text: str = "",
) -> MemoryEventRecord:
    chapter_id = resolve_chapter_id(module_key)
    skill_id = resolve_skill_id_for_context(
        module_key=module_key,
        topic=game_id,
    )
    delta = 1 if success else 0
    svc = MemoryService(db)
    return svc.record_event(
        user_id,
        MemoryEventInput(
            event_type="gamified_practice_complete",
            course_id="data_structures_algorithms",
            chapter_id=chapter_id,
            skill_id=skill_id,
            problem_slug=f"game:{game_id}:{level}",
            trace_summary=(evidence_text or f"游戏 {game_id} 关卡 {level} {'通关' if success else '未通关'}")[:2000],
            mastery_delta=delta,
            evidence_json={
                "game_id": game_id,
                "level": level,
                "module_key": module_key,
                "success": success,
                "score": score,
                "attempts": attempts,
                "time_spent_seconds": time_spent_seconds,
                "evidence_text": evidence_text,
                "persona_dimension": "knowledge_base",
            },
        ),
    )


def record_section_completion(
    db: Session,
    user_id: int,
    *,
    module_key: str,
    section_id: str,
) -> MemoryEventRecord:
    """幂等记录课程小节完成，供画像、掌握度与效果分析共同使用。"""
    problem_slug = f"section:{module_key}:{section_id}"
    existing = db.scalar(
        select(StudentLearningMemory)
        .where(
            StudentLearningMemory.user_id == user_id,
            StudentLearningMemory.event_type == "section_done",
            StudentLearningMemory.problem_slug == problem_slug,
        )
        .order_by(desc(StudentLearningMemory.created_at))
        .limit(1)
    )
    if existing is not None:
        return MemoryEventRecord.from_orm_row(existing)

    chapter_id = resolve_chapter_id(module_key)
    return MemoryService(db).record_event(
        user_id,
        MemoryEventInput(
            event_type="section_done",
            chapter_id=chapter_id,
            problem_slug=problem_slug,
            trace_summary=f"完成 {module_key} 模块小节 {section_id}",
            mastery_delta=1,
            evidence_json={
                "module_key": module_key,
                "section_id": section_id,
                "persona_dimension": "knowledge_base",
            },
        ),
    )
