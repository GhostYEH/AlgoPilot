"""编排层：所有 AI 能力统一入口，禁止 API 直连 LLM。"""

from __future__ import annotations

import asyncio
import contextvars
import json
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models.db_models import GeneratedResource, LearningPathPlan, StudentProfile, User
from schemas.ai_tutor import AiTutorChatRequest
from schemas.oj_assistant import OjAssistantRequest
from schemas.evaluation import (
    AgentLogItem,
    LearningEvaluationResponse,
    OjStruggleEvaluationRequest,
    OjStruggleEvaluationResponse,
    PersonaLearningPatchRequest,
)
from schemas.learning_path import LearningPathPlanResponse, LearningPathReplanRequest, PathStepItem
from schemas.persona import ChatHistoryItem, PersonaDimensions, PersonaProfileResponse
from schemas.resources import (
    CORE_RESOURCE_PIPELINE,
    PARALLEL_PHASES,
    RESOURCE_AGENT_META,
    GeneratedResourceItem,
    ResourceGenerateRequest,
    ResourceType,
)
from services.agents.evaluation import evaluation_agent
from services.agents.learning_path import LearningPathAgent
from services.agents.oj_assistant import OjAssistantAgent
from services.agents.persona import PersonaAgent
from services.agents.persona_learning import apply_learning_patch
from services.agents.resources import AgentOutputError
from services.agents.registry import agent_for_resource, list_agents
from services.agents.tutor import TutorAgent
from services.orchestrator.persona_fingerprint import (
    find_latest_resource,
    fingerprint_for_resource,
    save_fingerprint,
    should_skip_generation,
)
from services.orchestrator.pipeline_context import PipelineContext
from services.agents.template_fallback import (
    GENERATED_BY as TEMPLATE_FALLBACK_AGENT,
    is_llm_related_error,
    llm_unavailable_reason,
)
from services.orchestrator.fallback_workflow import fallback_resource_workflow
from services.orchestrator.workflow import resource_workflow
from services.safety.content_filter import content_filter

logger = logging.getLogger(__name__)

# each request gets its own fallback state via contextvars (no race on singleton)
_persona_chat_fallback_var: contextvars.ContextVar[dict] = contextvars.ContextVar(
    '_persona_chat_fallback', default={'fallback': False, 'reason': ''}
)

_persona = PersonaAgent()
_tutor = TutorAgent()
_oj = OjAssistantAgent()
_path = LearningPathAgent()


def _dimension_scores_from_row(row: StudentProfile | None) -> dict[str, int]:
    if row is None or not row.dimensions:
        return {}
    raw = (row.dimensions or {}).get("_dimension_scores") or {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, int] = {}
    for k in PersonaDimensions.model_fields:
        val = raw.get(k)
        if isinstance(val, (int, float)):
            out[k] = max(1, min(10, int(val)))
    return out


def _profile_to_response(
    row: StudentProfile | None,
    db: Session | None = None,
    user_id: int | None = None,
) -> PersonaProfileResponse:
    if row is None:
        baseline = PersonaDimensions(
            knowledge_base="默认按算法初学者基线评估，待结合课程进度补充",
            cognitive_style="默认采用图示、文字和动手练习混合方式，待访谈确认",
            coding_ability="默认按可完成入门代码练习评估，待 OJ 记录校准",
            learning_goals="默认目标为掌握数据结构与算法基础，待访谈确认",
            error_preference="暂无稳定错因偏好，待 OJ 与 Trace 记录识别",
            grit_level="默认提供分步提示与适中挑战，待学习行为校准",
        )
        return PersonaProfileResponse(
            summary="尚未完成画像访谈，当前使用可运行的六维初始画像。",
            dimensions=baseline,
            updated_at=None,
            dimension_scores={key: 4 for key in PersonaDimensions.model_fields},
            dimension_confidence={
                key: "inferred" for key in PersonaDimensions.model_fields
            },
            coverage_missing=list(PersonaDimensions.model_fields),
            fallback=True,
            fallback_reason="No stored persona; using deterministic baseline",
            generated_by="BaselinePersonaFallback",
        )
    raw = dict(row.dimensions or {})
    persona_fallback = bool(raw.pop("_persona_fallback", False))
    fallback_reason = str(raw.pop("_fallback_reason", "") or "")
    generated_by = str(raw.pop("_generated_by", "") or "")
    confidence = {k: str(v) for k, v in (raw.pop("_confidence", None) or {}).items()}
    missing = list(raw.pop("_coverage_missing", None) or [])
    scores_raw = raw.pop("_dimension_scores", None) or {}
    dims = PersonaDimensions.from_storage(raw)
    scores: dict[str, int] = {}
    if isinstance(scores_raw, dict):
        for k in PersonaDimensions.model_fields:
            val = scores_raw.get(k)
            if isinstance(val, (int, float)):
                scores[k] = max(1, min(10, int(val)))
    if not scores:
        from services.agents.persona import _infer_score_from_text

        for k in PersonaDimensions.model_fields:
            scores[k] = _infer_score_from_text(getattr(dims, k, ""))
    updated = row.updated_at.isoformat() if row.updated_at else None
    dim_evidence: dict[str, list[str]] = dict(raw.get("_dimension_evidence") or {})
    update_reason = str(raw.get("_update_reason") or "")
    recent_raw = raw.get("_recent_evidence") or []
    recent_evidence = []
    if db is not None and user_id is not None:
        try:
            from schemas.persona import LearningEvidenceBrief
            from services.memory.memory_summarizer import (
                build_dimension_evidence,
                build_recent_evidence_items,
                build_update_reason,
            )

            dim_evidence = build_dimension_evidence(db, user_id) or dim_evidence
            update_reason = build_update_reason(db, user_id) or update_reason
            recent_evidence = [
                LearningEvidenceBrief.model_validate(x)
                for x in build_recent_evidence_items(db, user_id, limit=3)
            ]
        except Exception:
            logger.warning("构建画像证据链失败", exc_info=True)
    elif recent_raw:
        from schemas.persona import LearningEvidenceBrief

        recent_evidence = [
            LearningEvidenceBrief.model_validate(x) for x in recent_raw[:3]
        ]

    return PersonaProfileResponse(
        summary=row.summary or "",
        dimensions=dims,
        updated_at=updated,
        dimension_scores=scores,
        dimension_confidence=confidence,
        coverage_missing=missing,
        dimension_evidence=dim_evidence,
        update_reason=update_reason,
        recent_evidence=recent_evidence,
        fallback=persona_fallback,
        fallback_reason=fallback_reason,
        generated_by=generated_by,
    )


def _format_profile_block(
    row: StudentProfile | None,
    db: Session | None = None,
    user_id: int | None = None,
) -> str:
    if row is None or not row.dimensions:
        base = "（尚未建立画像，按通用大一计科算法初学者处理）"
    else:
        dims = row.dimensions
        lines = [f"摘要：{row.summary or '无'}"]
        labels = {
            "knowledge_base": "知识基础",
            "cognitive_style": "认知风格",
            "coding_ability": "代码实操能力",
            "learning_goals": "学习目标",
            "error_preference": "易错点偏好",
            "grit_level": "抗挫折心理",
        }
        for key, label in labels.items():
            val = dims.get(key, "")
            if val:
                lines.append(f"- {label}：{val}")
        ev = dims.get("_dimension_evidence") or {}
        if isinstance(ev, dict):
            for key, snippets in ev.items():
                if snippets and key in labels:
                    lines.append(f"- {labels[key]}证据：" + "；".join(snippets[:2]))
        base = "\n".join(lines)

    if db is not None and user_id is not None:
        try:
            from services.memory.memory_summarizer import append_memory_to_profile_block

            return append_memory_to_profile_block(db, user_id, base)
        except Exception:
            logger.warning("追加学习记忆到画像块失败", exc_info=True)
    return base


