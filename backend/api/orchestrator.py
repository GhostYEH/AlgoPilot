"""编排层 API：画像对话（流式）、画像同步、资源生成。"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_optional_user
from core.database import get_db
from models.db_models import User
from schemas.ai_tutor import AiTutorChatRequest, AiTutorChatResponse
from schemas.oj_assistant import OjAssistantRequest, OjAssistantResponse
from schemas.evaluation import (
    LearningEvaluationResponse,
    OjStruggleEvaluationRequest,
    OjStruggleEvaluationResponse,
    PersonaLearningPatchRequest,
)
from schemas.persona import ChatHistoryItem, PersonaChatRequest, PersonaProfileResponse, PersonaSyncResponse
from schemas.learning_path import LearningPathPlanResponse, LearningPathReplanRequest
from schemas.resources import (
    AgentLogEntry,
    ResourceGenerateRequest,
    ResourceGenerateResponse,
    ResourceListResponse,
)
from services.orchestrator import orchestrator

router = APIRouter()


def _agent_logs_from_item(item) -> list[AgentLogEntry]:
    raw = (item.meta or {}).get("agent_logs") or []
    logs: list[AgentLogEntry] = []
    for entry in raw:
        try:
            logs.append(AgentLogEntry.model_validate(entry))
        except Exception:
            continue
    return logs



def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.get("/persona/profile", response_model=PersonaProfileResponse)
def get_persona_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PersonaProfileResponse:
    return orchestrator.get_profile(db, user)


@router.get("/persona/history")
def get_persona_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    items = orchestrator.get_persona_history(db, user)
    return {"history": [{"role": h.role, "content": h.content} for h in items]}


@router.post("/persona/chat")
async def persona_chat_stream(
    body: PersonaChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """流式对话；SSE 事件：token / done / error。"""

    async def event_gen():
        parts: list[str] = []
        try:
            async for chunk in orchestrator.persona_chat_stream(
                db, user, message=body.message, history=body.history
            ):
                parts.append(chunk)
                yield _sse({"type": "token", "content": chunk})
            reply = "".join(parts)
            new_history = [
                *body.history,
                ChatHistoryItem(role="user", content=body.message),
                ChatHistoryItem(role="assistant", content=reply),
            ]
            orchestrator.save_persona_history(db, user, new_history)
            yield _sse({"type": "done", "content": reply})
        except Exception as exc:
            yield _sse({"type": "error", "message": str(exc)})

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/persona/sync", response_model=PersonaSyncResponse)
async def sync_persona_profile(
    body: PersonaChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PersonaSyncResponse:
    """根据对话历史抽取 JSON 画像并入库。"""
    history = [
        *body.history,
        ChatHistoryItem(role="user", content=body.message),
    ] if body.message else list(body.history)
    profile = await orchestrator.sync_persona_profile(db, user, history=history)
    return PersonaSyncResponse(profile=profile)


@router.post("/persona/patch-from-learning", response_model=PersonaProfileResponse)
def patch_persona_from_learning(
    body: PersonaLearningPatchRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PersonaProfileResponse:
    """随学随新：根据学习行为信号更新画像（无需完整对话）。"""
    return orchestrator.patch_persona_from_learning(db, user, body)


@router.post("/persona/sync-from-stored", response_model=PersonaSyncResponse)
async def sync_persona_from_stored(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PersonaSyncResponse:
    history = orchestrator.get_persona_history(db, user)
    if not history:
        return PersonaSyncResponse(
            profile=orchestrator.get_profile(db, user),
            message="暂无对话记录，请先与画像 Agent 对话",
        )
    profile = await orchestrator.sync_persona_profile(db, user, history=history)
    return PersonaSyncResponse(profile=profile)


@router.get("/agents")
def list_agents() -> dict:
    return {
        "agents": orchestrator.list_agents(),
        "resource_pipeline": orchestrator.describe_resource_pipeline(),
        "framework_note": "自研 DAG 编排：条件路由 + 校验闭环 + Agent 协作上下文传递",
        "dag_mermaid": orchestrator.describe_resource_dag_mermaid(),
    }


@router.post("/tutor/chat", response_model=AiTutorChatResponse)
async def orchestrator_tutor_chat(
    body: AiTutorChatRequest,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> AiTutorChatResponse:
    profile_block = ""
    if user:
        from models.db_models import StudentProfile
        from services.orchestrator.core import _format_profile_block as fmt

        row = db.get(StudentProfile, user.id)
        profile_block = fmt(row)
    reply = await orchestrator.tutor_chat(body, profile_block=profile_block)
    return AiTutorChatResponse(reply=reply)


@router.post("/tutor/chat/stream")
async def orchestrator_tutor_chat_stream(
    body: AiTutorChatRequest,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    profile_block = ""
    if user:
        from models.db_models import StudentProfile
        from services.orchestrator.core import _format_profile_block

        row = db.get(StudentProfile, user.id)
        profile_block = _format_profile_block(row)

    async def event_gen():
        parts: list[str] = []
        try:
            async for chunk in orchestrator.tutor_chat_stream(body, profile_block=profile_block):
                parts.append(chunk)
                yield _sse({"type": "token", "content": chunk})
            yield _sse({"type": "done", "content": "".join(parts)})
        except Exception as exc:
            yield _sse({"type": "error", "message": str(exc)})

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/oj/assistant", response_model=OjAssistantResponse)
async def orchestrator_oj_assistant(body: OjAssistantRequest) -> OjAssistantResponse:
    reply = await orchestrator.oj_assistant(body)
    return OjAssistantResponse(reply=reply)


@router.get("/learning-path/plan")
def get_learning_path_plan(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    plan = orchestrator.get_learning_path_plan(db, user)
    return {"plan": plan}


@router.post("/learning-path/replan", response_model=LearningPathPlanResponse)
async def replan_learning_path(
    body: LearningPathReplanRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LearningPathPlanResponse:
    return await orchestrator.replan_learning_path(db, user, body)


@router.get("/resources/recommendations", response_model=ResourceListResponse)
def recommend_resources(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    module_key: str = Query(default=""),
    limit: int = Query(default=6, ge=1, le=12),
) -> ResourceListResponse:
    items = orchestrator.recommend_resources(db, user, module_key=module_key, limit=limit)
    return ResourceListResponse(items=items)


@router.post("/evaluation", response_model=LearningEvaluationResponse)
async def evaluate_learning(
    body: LearningPathReplanRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LearningEvaluationResponse:
    return await orchestrator.evaluate_learning(db, user, body)


@router.post("/evaluation/oj-struggle", response_model=OjStruggleEvaluationResponse)
async def evaluate_oj_struggle(
    body: OjStruggleEvaluationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OjStruggleEvaluationResponse:
    """OJ 连续 WA/RE/TLE → EvaluatorAgent 通知 PlannerAgent 插入降级巩固节点。"""
    return await orchestrator.evaluate_oj_struggle_and_replan(db, user, body)


@router.get("/resources", response_model=ResourceListResponse)
def list_resources(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResourceListResponse:
    return ResourceListResponse(items=orchestrator.list_resources(db, user))


@router.post("/resources/generate", response_model=ResourceGenerateResponse)
async def generate_resource(
    body: ResourceGenerateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    stream: bool = Query(default=False, description="true 时返回 SSE 流"),
):
    if stream:
        async def event_gen():
            try:
                async for line in orchestrator.generate_resource_stream(db, user, body):
                    yield line
            except ValueError as exc:
                yield _sse({"type": "error", "message": str(exc)})
            except Exception as exc:
                yield _sse({"type": "error", "message": str(exc)})

        return StreamingResponse(
            event_gen(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    try:
        item = await orchestrator.generate_resource(db, user, body)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return ResourceGenerateResponse(resource=item, agent_logs=_agent_logs_from_item(item))


@router.delete("/resources/{resource_id}")
def delete_resource(
    resource_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if not orchestrator.delete_resource(db, user, resource_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "资源不存在")
    return {"ok": True}


@router.patch("/resources/{resource_id}/favorite")
def favorite_resource(
    resource_id: int,
    favorited: bool = Query(default=True),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResourceGenerateResponse:
    item = orchestrator.set_resource_favorite(db, user, resource_id, favorited)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "资源不存在")
    return ResourceGenerateResponse(resource=item, agent_logs=_agent_logs_from_item(item))


@router.post("/resources/generate-all")
async def generate_all_resources_stream(
    body: ResourceGenerateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """流式批量生成五类核心个性化资源（Concept/Graph/Quiz/Scenario/Trace）。"""

    async def event_gen():
        try:
            async for line in orchestrator.generate_all_resources_stream(
                db,
                user,
                topic=body.topic,
                module_key=body.module_key,
                focus_hint=body.focus_hint,
            ):
                yield line
        except Exception as exc:
            yield _sse({"type": "error", "message": str(exc)})

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
