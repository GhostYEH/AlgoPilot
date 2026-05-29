"""编排层：所有 AI 能力统一入口，禁止 API 直连 LLM。"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import datetime

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
from services.agents.registry import agent_for_resource, list_agents
from services.agents.tutor import TutorAgent
from services.orchestrator.persona_fingerprint import (
    find_latest_resource,
    fingerprint_for_resource,
    save_fingerprint,
    should_skip_generation,
)
from services.orchestrator.pipeline_context import PipelineContext
from services.orchestrator.workflow import resource_workflow
from services.safety.content_filter import content_filter

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


def _profile_to_response(row: StudentProfile | None) -> PersonaProfileResponse:
    if row is None:
        return PersonaProfileResponse(
            summary="",
            dimensions=PersonaDimensions(),
            updated_at=None,
        )
    raw = dict(row.dimensions or {})
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
    return PersonaProfileResponse(
        summary=row.summary or "",
        dimensions=dims,
        updated_at=updated,
        dimension_scores=scores,
        dimension_confidence=confidence,
        coverage_missing=missing,
    )


def _format_profile_block(row: StudentProfile | None) -> str:
    if row is None or not row.dimensions:
        return "（尚未建立画像，按通用大一计科算法初学者处理）"
    dims = row.dimensions
    lines = [f"摘要：{row.summary or '无'}"]
    labels = {
        "knowledge_base": "知识基础",
        "cognitive_style": "认知风格",
        "coding_ability": "代码实操能力",
        "learning_goals": "学习目标",
        "error_preference": "易错点偏好",
        "grit_level": "抗挫折心理能力",
    }
    for key, label in labels.items():
        val = dims.get(key, "")
        if val:
            lines.append(f"- {label}：{val}")
    return "\n".join(lines)


class Orchestrator:
    """自研轻量编排：按任务类型路由到对应 Agent。"""

    # --- 画像 ---

    def get_profile(self, db: Session, user: User) -> PersonaProfileResponse:
        row = db.get(StudentProfile, user.id)
        return _profile_to_response(row)

    async def persona_chat_stream(
        self,
        db: Session,
        user: User,
        *,
        message: str,
        history: list[ChatHistoryItem],
    ) -> AsyncIterator[str]:
        row = db.get(StudentProfile, user.id)
        summary = row.summary if row else ""
        existing_dims = None
        if row and row.dimensions:
            existing_dims = PersonaDimensions.from_storage(row.dimensions)
        async for chunk in _persona.run_stream(
            message=message,
            history=history,
            profile_summary=summary,
            existing_dims=existing_dims,
        ):
            yield chunk

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
        dims = PersonaDimensions.from_storage(row.dimensions or {})
        summary, new_dims = apply_learning_patch(row.summary or "", dims, body)
        row.summary = summary
        row.dimensions = new_dims.model_dump()
        row.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(row)
        return _profile_to_response(row)

    async def sync_persona_profile(
        self,
        db: Session,
        user: User,
        *,
        history: list[ChatHistoryItem],
    ) -> PersonaProfileResponse:
        row = db.get(StudentProfile, user.id)
        existing = None
        existing_conf: dict[str, str] = {}
        if row and row.dimensions:
            existing = PersonaDimensions.from_storage(row.dimensions)
            existing_conf = dict((row.dimensions or {}).get("_confidence") or {})
        summary, dims, confidence, missing, scores = await _persona.extract_dimensions(
            history, existing=existing, existing_confidence=existing_conf
        )
        if row is None:
            row = StudentProfile(user_id=user.id)
            db.add(row)
        row.summary = summary
        payload = dims.model_dump()
        payload["_confidence"] = confidence
        payload["_dimension_scores"] = scores
        if missing:
            payload["_coverage_missing"] = missing
        row.dimensions = payload
        row.chat_history = [{"role": h.role, "content": h.content} for h in history[-30:]]
        row.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(row)
        return _profile_to_response(row)

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
            "  CONCEPT -.摘要.-> QUIZ[QuizAgent<br/>3道练习题]\n"
            "  QUIZ -.易错点.-> SCENARIO[ScenarioAgent<br/>剧本沙盒]\n"
            "  SCENARIO -.TODO框架.-> TRACE[TraceAgent<br/>轨迹动画JSON]\n"
            "  CONCEPT -.核心提炼.-> PPT[PptAgent<br/>PPT胶片预览]\n"
            "  CONCEPT -.认知风格.-> VIDEO[VideoScriptAgent<br/>60秒短视频脚本]\n"
            "  CONCEPT -.拓展方向.-> READ[ReadingAgent<br/>三层拓展阅读]\n"
            "  VIDEO --> TTS[科大讯飞 TTS<br/>讲解音频试听]\n"
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
            profile_block=_format_profile_block(profile_row),
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
        return _path_plan_response(row)

    async def replan_learning_path(
        self,
        db: Session,
        user: User,
        body: LearningPathReplanRequest,
        *,
        remediation_module_key: str | None = None,
    ) -> LearningPathPlanResponse:
        profile_row = db.get(StudentProfile, user.id)
        profile_block = _format_profile_block(profile_row)
        scores = _dimension_scores_from_row(profile_row)
        plan_data = await _path.plan(
            profile_block=profile_block,
            request=body,
            dimension_scores=scores,
            remediation_before=remediation_module_key,
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
        row.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(row)
        return _path_plan_response(row)

    async def evaluate_oj_struggle(
        self,
        db: Session,
        user: User,
        body: OjStruggleEvaluationRequest,
    ) -> OjStruggleEvaluationResponse:
        struggle, rem_key, rem_label, logs = await evaluation_agent.evaluate_oj_struggle(
            knowledge_point=body.knowledge_point,
            module_key=body.module_key,
            verdict=body.verdict,
            consecutive_failures=body.consecutive_failures,
            error_pattern=body.error_pattern,
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
        profile_block = _format_profile_block(row)
        title, content, gen_meta = await resource_workflow.run(
            body.resource_type,
            topic=body.topic,
            profile_block=profile_block,
            module_key=body.module_key,
            focus_hint=body.focus_hint,
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
            "ppt",
            "video_script",
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
        return [_resource_item(r) for r in ranked]

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
        """SSE：按并行阶段生成比赛展示资源，无依赖的 Agent 并行执行。

        阶段拓扑（来自 README DAG）：
          Phase 1: document            ← 无依赖
          Phase 2: mindmap + exercises ← 并行，均只依赖 document
          Phase 3: code_case           ← 依赖 exercises
          Phase 4: trace_animation + ppt + video_script + reading ← 展示型资源并行

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
                if skip and existing is not None:
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
                )
                for rtype in to_generate
            ]

            raw_results: list = []
            if is_parallel and len(coros) > 1:
                raw_results = await asyncio.gather(*coros, return_exceptions=True)
            elif len(coros) == 1:
                raw_results = [await coros[0]]
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
                        "agent": "Orchestrator",
                        "status": "skipped",
                        "resource_type": rtype,
                        "detail": reason,
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
                        yield _sse(ev)
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
                    "percent": pct,
                    "agent_logs": (item.meta or {}).get("agent_logs", []),
                })

        yield _sse({
            "type": "done",
            "percent": 100,
            "agent_logs": pipe_ctx.agent_logs,
            "partial_failure": bool(phase_errors),
            "errors": phase_errors or None,
            "reused_count": reused_count,
        })


