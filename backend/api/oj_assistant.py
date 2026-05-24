"""刷题页智能体：经 Orchestrator 调度 OjAssistantAgent。"""

from fastapi import APIRouter

from schemas.oj_assistant import OjAssistantRequest, OjAssistantResponse
from services.orchestrator import orchestrator

router = APIRouter()


@router.post("/assistant", response_model=OjAssistantResponse)
async def oj_assistant(body: OjAssistantRequest) -> OjAssistantResponse:
    reply = await orchestrator.oj_assistant(body)
    return OjAssistantResponse(reply=reply)