class Orchestrator:
    """自研轻量编排：按任务类型路由到对应 Agent。

    注意：Orchestrator 是模块级单例，所有请求共享实例。
    不要使用实例变量存储请求级状态（如 fallback 标记），
    请使用 _persona_chat_fallback_var 等 contextvars 替代。
    """

    def __init__(self) -> None:
        pass  # 所有请求级状态通过 contextvars 管理，避免并发竞态

    # --- 画像 ---

    def get_profile(self, db: Session, user: User) -> PersonaProfileResponse:
        row = db.get(StudentProfile, user.id)
        return _profile_to_response(row, db=db, user_id=user.id)

    async def persona_chat_stream(
        self,
        db: Session,
        user: User,
        *,
        message: str,
        history: list[ChatHistoryItem],
    ) -> AsyncIterator[str]:
        from services.agents.persona_fallback import (
            FALLBACK_REASON_DEFAULT,
            should_use_persona_fallback,
            stream_persona_fallback_reply,
        )
        from services.agents.template_fallback import is_llm_related_error

        row = db.get(StudentProfile, user.id)
        summary = row.summary if row else ""
        existing_dims = None
        if row and row.dimensions:
            existing_dims = PersonaDimensions.from_storage(row.dimensions)

        _meta = {"fallback": False, "reason": ""}

        if should_use_persona_fallback():
            _meta["fallback"] = True
            _meta["reason"] = FALLBACK_REASON_DEFAULT
            _persona_chat_fallback_var.set(_meta)
            async for chunk in stream_persona_fallback_reply(
                message=message,
                history=history,
                existing_dims=existing_dims,
            ):
                yield chunk
            return

        try:
            async for chunk in _persona.run_stream(
                message=message,
                history=history,
                profile_summary=summary,
                existing_dims=existing_dims,
            ):
                yield chunk
        except Exception as exc:
            if not is_llm_related_error(exc):
                raise
            _meta["fallback"] = True
            _meta["reason"] = str(exc)[:200] or FALLBACK_REASON_DEFAULT
            _persona_chat_fallback_var.set(_meta)
            async for chunk in stream_persona_fallback_reply(
                message=message,
                history=history,
                existing_dims=existing_dims,
            ):
                yield chunk

    def last_persona_chat_meta(self) -> dict:
        """返回当前请求上下文中画像对话的降级元信息。

        通过 contextvars 实现每个请求/任务独立存储，
        避免模块级单例 Orchestrator 在并发请求下的竞态条件。
        """
        from services.agents.persona_fallback import persona_fallback_meta

        _meta = _persona_chat_fallback_var.get()
        if _meta["fallback"]:
            return persona_fallback_meta(_meta["reason"])
        return {
            "fallback": False,
            "fallback_reason": "",
            "generated_by": "ProfilingAgent",
        }

    def persona_chat_fallback_meta(self, reason: str | None = None) -> dict:
        from services.agents.persona_fallback import persona_fallback_meta

        return persona_fallback_meta(reason)

    def persona_chat_used_fallback(self) -> bool:
        from services.agents.persona_fallback import should_use_persona_fallback

        return should_use_persona_fallback()

    def patch_persona_from_learning(
        self,
        db: Session,
        user: User,
        body: PersonaLearningPatchRequest,
    ) -> PersonaProfileResponse:
        """随学随新：根据学习信号更新画像维度。"""
        row = db.get(StudentProfile, user.id)
        if row is None:
            row = StudentProfile(user_id=user.id, dimensions={}, summary="")
            db.add(row)
        for signal in body.signals:
            if signal.event_type != "section_done" or not signal.module_key:
                continue
            try:
                from services.memory.memory_service import record_section_completion

                record_section_completion(
                    db,
                    user.id,
                    module_key=signal.module_key,
                    section_id=signal.detail or "unknown",
                )
            except Exception:
                logger.warning("记录小节完成学习记忆失败", exc_info=True)
                db.rollback()
        dims = PersonaDimensions.from_storage(row.dimensions or {})
        summary, new_dims = apply_learning_patch(row.summary or "", dims, body)
        payload = new_dims.model_dump()
        try:
            from services.memory.memory_summarizer import (
                build_dimension_evidence,
                build_recent_evidence_items,
                build_update_reason,
            )

            payload["_dimension_evidence"] = build_dimension_evidence(db, user.id)
            payload["_update_reason"] = (
                build_update_reason(db, user.id) or "随学随新：学习行为已同步至画像"
            )
            payload["_recent_evidence"] = build_recent_evidence_items(db, user.id, limit=3)
        except Exception:
            logger.warning("构建随学随新证据失败", exc_info=True)
            payload["_update_reason"] = "随学随新：学习行为已同步至画像"
        row.summary = summary
        row.dimensions = payload
        row.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(row)
        return _profile_to_response(row, db=db, user_id=user.id)

    async def sync_persona_profile(
        self,
        db: Session,
        user: User,
        *,
        history: list[ChatHistoryItem],
    ) -> PersonaProfileResponse:
        from services.agents.persona_fallback import (
            extract_persona_fallback,
            should_use_persona_fallback,
        )
        from services.agents.template_fallback import is_llm_related_error

        row = db.get(StudentProfile, user.id)
        existing = None
        existing_conf: dict[str, str] = {}
        if row and row.dimensions:
            existing = PersonaDimensions.from_storage(row.dimensions)
            existing_conf = dict((row.dimensions or {}).get("_confidence") or {})

        used_fallback = False
        fallback_reason = ""
        dim_evidence: dict[str, list[str]] = {}
        update_reason = ""
        recent_evidence: list = []

        if should_use_persona_fallback():
            (
                summary,
                dims,
                confidence,
                missing,
                scores,
                dim_evidence,
                update_reason,
                recent_evidence,
            ) = extract_persona_fallback(
                history, existing=existing, existing_confidence=existing_conf
            )
            used_fallback = True
            fallback_reason = "LLM key missing or provider unavailable"
        else:
            try:
                summary, dims, confidence, missing, scores = await _persona.extract_dimensions(
                    history, existing=existing, existing_confidence=existing_conf
                )
            except Exception as exc:
                if not is_llm_related_error(exc):
                    raise
                (
                    summary,
                    dims,
                    confidence,
                    missing,
                    scores,
                    dim_evidence,
                    update_reason,
                    recent_evidence,
                ) = extract_persona_fallback(
                    history, existing=existing, existing_confidence=existing_conf
                )
                used_fallback = True
                fallback_reason = str(exc)[:200]

        if row is None:
            row = StudentProfile(user_id=user.id)
            db.add(row)
        row.summary = summary
        payload = dims.model_dump()
        payload["_confidence"] = confidence
        payload["_dimension_scores"] = scores
        if missing:
            payload["_coverage_missing"] = missing
        if used_fallback:
            from services.agents.persona_fallback import GENERATED_BY

            payload["_persona_fallback"] = True
            payload["_fallback_reason"] = fallback_reason or "LLM key missing or provider unavailable"
            payload["_generated_by"] = GENERATED_BY
            if dim_evidence:
                payload["_dimension_evidence"] = dim_evidence
            if update_reason:
                payload["_update_reason"] = update_reason
            if recent_evidence:
                payload["_recent_evidence"] = [x.model_dump() for x in recent_evidence]
        row.dimensions = payload
        row.chat_history = [{"role": h.role, "content": h.content} for h in history[-30:]]
        row.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(row)
        return _profile_to_response(row, db=db, user_id=user.id)

    def save_persona_history(
        self, db: Session, user: User, history: list[ChatHistoryItem]
    ) -> None:
        row = db.get(StudentProfile, user.id)
        if row is None:
            row = StudentProfile(user_id=user.id, dimensions={}, summary="")
            db.add(row)
        row.chat_history = [{"role": h.role, "content": h.content} for h in history[-30:]]
        db.commit()

    def get_persona_history(self, db: Session, user: User) -> list[ChatHistoryItem]:
        row = db.get(StudentProfile, user.id)
        if not row or not row.chat_history:
            return []
        return [ChatHistoryItem.model_validate(h) for h in row.chat_history]

    # --- 助教 / OJ（非流式，兼容原 API）---

    async def tutor_chat(
        self, request: AiTutorChatRequest, *, profile_block: str = ""
    ) -> str:
        reply = await _tutor.run(request=request, profile_block=profile_block)
        safety = content_filter.check(reply)
        if safety.blocked:
            return "抱歉，回复未通过内容安全校验，请换个问法或联系管理员。"
        return safety.text

    async def tutor_chat_stream(
        self,
        request: AiTutorChatRequest,
        *,
        profile_block: str = "",
    ) -> AsyncIterator[str]:
        async for chunk in _tutor.run_stream(request=request, profile_block=profile_block):
            yield chunk

    async def oj_assistant(self, body: OjAssistantRequest) -> str:
        return await _oj.run_for_request(body)

    async def oj_assistant_stream(self, body: OjAssistantRequest) -> AsyncIterator[str]:
        """流式产出 OJ 助手回复（ds_hint / code_hint）。"""
        async for chunk in _oj.run_stream_for_request(body):
            yield chunk

    def list_agents(self) -> list[dict]:
        return list_agents()

    def describe_resource_pipeline(self) -> list[dict[str, str]]:
        return resource_workflow.describe_pipeline()

    @staticmethod
    def describe_resource_dag_mermaid() -> str:
        return (
            "flowchart TD\n"
            "  PROFILE[ProfilingAgent<br/>六维画像] --> ORCH[Orchestrator]\n"
            "  SPARK[科大讯飞星火 Spark<br/>默认核心大模型] --> ORCH\n"
            "  ORCH --> RAG[KnowledgeRetriever]\n"
            "  RAG --> CONCEPT[ConceptAgent<br/>讲解文档]\n"
            "  CONCEPT -.摘要.-> GRAPH[GraphAgent<br/>Mermaid图谱]\n"
            "  CONCEPT -.摘要.-> QUIZ[QuizAgent<br/>5道练习题]\n"
            "  QUIZ -.易错点.-> SCENARIO[ScenarioAgent<br/>剧本沙盒]\n"
            "  SCENARIO -.TODO框架.-> TRACE[TraceAgent<br/>轨迹动画JSON]\n"
            "  CONCEPT -.拓展方向.-> READ[ReadingAgent<br/>三层拓展阅读]\n"
            "  CONCEPT --> VERIFY{ContentVerifier}\n"
            "  GRAPH --> VERIFY\n"
            "  QUIZ --> VERIFY\n"
            "  SCENARIO --> VERIFY\n"
            "  PPT --> VERIFY\n"
            "  VIDEO --> VERIFY\n"
            "  READ --> VERIFY\n"
            "  TRACE --> SAFETY[SafetyAgent]\n"
            "  VERIFY -->|passed| SAFETY\n"
            "  VERIFY -->|failed| CONCEPT\n"
            "  SAFETY --> STORE[落库 + agent_logs]\n"
        )

    async def evaluate_learning(
        self,
        db: Session,
        user: User,
        body: LearningPathReplanRequest,
    ) -> LearningEvaluationResponse:
        profile_row = db.get(StudentProfile, user.id)
        resources = (
            db.query(GeneratedResource)
            .filter(GeneratedResource.user_id == user.id)
            .order_by(GeneratedResource.created_at.desc())
            .limit(20)
            .all()
        )
        prior = None
        if profile_row and profile_row.dimensions:
            hist = (profile_row.dimensions or {}).get("_evaluation_history") or []
            if hist:
                prior = hist[-1]

        result = await evaluation_agent.evaluate(
            profile_summary=profile_row.summary if profile_row else "",
            profile_block=_format_profile_block(profile_row, db=db, user_id=user.id),
            request=body,
            resources_count=len(resources),
            recent_resource_types=[r.resource_type for r in resources[:8]],
            prior_snapshot=prior,
        )

        if profile_row:
            hist = list((profile_row.dimensions or {}).get("_evaluation_history") or [])
            hist.append(evaluation_agent.build_snapshot(result))
            hist = hist[-10:]
            payload = dict(profile_row.dimensions or {})
            for k in PersonaDimensions.model_fields:
                if k not in payload:
                    payload[k] = str(payload.get(k, ""))
            payload["_evaluation_history"] = hist
            profile_row.dimensions = payload
            db.commit()

        return result

    # --- 学习路径 ---

    def get_learning_path_plan(self, db: Session, user: User) -> LearningPathPlanResponse | None:
        row = db.get(LearningPathPlan, user.id)
        if row is None:
            return None
        return _path_plan_response(row, db=db)

    async def replan_learning_path(
        self,
        db: Session,
        user: User,
        body: LearningPathReplanRequest,
        *,
        remediation_module_key: str | None = None,
    ) -> LearningPathPlanResponse:
        profile_row = db.get(StudentProfile, user.id)
        profile_block = _format_profile_block(profile_row, db=db, user_id=user.id)
        scores = _dimension_scores_from_row(profile_row)
        mastery_by_chapter: dict[str, int] = {}
        try:
            from services.mastery.mastery_service import get_cached_mastery_by_chapter

            mastery_by_chapter = get_cached_mastery_by_chapter(db, user.id)
        except Exception:
            logger.warning("获取掌握度缓存失败", exc_info=True)
        plan_data = await _path.plan(
            profile_block=profile_block,
            request=body,
            dimension_scores=scores,
            remediation_before=remediation_module_key,
            mastery_by_chapter=mastery_by_chapter,
        )

        row = db.get(LearningPathPlan, user.id)
        if row is None:
            row = LearningPathPlan(user_id=user.id)
            db.add(row)
        row.summary = plan_data["summary"]
        row.rationale = plan_data["rationale"]
        row.next_module_key = plan_data.get("next_module_key")
        row.ordered_keys = plan_data["ordered_keys"]
        row.steps = plan_data["steps"]
        row.progress_snapshot = {
            "overall_percent": body.overall_percent,
            "modules": [m.model_dump() for m in body.modules],
            "remediation_inserted": bool(plan_data.get("remediation_inserted")),
        }
        row.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(row)
        try:
            from services.events.event_bus import event_bus

            event_bus.publish(
                db,
                event_type="on_path_adjusted",
                user_id=user.id,
                payload={
                    "summary": plan_data.get("summary", ""),
                    "remediation_inserted": bool(plan_data.get("remediation_inserted")),
                    "next_module_key": plan_data.get("next_module_key"),
                },
            )
        except Exception:
            logger.warning("发布路径调整事件失败", exc_info=True)
        return _path_plan_response(row, db=db, profile_row=profile_row, mastery_by_chapter=mastery_by_chapter)

    async def evaluate_oj_struggle(
        self,
        db: Session,
        user: User,
        body: OjStruggleEvaluationRequest,
    ) -> OjStruggleEvaluationResponse:
        from schemas.oj import SkillCardBrief
        from services.oj.error_patterns import ERROR_TYPE_LABELS
        from services.oj.tutoring_pipeline import _recommended_resources

        course_id = body.course_id or "data_structures_algorithms"
        chapter_id = body.chapter_id or ""
        if not chapter_id:
            try:
                from services.knowledge.course_loader import chapter_id_for_module, load_manifest

                chapter_id = chapter_id_for_module(load_manifest(course_id), body.module_key) or ""
            except Exception:
                logger.warning("获取章节ID失败", exc_info=True)

        error_pattern = (body.error_pattern or "").strip()
        error_pattern_label = ERROR_TYPE_LABELS.get(error_pattern, error_pattern or body.verdict)

        struggle, rem_key, rem_label, logs, skill_cards = await evaluation_agent.evaluate_oj_struggle(
            knowledge_point=body.knowledge_point,
            module_key=body.module_key,
            verdict=body.verdict,
            consecutive_failures=body.consecutive_failures,
            error_pattern=error_pattern,
            recent_trace_summary=body.recent_trace_summary,
        )
        path_updated = False
        plan_summary = ""
        if struggle and rem_key:
            replan_body = LearningPathReplanRequest(
                modules=body.modules,
                overall_percent=body.overall_percent,
            )
            plan = await self.replan_learning_path(
                db,
                user,
                replan_body,
                remediation_module_key=rem_key,
            )
            path_updated = bool(plan.remediation_inserted)
            plan_summary = plan.summary or ""

        memory_recorded = False
        memory_event_id: int | None = None
        try:
            from services.memory.memory_service import record_evaluation_struggle

            mem = record_evaluation_struggle(
                db,
                user.id,
                module_key=body.module_key,
                knowledge_point=body.knowledge_point,
                verdict=body.verdict,
                error_pattern=error_pattern,
                consecutive_failures=body.consecutive_failures,
                skill_ids=[s.id for s in skill_cards],
            )
            memory_recorded = True
            memory_event_id = mem.id
        except Exception:
            logger.warning("记录受挫学习记忆失败", exc_info=True)

        mastery_updated = False
        mastery_update_summary = ""
        recommended_actions: list[str] = []
        path_adjustment_suggestion = ""
        try:
            from services.events.event_bus import event_bus

            pub = event_bus.publish(
                db,
                event_type="on_mastery_recalculated",
                user_id=user.id,
                course_id=course_id,
                chapter_id=chapter_id,
                payload={
                    "module_key": body.module_key,
                    "knowledge_point": body.knowledge_point,
                    "error_pattern": error_pattern,
                    "mastery_score": None,
                    "modules": [m.model_dump() for m in body.modules],
                },
            )
            logs.extend([entry.model_dump() for entry in pub.event.agent_logs])
            path_adj = pub.event.payload.get("path_adjustment") or {}
            if isinstance(path_adj, dict) and path_adj.get("reason"):
                path_adjustment_suggestion = str(path_adj["reason"])
        except Exception:
            logger.warning("发布掌握度重算事件失败", exc_info=True)

        try:
            from services.mastery.mastery_service import MasteryService

            overview = MasteryService(db).recalculate(
                user.id,
                course_id=course_id,
                chapter_id=chapter_id,
                modules=body.modules,
            )
            if overview.report:
                mastery_updated = True
                mastery_update_summary = (
                    f"掌握度 {overview.report.mastery_score}（{overview.report.mastery_level}）"
                )
                recommended_actions = list(overview.report.recommended_actions)
                if overview.report.path_adjustment_suggestion:
                    path_adjustment_suggestion = overview.report.path_adjustment_suggestion
        except Exception:
            logger.warning("掌握度重算失败", exc_info=True)

        skill_id = body.skill_id or (skill_cards[0].id if skill_cards else "")
        recommended_resources = _recommended_resources(skill_id, body.module_key, chapter_id)
        matched_skill: SkillCardBrief | None = None
        if skill_cards:
            primary = skill_cards[0]
            matched_skill = SkillCardBrief(
                id=primary.id,
                name=primary.name,
                chapter_id=primary.chapter_id,
                description=primary.description,
            )
        elif skill_id:
            try:
                from services.skills.registry import SkillRegistry

                card = SkillRegistry().get(skill_id)
                if card:
                    matched_skill = SkillCardBrief(
                        id=card.id,
                        name=card.name,
                        chapter_id=card.chapter_id,
                        description=card.description,
                    )
            except Exception:
                logger.warning("获取技能卡详情失败", exc_info=True)

        if struggle and rem_label and not path_adjustment_suggestion:
            path_adjustment_suggestion = f"LearningPathAgent：优先巩固「{rem_label}」"

        return OjStruggleEvaluationResponse(
            agent_name="EvaluatorAgent",
            struggle_detected=struggle,
            consecutive_failures=body.consecutive_failures,
            remediation_module_key=rem_key or None,
            remediation_label=rem_label,
            planner_notified=struggle,
            path_updated=path_updated,
            agent_logs=[AgentLogItem.model_validate(entry) for entry in logs],
            plan_summary=plan_summary,
            recommended_skill_cards=skill_cards,
            course_id=course_id,
            chapter_id=chapter_id,
            matched_skill=matched_skill,
            error_pattern=error_pattern,
            error_pattern_label=error_pattern_label,
            recommended_actions=recommended_actions,
            recommended_resources=recommended_resources,
            memory_recorded=memory_recorded,
            memory_event_id=memory_event_id,
            mastery_updated=mastery_updated,
            mastery_update_summary=mastery_update_summary,
            path_adjustment_suggestion=path_adjustment_suggestion,
        )

    # --- 资源生成 ---

    async def generate_resource(
        self,
        db: Session,
        user: User,
        body: ResourceGenerateRequest,
        *,
        emit: Callable[[dict], Awaitable[None]] | None = None,
        pipeline_ctx: PipelineContext | None = None,
    ) -> GeneratedResourceItem:
        row = db.get(StudentProfile, user.id)
        profile_block = _format_profile_block(row, db=db, user_id=user.id)
        from core.config import settings

        if not settings.llm_configured:
            return await self.generate_resource_fallback(
                db,
                user,
                body,
                fallback_reason=llm_unavailable_reason(),
                emit=emit,
                pipeline_ctx=pipeline_ctx,
            )
        try:
            title, content, gen_meta = await resource_workflow.run(
                body.resource_type,
                topic=body.topic,
                profile_block=profile_block,
                module_key=body.module_key,
                focus_hint=body.focus_hint,
                emit=emit,
                pipeline_ctx=pipeline_ctx,
            )
        except Exception as exc:
            if not (is_llm_related_error(exc) or isinstance(exc, AgentOutputError)):
                raise
            db.rollback()
            return await self.generate_resource_fallback(
                db,
                user,
                body,
                fallback_reason=str(exc)[:300] or llm_unavailable_reason(),
                emit=emit,
                pipeline_ctx=pipeline_ctx,
            )
        agent_name = agent_for_resource(body.resource_type)
        meta = {
            "topic": body.topic,
            "module_key": body.module_key,
            "agent_logs": gen_meta.get("agent_logs", []),
            **gen_meta,
        }
        record = GeneratedResource(
            user_id=user.id,
            resource_type=body.resource_type,
            agent_name=agent_name,
            title=title,
            content=content,
            meta=meta,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        if row:
            fp = fingerprint_for_resource(
                row,
                resource_type=body.resource_type,
                topic=body.topic,
                module_key=body.module_key,
                focus_hint=body.focus_hint,
            )
            save_fingerprint(
                row,
                resource_type=body.resource_type,
                topic=body.topic,
                module_key=body.module_key,
                fingerprint=fp,
            )
            db.commit()
        try:
            from services.events.event_bus import event_bus

            event_bus.publish(
                db,
                event_type="on_resource_generated",
                user_id=user.id,
                chapter_id=str(meta.get("chapter_id") or ""),
                payload={
                    "resource_type": body.resource_type,
                    "title": title,
                    "resource_id": record.id,
                    "verified": gen_meta.get("verified"),
                    "safety_passed": gen_meta.get("status") != "draft",
                    "agent_logs": gen_meta.get("agent_logs", []),
                    "module_key": body.module_key,
                    "topic": body.topic,
                },
            )
        except Exception:
            logger.warning("发布资源生成事件失败", exc_info=True)
        return _resource_item(record)

    async def generate_resource_fallback(
        self,
        db: Session,
        user: User,
        body: ResourceGenerateRequest,
        *,
        fallback_reason: str,
        emit: Callable[[dict], Awaitable[None]] | None = None,
        pipeline_ctx: PipelineContext | None = None,
    ) -> GeneratedResourceItem:
        row = db.get(StudentProfile, user.id)
        profile_block = _format_profile_block(row, db=db, user_id=user.id)
        title, content, gen_meta = await fallback_resource_workflow.run(
            body.resource_type,
            topic=body.topic,
            profile_block=profile_block,
            module_key=body.module_key,
            focus_hint=body.focus_hint,
            fallback_reason=fallback_reason,
            emit=emit,
            pipeline_ctx=pipeline_ctx,
        )
        agent_name = TEMPLATE_FALLBACK_AGENT
        meta = {
            "topic": body.topic,
            "module_key": body.module_key,
            "agent_logs": gen_meta.get("agent_logs", []),
            **gen_meta,
        }
        record = GeneratedResource(
            user_id=user.id,
            resource_type=body.resource_type,
            agent_name=agent_name,
            title=title,
            content=content,
            meta=meta,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return _resource_item(record)

    def list_resources(self, db: Session, user: User) -> list[GeneratedResourceItem]:
        rows = (
            db.query(GeneratedResource)
            .filter(GeneratedResource.user_id == user.id)
            .order_by(GeneratedResource.created_at.desc())
            .limit(50)
            .all()
        )
        return [_resource_item(r) for r in rows]

    def recommend_resources(
        self,
        db: Session,
        user: User,
        *,
        module_key: str = "",
        limit: int = 6,
    ) -> list[GeneratedResourceItem]:
        """基于画像薄弱点、路径下一步与模块匹配推送资源。"""
        from services.agents.explain_engine import (
            build_explain_context,
            generate_resource_explain,
        )

        profile_row = db.get(StudentProfile, user.id)
        path_row = db.get(LearningPathPlan, user.id)
        weak_hint = ""
        if profile_row and profile_row.dimensions:
            weak_hint = str(
                profile_row.dimensions.get("error_preference")
                or profile_row.dimensions.get("weak_points", "")
            )
        target_key = module_key
        if not target_key and path_row and path_row.next_module_key:
            target_key = path_row.next_module_key

        mastery_by_chapter: dict[str, int] = {}
        try:
            from services.mastery.mastery_service import get_cached_mastery_by_chapter

            mastery_by_chapter = get_cached_mastery_by_chapter(db, user.id)
        except Exception:
            logger.warning("获取掌握度缓存（资源推荐）失败", exc_info=True)

        rows = (
            db.query(GeneratedResource)
            .filter(GeneratedResource.user_id == user.id)
            .order_by(GeneratedResource.created_at.desc())
            .limit(40)
            .all()
        )
        if not rows:
            return []

        priority_types = [
            "exercises",
            "document",
            "mindmap",
            "code_case",
            "trace_animation",
            "reading",
        ]

        def score(row: GeneratedResource) -> float:
            meta = row.meta or {}
            mk = str(meta.get("module_key", ""))
            s = 0.0
            if target_key and mk == target_key:
                s += 10.0
            if target_key and target_key.replace("-", "") in (row.title + row.content)[:200]:
                s += 3.0
            if weak_hint and any(w in row.title for w in weak_hint.split("、")[:3]):
                s += 5.0
            try:
                s += (len(priority_types) - priority_types.index(row.resource_type)) * 0.5
            except ValueError:
                pass
            if row.created_at:
                s += min(2.0, _resource_age_days(row.created_at))
            return s

        ranked = sorted(rows, key=score, reverse=True)[:limit]
        items = [_resource_item(r) for r in ranked]

        for item in items:
            res_mk = str((item.meta or {}).get("module_key", "")) or target_key
            ctx = build_explain_context(
                profile_row=profile_row,
                path_row=path_row,
                module_key=res_mk,
                resource_type=item.resource_type,
                is_next_module=(res_mk == (path_row.next_module_key if path_row else None)),
                mastery_by_chapter=mastery_by_chapter,
            )
            item.explain = generate_resource_explain(ctx)

        return items

    async def generate_resource_stream(
        self,
        db: Session,
        user: User,
        body: ResourceGenerateRequest,
    ) -> AsyncIterator[str]:
        """SSE：单类资源生成，含 workflow 与进度百分比。"""
        total_steps = 5
        events: list[dict] = []
        wf_count = 0

        async def capture(ev: dict) -> None:
            nonlocal wf_count
            if ev.get("type") == "workflow":
                wf_count += 1
                ev = {**ev, "percent": min(95, int(wf_count / total_steps * 100))}
            events.append(ev)

        yield _sse({"type": "progress", "step": 0, "total": total_steps, "percent": 0})
        item = await self.generate_resource(db, user, body, emit=capture)
        for ev in events:
            yield _sse(ev)
        yield _sse({
            "type": "resource",
            "resource": item.model_dump(),
            "agent_logs": (item.meta or {}).get("agent_logs", []),
            "percent": 100,
        })
        yield _sse({"type": "done", "percent": 100})

    def delete_resource(self, db: Session, user: User, resource_id: int) -> bool:
        row = (
            db.query(GeneratedResource)
            .filter(
                GeneratedResource.id == resource_id,
                GeneratedResource.user_id == user.id,
            )
            .first()
        )
        if not row:
            return False
        db.delete(row)
        db.commit()
        return True

    def set_resource_favorite(
        self, db: Session, user: User, resource_id: int, favorited: bool
    ) -> GeneratedResourceItem | None:
        row = (
            db.query(GeneratedResource)
            .filter(
                GeneratedResource.id == resource_id,
                GeneratedResource.user_id == user.id,
            )
            .first()
        )
        if not row:
            return None
        meta = dict(row.meta or {})
        meta["favorited"] = favorited
        row.meta = meta
        db.commit()
        db.refresh(row)
        return _resource_item(row)

    async def _run_phase_task(
        self,
        _db: Session,
        user: User,
        *,
        resource_type: ResourceType,
        topic: str,
        module_key: str,
        focus_hint: str,
        pipeline_ctx: PipelineContext,
        fallback_reason: str | None = None,
    ) -> tuple[ResourceType, list[dict], GeneratedResourceItem | None, Exception | None]:
        """单阶段资源任务。并行阶段使用独立 Session，避免共享请求级 Session 并发 commit。"""
        from core.database import SessionLocal

        events: list[dict] = []

        async def capture(ev: dict) -> None:
            events.append(ev)

        req = ResourceGenerateRequest(
            resource_type=resource_type,
            topic=topic,
            module_key=module_key,
            focus_hint=focus_hint,
        )
        local_db = SessionLocal()
        try:
            local_user = local_db.get(User, user.id)
            if local_user is None:
                return resource_type, events, None, ValueError("用户不存在")
            if fallback_reason:
                item = await self.generate_resource_fallback(
                    local_db,
                    local_user,
                    req,
                    fallback_reason=fallback_reason,
                    emit=capture,
                    pipeline_ctx=pipeline_ctx,
                )
                return resource_type, events, item, None
            item = await self.generate_resource(
                local_db,
                local_user,
                req,
                emit=capture,
                pipeline_ctx=pipeline_ctx,
            )
            return resource_type, events, item, None
        except Exception as exc:
            local_db.rollback()
            if fallback_reason:
                return resource_type, events, None, exc
            if is_llm_related_error(exc) or isinstance(exc, AgentOutputError):
                from fastapi import HTTPException

                reason = (
                    str(exc.detail)[:240]
                    if isinstance(exc, HTTPException)
                    else str(exc)[:240]
                )
                try:
                    item = await self.generate_resource_fallback(
                        local_db,
                        local_user,
                        req,
                        fallback_reason=reason or "LLM 调用失败",
                        emit=capture,
                        pipeline_ctx=pipeline_ctx,
                    )
                    return resource_type, events, item, None
                except Exception as fb_exc:
                    local_db.rollback()
                    return resource_type, events, None, fb_exc
            return resource_type, events, None, exc
        finally:
            local_db.close()

    async def generate_all_resources_stream(
        self,
        db: Session,
        user: User,
        *,
        topic: str,
        module_key: str = "",
        focus_hint: str = "",
    ) -> AsyncIterator[str]:
        """SSE：按并行阶段生成多类型学习资源，无依赖的 Agent 并行执行。

        阶段拓扑（来自 README DAG）：
          Phase 1: document            ← 无依赖
          Phase 2: mindmap + exercises ← 并行，均只依赖 document
          Phase 3: code_case           ← 依赖 exercises
          Phase 4: trace_animation + reading ← 展示型资源并行

        asyncio 协作式调度保证：
          PipelineContext 的 log() / update_from_resource() 均为纯同步方法，
          在两个 await 之间原子完成；不同 Agent 写不同字段，无数据竞争。
        """
        phases: list[list[ResourceType]] = PARALLEL_PHASES
        total = len(CORE_RESOURCE_PIPELINE)
        pipe_ctx = PipelineContext()
        started = 0
        completed = 0
        phase_errors: list[dict] = []
        emitted_collab_count = 0
        emitted_agent_log_count = 0
        reused_count = 0
        batch_fallback_reason = llm_unavailable_reason()

        yield _sse({
            "type": "progress",
            "event_type": "accepted",
            "agent_id": "Orchestrator",
            "agent_name": "Orchestrator",
            "message": "Orchestrator 已接收任务",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step": 0,
            "total": total,
            "percent": 0,
        })
        yield _sse(_observable_agent_event(
            agent="ProfilingAgent",
            stage="profile_context",
            status="success",
            message="已加载六维动态学习画像",
            input_summary=f"user_id={user.id}",
            output_summary="profile summary + persona dimensions",
        ))
        yield _sse(_observable_agent_event(
            agent="LearningPathAgent",
            stage="path_context",
            status="success",
            message="已读取当前学习路径，作为资源编排上下文",
            input_summary=f"module_key={module_key or 'auto'}",
            output_summary="current learning path context",
        ))
        if batch_fallback_reason:
            yield _sse({
                "type": "workflow",
                "stage": "llm_check",
                "agent": "Orchestrator",
                "status": "skipped",
                "detail": batch_fallback_reason,
                "percent": 0,
                "event_type": "llm_check",
                "agent_id": "Orchestrator",
                "agent_name": "Orchestrator",
                "message": batch_fallback_reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "severity": "warn",
            })
            yield _sse({
                "type": "workflow",
                "stage": "fallback_mode",
                "agent": TEMPLATE_FALLBACK_AGENT,
                "status": "running",
                "detail": "检测到 LLM 不可用，切换课程知识库模板生成",
                "percent": 0,
                "event_type": "fallback_mode",
                "agent_id": TEMPLATE_FALLBACK_AGENT,
                "agent_name": TEMPLATE_FALLBACK_AGENT,
                "message": "检测到 LLM 不可用，切换课程知识库模板生成",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "severity": "warn",
            })

        profile_row = db.get(StudentProfile, user.id)
        existing_rows = (
            db.query(GeneratedResource)
            .filter(GeneratedResource.user_id == user.id)
            .order_by(GeneratedResource.created_at.desc())
            .limit(80)
            .all()
        )

        for phase_idx, phase_types in enumerate(phases):
            is_parallel = len(phase_types) > 1
            to_generate: list[ResourceType] = []
            reuse_results: list[tuple[ResourceType, GeneratedResourceItem, str]] = []

            for rtype in phase_types:
                started += 1
                meta = RESOURCE_AGENT_META[rtype]
                yield _sse({
                    "type": "progress",
                    "step": started,
                    "total": total,
                    "percent": int((started - 1) / total * 100),
                    "resource_type": rtype,
                    "agent_name": meta["agent_name"],
                    "label": meta["label"],
                    "parallel": is_parallel,
                })
                existing = find_latest_resource(
                    existing_rows,
                    resource_type=rtype,
                    topic=topic,
                    module_key=module_key,
                )
                skip, reason = should_skip_generation(
                    profile_row,
                    existing,
                    resource_type=rtype,
                    topic=topic,
                    module_key=module_key,
                    focus_hint=focus_hint,
                )
                if skip and existing is not None and not batch_fallback_reason:
                    item = _resource_item(existing)
                    meta_dict = dict(item.meta or {})
                    meta_dict["reused"] = True
                    meta_dict["reuse_reason"] = reason
                    item = GeneratedResourceItem(**{**item.model_dump(), "meta": meta_dict})
                    # 复用资源时仍注入 PipelineContext，避免后续 phase 缺少上游摘要
                    pipe_ctx.update_from_resource(rtype, existing.content or "")
                    reuse_results.append((rtype, item, reason))
                    reused_count += 1
                else:
                    to_generate.append(rtype)

            coros = [
                self._run_phase_task(
                    db,
                    user,
                    resource_type=rtype,
                    topic=topic,
                    module_key=module_key,
                    focus_hint=focus_hint,
                    pipeline_ctx=pipe_ctx,
                    fallback_reason=batch_fallback_reason,
                )
                for rtype in to_generate
            ]

            raw_results: list = []
            if is_parallel and len(coros) > 1:
                gather_task = asyncio.ensure_future(asyncio.gather(*coros, return_exceptions=True))
                while not gather_task.done():
                    done, _ = await asyncio.wait({gather_task}, timeout=2.5)
                    if done:
                        break
                    yield _sse({
                        "type": "heartbeat",
                        "event_type": "heartbeat",
                        "message": "Agent 正在生成中…",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "percent": int(completed / total * 100),
                    })
                raw_results = gather_task.result()
            elif len(coros) == 1:
                # 单协程阶段也需心跳，避免前端 150s 无活动超时
                single_task = asyncio.ensure_future(coros[0])
                while not single_task.done():
                    done, _ = await asyncio.wait({single_task}, timeout=2.5)
                    if done:
                        break
                    yield _sse({
                        "type": "heartbeat",
                        "event_type": "heartbeat",
                        "message": "Agent 正在生成中…",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "percent": int(completed / total * 100),
                    })
                try:
                    raw_results = [single_task.result()]
                except Exception as exc:
                    raw_results = [exc]
            elif len(coros) == 0:
                raw_results = []

            combined: list = list(reuse_results)
            for raw in raw_results:
                if isinstance(raw, Exception):
                    combined.append(raw)
                else:
                    combined.append(raw)

            for raw in combined:
                if isinstance(raw, Exception):
                    completed += 1
                    phase_errors.append({"error": str(raw)[:300]})
                    yield _sse({
                        "type": "error",
                        "message": f"阶段 {phase_idx + 1} 资源生成异常：{str(raw)[:200]}",
                        "percent": int(completed / total * 100),
                    })
                    continue

                if isinstance(raw, tuple) and len(raw) == 3:
                    rtype, item, reason = raw
                    completed += 1
                    pct = int(completed / total * 100)
                    yield _sse({
                        "type": "workflow",
                        "stage": "reuse",
                        "agent": RESOURCE_AGENT_META[rtype]["agent_name"],
                        "agent_id": RESOURCE_AGENT_META[rtype]["agent_name"],
                        "agent_name": RESOURCE_AGENT_META[rtype]["agent_name"],
                        "status": "skipped",
                        "resource_type": rtype,
                        "detail": reason,
                        "message": reason,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "duration_ms": 0,
                        "validation_result": {"status": "reused"},
                        "retry_count": 0,
                        "input_summary": f"{topic} | {rtype}",
                        "output_summary": "reused latest verified resource",
                        "failure_reason": "",
                        "percent": pct,
                    })
                    verification = item.verification or (item.meta or {}).get("verification") or {}
                    if not isinstance(verification, dict):
                        verification = {}
                    final_decision = str(verification.get("final_decision") or "draft")
                    verifier_status = str(verification.get("verifier_status") or "warning")
                    safety_status = str(verification.get("safety_status") or "warning")
                    yield _sse({
                        "type": "workflow",
                        "stage": "content_verify",
                        "agent": "ContentVerifierAgent",
                        "agent_id": "ContentVerifierAgent",
                        "agent_name": "ContentVerifierAgent",
                        "status": "skipped",
                        "resource_type": rtype,
                        "detail": "复用已校验资源，未重复调用校验 Agent",
                        "message": "复用已校验资源，未重复调用校验 Agent",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "duration_ms": 0,
                        "validation_result": {"status": verifier_status, "final_decision": final_decision},
                        "retry_count": int(verification.get("retry_count") or 0),
                        "input_summary": f"reused {rtype}",
                        "output_summary": f"verification={verifier_status}",
                        "failure_reason": "" if final_decision == "publish" else "资源保留为草稿，等待复核",
                        "percent": pct,
                    })
                    yield _sse({
                        "type": "workflow",
                        "stage": "safety_filter",
                        "agent": "SafetyAgent",
                        "agent_id": "SafetyAgent",
                        "agent_name": "SafetyAgent",
                        "status": "skipped",
                        "resource_type": rtype,
                        "detail": "复用已审查资源，未重复调用安全 Agent",
                        "message": "复用已审查资源，未重复调用安全 Agent",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "duration_ms": 0,
                        "validation_result": {"status": safety_status, "final_decision": final_decision},
                        "retry_count": 0,
                        "input_summary": f"reused {rtype}",
                        "output_summary": f"safety={safety_status}",
                        "failure_reason": "" if safety_status != "failed" else "原资源安全审查未通过",
                        "percent": pct,
                    })
                    yield _sse({
                        "type": "resource",
                        "resource": item.model_dump(),
                        "percent": pct,
                        "reused": True,
                    })
                    continue

                rtype, events, item, error = raw
                completed += 1
                pct = int(completed / total * 100)

                if error is not None:
                    phase_errors.append({
                        "resource_type": rtype,
                        "agent_name": RESOURCE_AGENT_META[rtype]["agent_name"],
                        "error": str(error)[:300],
                    })
                    for ev in events:
                        if ev.get("type") == "workflow":
                            ev.setdefault("event_type", ev.get("stage", ""))
                            ev.setdefault("agent_id", ev.get("agent", ""))
                            ev.setdefault("agent_name", ev.get("agent", ""))
                            ev.setdefault("message", ev.get("detail", ""))
                            ev.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
                            ev.setdefault("severity", "info")
                        yield _sse(ev)
                    yield _sse({
                        "type": "workflow",
                        "stage": "agent_generate",
                        "agent": RESOURCE_AGENT_META[rtype]["agent_name"],
                        "agent_id": RESOURCE_AGENT_META[rtype]["agent_name"],
                        "agent_name": RESOURCE_AGENT_META[rtype]["agent_name"],
                        "status": "failed",
                        "resource_type": rtype,
                        "detail": str(error)[:300],
                        "message": str(error)[:300],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "duration_ms": None,
                        "validation_result": {"status": "failed"},
                        "retry_count": 0,
                        "input_summary": f"{topic} | {rtype}",
                        "output_summary": "",
                        "failure_reason": str(error)[:300],
                        "percent": pct,
                    })
                    yield _sse({
                        "type": "error",
                        "message": f"{RESOURCE_AGENT_META[rtype]['agent_name']} 生成失败，跳过继续",
                        "resource_type": rtype,
                        "percent": pct,
                    })
                    continue

                for ev in events:
                    if ev.get("type") == "workflow":
                        ev["percent"] = pct
                        ev.setdefault("event_type", ev.get("stage", ""))
                        ev.setdefault("agent_id", ev.get("agent", ""))
                        ev.setdefault("agent_name", ev.get("agent", ""))
                        ev.setdefault("message", ev.get("detail", ""))
                        ev.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
                        ev.setdefault("severity", "info")
                    yield _sse(ev)

                new_collab = pipe_ctx.collaboration_log[emitted_collab_count:]
                new_logs = pipe_ctx.agent_logs[emitted_agent_log_count:]
                emitted_collab_count = len(pipe_ctx.collaboration_log)
                emitted_agent_log_count = len(pipe_ctx.agent_logs)
                yield _sse({
                    "type": "collaboration",
                    "log": new_collab[-5:] if new_collab else [],
                    "agent_logs": new_logs,
                })
                yield _sse({
                    "type": "resource",
                    "resource": item.model_dump(),
                    "verification": item.verification or (item.meta or {}).get("verification"),
                    "percent": pct,
                    "agent_logs": (item.meta or {}).get("agent_logs", []),
                })

        yield _sse(_observable_agent_event(
            agent="EvaluationAgent",
            stage="batch_evaluation",
            status="success" if not phase_errors else "failed",
            message="资源批次质量评估完成" if not phase_errors else "资源批次存在部分失败",
            input_summary=f"completed={completed}, total={total}",
            output_summary=f"reused={reused_count}, errors={len(phase_errors)}",
            validation_result={
                "status": "passed" if not phase_errors else "warning",
                "error_count": len(phase_errors),
            },
            failure_reason="; ".join(e.get("error", "") for e in phase_errors[:3]),
        ))
        yield _sse({
            "type": "done",
            "percent": 100,
            "agent_logs": pipe_ctx.agent_logs,
            "partial_failure": bool(phase_errors),
            "errors": phase_errors or None,
            "reused_count": reused_count,
            "fallback_mode": bool(batch_fallback_reason),
            "fallback_reason": batch_fallback_reason,
        })


def _normalize_legacy_step(step: dict, rank: int) -> dict:
    """兼容旧格式 step：旧版用 key/label/status，新版用 module_key/rank。

    无论数据库里存的是旧格式还是新格式，都返回可被 PathStepItem 校验通过的新格式 dict。
    """
    out = dict(step)
    if "module_key" not in out:
        out["module_key"] = str(out.get("key", ""))
    out.setdefault("rank", rank)
    return out


def _step_needs_migration(step: dict) -> bool:
    """判断一个 step 是否仍是旧格式（缺 module_key 或 rank）。"""
    return "module_key" not in step or "rank" not in step


def migrate_legacy_learning_path_plans(db: Session) -> int:
    """启动时数据自愈：扫描所有 LearningPathPlan，把旧格式 steps 原地升级为新格式。

    返回迁移的行数。幂等——已是新格式的行不会被改动。
    """
    rows = db.query(LearningPathPlan).all()
    migrated = 0
    for row in rows:
        steps = row.steps or []
        if not any(_step_needs_migration(s) for s in steps if isinstance(s, dict)):
            continue
        row.steps = [
            _normalize_legacy_step(s, i)
            for i, s in enumerate(steps, start=1)
            if isinstance(s, dict)
        ]
        migrated += 1
    if migrated:
        db.commit()
        logger.info("学习路径计划旧格式数据迁移完成，共 %d 行", migrated)
    return migrated


def _path_plan_response(
    row: LearningPathPlan,
    *,
    db: Session | None = None,
    profile_row=None,
    mastery_by_chapter: dict[str, int] | None = None,
) -> LearningPathPlanResponse:
    from services.agents.explain_engine import (
        build_explain_context,
        generate_path_step_explain,
    )

    raw_steps = row.steps or []
    steps = [
        PathStepItem.model_validate(_normalize_legacy_step(s, i))
        for i, s in enumerate(raw_steps, start=1)
    ]
    snapshot = row.progress_snapshot or {}
    remediation = bool(snapshot.get("remediation_inserted")) or any(
        s.is_remediation for s in steps
    )
    next_key = row.next_module_key

    if profile_row is None and db is not None:
        try:
            from models.db_models import StudentProfile

            profile_row = db.get(StudentProfile, row.user_id)
        except Exception:
            logger.warning("获取画像行失败", exc_info=True)
            profile_row = None

    if mastery_by_chapter is None and db is not None:
        try:
            from services.mastery.mastery_service import get_cached_mastery_by_chapter

            mastery_by_chapter = get_cached_mastery_by_chapter(db, row.user_id)
        except Exception:
            logger.warning("获取掌握度缓存（路径响应）失败", exc_info=True)
            mastery_by_chapter = {}

    for step in steps:
        ctx = build_explain_context(
            profile_row=profile_row,
            module_key=step.module_key,
            prerequisites=step.prerequisites,
            is_remediation=step.is_remediation,
            is_next_module=(step.module_key == next_key),
            mastery_by_chapter=mastery_by_chapter,
        )
        step.explain = generate_path_step_explain(ctx)

    return LearningPathPlanResponse(
        agent_name="PlannerAgent",
        summary=row.summary or "",
        rationale=row.rationale or "",
        next_module_key=next_key,
        ordered_keys=list(row.ordered_keys or []),
        steps=steps,
        updated_at=row.updated_at.isoformat() if row.updated_at else None,
        remediation_inserted=remediation,
    )


def _resource_item(row: GeneratedResource) -> GeneratedResourceItem:
    meta = dict(row.meta or {})
    verification = meta.get("verification")
    raw_sources = meta.get("sources")
    sources = []
    if isinstance(raw_sources, list):
        for source in raw_sources:
            if not isinstance(source, dict):
                continue
            normalized = dict(source)
            normalized["chunk_id"] = str(
                normalized.get("chunk_id") or normalized.get("id") or ""
            )
            if normalized["chunk_id"]:
                sources.append(normalized)
    return GeneratedResourceItem(
        id=row.id,
        resource_type=row.resource_type,
        agent_name=row.agent_name,
        title=row.title,
        content=row.content,
        meta=meta,
        sources=sources if isinstance(sources, list) else [],
        created_at=row.created_at.isoformat() if row.created_at else "",
        verification=verification if isinstance(verification, dict) else None,
    )


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _observable_agent_event(
    *,
    agent: str,
    stage: str,
    status: str,
    message: str,
    input_summary: str = "",
    output_summary: str = "",
    validation_result: dict | None = None,
    failure_reason: str = "",
    duration_ms: int | None = 0,
    retry_count: int = 0,
) -> dict:
    return {
        "type": "workflow",
        "event_type": stage,
        "agent": agent,
        "agent_id": agent,
        "agent_name": agent,
        "stage": stage,
        "status": status,
        "detail": message,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_ms": duration_ms,
        "validation_result": validation_result,
        "retry_count": retry_count,
        "input_summary": input_summary,
        "output_summary": output_summary,
        "failure_reason": failure_reason,
        "severity": "error" if status == "failed" else "info",
    }


def _resource_age_days(created_at: datetime) -> float:
    """兼容 SQLite 返回的 naive/aware datetime。"""
    from datetime import timezone

    now = datetime.now(timezone.utc)
    ts = created_at
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return max(0.0, (now - ts).total_seconds() / 86400)


orchestrator = Orchestrator()