def _path_plan_response(row: LearningPathPlan) -> LearningPathPlanResponse:
    steps = [PathStepItem.model_validate(s) for s in (row.steps or [])]
    snapshot = row.progress_snapshot or {}
    remediation = bool(snapshot.get("remediation_inserted")) or any(
        s.is_remediation for s in steps
    )
    return LearningPathPlanResponse(
        agent_name="PlannerAgent",
        summary=row.summary or "",
        rationale=row.rationale or "",
        next_module_key=row.next_module_key,
        ordered_keys=list(row.ordered_keys or []),
        steps=steps,
        updated_at=row.updated_at.isoformat() if row.updated_at else None,
        remediation_inserted=remediation,
    )


def _resource_item(row: GeneratedResource) -> GeneratedResourceItem:
    return GeneratedResourceItem(
        id=row.id,
        resource_type=row.resource_type,
        agent_name=row.agent_name,
        title=row.title,
        content=row.content,
        meta=row.meta or {},
        created_at=row.created_at.isoformat() if row.created_at else "",
    )


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _resource_age_days(created_at: datetime) -> float:
    """兼容 SQLite 返回的 naive/aware datetime。"""
    from datetime import timezone

    now = datetime.now(timezone.utc)
    ts = created_at
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return max(0.0, (now - ts).total_seconds() / 86400)


orchestrator = Orchestrator()
