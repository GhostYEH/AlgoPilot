"""编排层：所有 AI 能力统一入口，禁止 API 直连 LLM。"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import datetime

from sqlalchemy.orm import Session

from models.db_models import GeneratedResource, LearningPathPlan, StudentProfile, User
from schemas.ai_tutor import AiTutorChatRequest
from schemas.oj_assistant import OjAssistantRequest
from schemas.evaluation import LearningEvaluationResponse, PersonaLearningPatchRequest
from schemas.learning_path import LearningPathPlanResponse, LearningPathReplanRequest, PathStepItem
from schemas.persona import ChatHistoryItem, PersonaDimensions, PersonaProfileResponse
from schemas.resources import (
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
from services.orchestrator.pipeline_context import PipelineContext
from services.orchestrator.workflow import resource_workflow
from services.safety.content_filter import content_filter

_persona = PersonaAgent()
_tutor = TutorAgent()
_oj = OjAssistantAgent()
_path = LearningPathAgent()


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
    dims = PersonaDimensions.model_validate(
        {k: str(raw.get(k, "") or "") for k in PersonaDimensions.model_fields}
    )
    updated = row.updated_at.isoformat() if row.updated_at else None
    return PersonaProfileResponse(
        summary=row.summary or "",
        dimensions=dims,
        updated_at=updated,
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
        "learning_goal": "学习目标",
        "cognitive_style": "认知风格",
        "weak_points": "薄弱点",
        "pace_preference": "学习节奏",
        "interest_focus": "兴趣方向",
        "preferred_modalities": "偏好模态",
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
            existing_dims = PersonaDimensions.model_validate(
                {
                    k: str((row.dimensions or {}).get(k, ""))
                    for k in PersonaDimensions.model_fields
                }
            )
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
        dims = PersonaDimensions.model_validate(row.dimensions or {})
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
            existing = PersonaDimensions.model_validate(
                {
                    k: str((row.dimensions or {}).get(k, ""))
                    for k in PersonaDimensions.model_fields
                }
            )
            existing_conf = dict((row.dimensions or {}).get("_confidence") or {})
        summary, dims, confidence, missing = await _persona.extract_dimensions(
            history, existing=existing, existing_confidence=existing_conf
        )
        if row is None:
            row = StudentProfile(user_id=user.id)
            db.add(row)
        row.summary = summary
        payload = dims.model_dump()
        payload["_confidence"] = confidence
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
            "  RAG[KnowledgeRetriever<br/>BM25检索] --> GEN[Role Agent<br/>生成内容]\n"
            "  GEN --> VERIFY{ContentVerifier<br/>校验}\n"
            "  VERIFY -->|passed| SAFETY[ContentSafety]\n"
            "  VERIFY -->|failed 最多2次| GEN\n"
            "  SAFETY --> STORE{落库}\n"
            "  STORE -->|verified| PUB[已校验发布]\n"
            "  STORE -->|draft| DRAFT[草稿待校验]\n"
            "  DOC[DocAgent] -.摘要.-> QUIZ[QuizAgent]\n"
            "  DOC -.摘要.-> MAP[MindMapAgent]\n"
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
    ) -> LearningPathPlanResponse:
        profile_row = db.get(StudentProfile, user.id)
        profile_block = _format_profile_block(profile_row)
        plan_data = await _path.plan(profile_block=profile_block, request=body)

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
        }
        row.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(row)
        return _path_plan_response(row)

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
        meta = {"topic": body.topic, "module_key": body.module_key, **gen_meta}
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
        profile_row = db.get(StudentProfile, user.id)
        path_row = db.get(LearningPathPlan, user.id)
        weak_hint = ""
        if profile_row and profile_row.dimensions:
            weak_hint = str(profile_row.dimensions.get("weak_points", ""))
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

        priority_types = ["exercises", "document", "mindmap", "code_case", "reading", "video_script"]

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
        yield _sse({"type": "resource", "resource": item.model_dump(), "percent": 100})
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

    async def generate_all_resources_stream(
        self,
        db: Session,
        user: User,
        *,
        topic: str,
        module_key: str = "",
        focus_hint: str = "",
    ) -> AsyncIterator[str]:
        """SSE：依次生成六类资源，Agent 间传递协作上下文。"""
        types: list[ResourceType] = [
            "document",
            "mindmap",
            "exercises",
            "reading",
            "code_case",
            "video_script",
        ]
        total = len(types)
        pipe_ctx = PipelineContext()
        for idx, rtype in enumerate(types, start=1):
            meta = RESOURCE_AGENT_META[rtype]
            pct = int((idx - 1) / total * 100)
            yield _sse(
                {
                    "type": "progress",
                    "step": idx,
                    "total": total,
                    "percent": pct,
                    "resource_type": rtype,
                    "agent_name": meta["agent_name"],
                    "label": meta["label"],
                }
            )
            req = ResourceGenerateRequest(
                resource_type=rtype,
                topic=topic,
                module_key=module_key,
                focus_hint=focus_hint,
            )

            events: list[dict] = []

            async def capture(ev: dict) -> None:
                events.append(ev)

            item = await self.generate_resource(
                db, user, req, emit=capture, pipeline_ctx=pipe_ctx
            )
            for ev in events:
                if ev.get("type") == "workflow":
                    ev["percent"] = int(idx / total * 100)
                yield _sse(ev)
            yield _sse(
                {
                    "type": "collaboration",
                    "log": pipe_ctx.collaboration_log[-5:],
                }
            )
            yield _sse({"type": "resource", "resource": item.model_dump(), "percent": int(idx / total * 100)})
        yield _sse({"type": "done", "percent": 100})


def _path_plan_response(row: LearningPathPlan) -> LearningPathPlanResponse:
    steps = [PathStepItem.model_validate(s) for s in (row.steps or [])]
    return LearningPathPlanResponse(
        agent_name="学习路径 Agent",
        summary=row.summary or "",
        rationale=row.rationale or "",
        next_module_key=row.next_module_key,
        ordered_keys=list(row.ordered_keys or []),
        steps=steps,
        updated_at=row.updated_at.isoformat() if row.updated_at else None,
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
