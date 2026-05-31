"""学习事件 handler 注册与闭环编排。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from services.events.event_bus import EventBus
from services.events.event_models import LearningEvent


def register_handlers(bus: EventBus) -> None:
    bus.subscribe("on_oj_submission_failed", "OjFailurePipeline", handle_oj_submission_failed)
    bus.subscribe("on_oj_submission_accepted", "OjAcceptPipeline", handle_oj_submission_accepted)
    bus.subscribe("on_resource_generated", "ResourcePipeline", handle_resource_generated)
    bus.subscribe("on_mastery_recalculated", "MasteryPathPipeline", handle_mastery_recalculated)
    bus.subscribe("on_trace_diagnosed", "TraceMemoryPipeline", handle_trace_diagnosed)
    bus.subscribe("on_path_adjusted", "PathLogPipeline", handle_path_adjusted)
    bus.subscribe("on_profile_updated", "ProfileLogPipeline", handle_profile_updated)
    bus.subscribe("on_quiz_completed", "QuizMemoryPipeline", handle_quiz_completed)


def handle_oj_submission_failed(db: Session | None, event: LearningEvent) -> None:
    """OJ 失败：StudentMemory → Mastery 重算 → SkillCard 推荐。"""
    payload = event.payload
    slug = str(payload.get("problem_slug") or "")
    verdict = str(payload.get("verdict") or "WA")
    message = str(payload.get("message") or "")
    module_key = str(payload.get("module_key") or "")

    memory_id = None
    if db is not None:
        from services.memory.memory_service import record_oj_submit_failure

        row = record_oj_submit_failure(
            db,
            event.user_id,
            problem_slug=slug,
            verdict=verdict,
            message=message,
            module_key=module_key,
        )
        if row:
            memory_id = row.id
            event.skill_id = event.skill_id or row.skill_id
            event.chapter_id = event.chapter_id or row.chapter_id
    event.log(
        "StudentMemory",
        "record_event",
        f"错因记忆已写入 memory_id={memory_id}",
        status="done",
    )

    try:
        from services.skills.recommend import recommend_skill_cards

        cards = recommend_skill_cards(
            module_key=module_key,
            topic=slug,
            error_pattern=str(payload.get("error_pattern") or message),
            oj_verdict=verdict,
            consecutive_failures=int(payload.get("consecutive_failures") or 1),
        )
        if cards:
            event.payload["recommended_skill_cards"] = [
                {"id": c.id, "name": c.name, "chapter_id": c.chapter_id} for c in cards[:3]
            ]
            event.skill_id = event.skill_id or cards[0].id
            event.log(
                "SkillRouter",
                "recommend",
                f"推荐 SkillCard：{cards[0].name}",
                status="done",
            )
        else:
            event.log("SkillRouter", "recommend", "暂无匹配 SkillCard", status="warn")
    except Exception as exc:
        event.log("SkillRouter", "recommend", str(exc), status="warn")

    if db is not None:
        try:
            from services.knowledge.course_loader import chapter_id_for_module, load_manifest

            manifest = load_manifest(event.course_id)
            cid = event.chapter_id or chapter_id_for_module(manifest, module_key) or ""
            event.chapter_id = cid
            event.payload.setdefault("module_key", module_key)
            handle_mastery_recalculated(db, event)
        except Exception as exc:
            event.log("MasteryAgent", "pipeline", str(exc), status="warn")


def handle_oj_submission_accepted(db: Session | None, event: LearningEvent) -> None:
    payload = event.payload
    slug = str(payload.get("problem_slug") or "")
    if db is not None:
        try:
            from services.memory.memory_service import MemoryService
            from services.memory.schemas import MemoryEventInput

            MemoryService(db).record_event(
                event.user_id,
                MemoryEventInput(
                    event_type="oj_submit_success",
                    problem_slug=slug,
                    chapter_id=event.chapter_id,
                    mastery_delta=1,
                    evidence_json={"verdict": "AC", "persona_dimension": "coding_ability"},
                ),
            )
            event.log("StudentMemory", "record_event", f"AC 记录：{slug}", status="done")
        except Exception:
            event.log("StudentMemory", "record_event", "AC 记忆写入跳过", status="warn")


def handle_resource_generated(db: Session | None, event: LearningEvent) -> None:
    """资源生成后记录校验与安全 Agent 日志。"""
    payload = event.payload
    resource_type = str(payload.get("resource_type") or "")
    title = str(payload.get("title") or "")
    verified = payload.get("verified")
    safety_passed = payload.get("safety_passed", True)

    for entry in payload.get("agent_logs") or []:
        if not isinstance(entry, dict):
            continue
        agent = str(entry.get("agent") or "Agent")
        if agent not in (
            "ContentVerifierAgent",
            "SafetyAgent",
            "ContentSafety",
            "KnowledgeRetriever",
        ):
            continue
        event.log(
            agent,
            str(entry.get("action") or "collaborate"),
            str(entry.get("detail") or ""),
            status=str(entry.get("status") or "done"),
        )

    event.log(
        "ContentVerifierAgent",
        "verify_summary",
        "校验通过" if verified else "草稿/未完全校验",
        status="done" if verified else "warn",
    )
    event.log(
        "SafetyAgent",
        "audit_summary",
        "安全审查通过" if safety_passed else "安全审查告警",
        status="done" if safety_passed else "warn",
    )
    event.log(
        "Orchestrator",
        "resource_persisted",
        f"{resource_type} · {title}",
        status="done",
    )


def handle_mastery_recalculated(db: Session | None, event: LearningEvent) -> None:
    """掌握度变化后由 LearningPathAgent 判断是否插入巩固节点。"""
    score = event.payload.get("mastery_score")
    if score is None and db is not None:
        try:
            from services.mastery.mastery_service import MasteryService

            overview = MasteryService(db).recalculate(
                event.user_id,
                course_id=event.course_id,
                chapter_id=event.chapter_id,
                modules=event.payload.get("modules") or [],
            )
            score = overview.overall_score
            event.payload["mastery_score"] = score
            event.payload["mastery_level"] = overview.overall_level
            event.log(
                "MasteryAgent",
                "recalculate",
                f"掌握度 {score}（{overview.overall_level}）",
                status="done",
            )
        except Exception as exc:
            event.log("MasteryAgent", "recalculate", str(exc), status="error")
            score = 50
    score = int(score or 50)
    module_key = str(event.payload.get("module_key") or "")
    chapter_id = event.chapter_id or str(event.payload.get("chapter_id") or "")

    from services.agents.learning_path import LearningPathAgent

    path_agent = LearningPathAgent()
    if score < 45:
        rem = path_agent.plan_remediation_for_struggle(
            knowledge_point=str(event.payload.get("knowledge_point") or chapter_id),
            module_key=module_key,
            error_pattern=str(event.payload.get("error_pattern") or "掌握度偏低"),
        )
        event.payload["path_adjustment"] = rem
        event.log(
            "LearningPathAgent",
            "suggest_remediation",
            rem.get("reason") or rem.get("label") or "建议插入巩固节点",
            status="warn",
        )
        if db is not None and rem.get("module_key"):
            try:
                from models.db_models import LearningPathPlan

                plan = db.get(LearningPathPlan, event.user_id)
                if plan and rem["module_key"] not in (plan.ordered_keys or []):
                    event.log(
                        "LearningPathAgent",
                        "path_flag",
                        f"建议优先巩固 {rem.get('label', rem['module_key'])}",
                        status="done",
                    )
            except Exception:
                pass
    elif score >= 60:
        event.log(
            "LearningPathAgent",
            "path_advance",
            f"掌握度 {score} 达标，可进入下一章节",
            status="done",
        )
    else:
        event.log(
            "LearningPathAgent",
            "path_hold",
            f"掌握度 {score}，建议完成推荐练习后再前进",
            status="done",
        )


def handle_trace_diagnosed(db: Session | None, event: LearningEvent) -> None:
    if db is None:
        event.log("StudentMemory", "skip", "无数据库会话", status="warn")
        return
    if event.payload.get("memory_written"):
        mid = event.payload.get("memory_event_id")
        event.log(
            "StudentMemory",
            "record_diagnosis",
            f"Trace 诊断已由 tutoring pipeline 写入 memory_id={mid}",
            status="done",
        )
        return
    from services.memory.memory_service import record_oj_diagnosis

    diagnosis = event.payload.get("diagnosis") or {}
    slug = str(event.payload.get("problem_slug") or "")
    record_oj_diagnosis(
        db,
        event.user_id,
        problem_slug=slug,
        diagnosis=diagnosis if isinstance(diagnosis, dict) else {},
        edge_category=str(event.payload.get("edge_category") or ""),
    )
    event.log("StudentMemory", "record_diagnosis", f"Trace 诊断摘要已写入 · {slug}", status="done")


def handle_path_adjusted(db: Session | None, event: LearningEvent) -> None:
    summary = str(event.payload.get("summary") or "")
    remediation = event.payload.get("remediation_inserted")
    event.log(
        "LearningPathAgent",
        "path_adjusted",
        summary or ("已插入巩固节点" if remediation else "路径已更新"),
        status="done",
    )


def handle_profile_updated(db: Session | None, event: LearningEvent) -> None:
    event.log(
        "ProfilingAgent",
        "profile_sync",
        str(event.payload.get("message") or "画像已更新"),
        status="done",
    )


def handle_quiz_completed(db: Session | None, event: LearningEvent) -> None:
    if db is None:
        return
    from services.memory.memory_service import MemoryService
    from services.memory.schemas import MemoryEventInput

    MemoryService(db).record_event(
        event.user_id,
        MemoryEventInput(
            event_type="quiz_complete",
            chapter_id=event.chapter_id,
            skill_id=event.skill_id,
            observed_error_pattern=str(event.payload.get("error_pattern") or ""),
            mastery_delta=int(event.payload.get("mastery_delta") or 0),
            evidence_json=dict(event.payload.get("evidence_json") or {}),
        ),
    )
    event.log("StudentMemory", "quiz_complete", "测验完成记忆已写入", status="done")
