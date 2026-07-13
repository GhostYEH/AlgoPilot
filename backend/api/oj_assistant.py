"""刷题页智能体：经 Orchestrator 调度 OjAssistantAgent（非流式 + 流式）。"""

import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from schemas.oj_assistant import OjAssistantRequest, OjAssistantResponse
from services.orchestrator import orchestrator

router = APIRouter()


@router.post("/assistant", response_model=OjAssistantResponse)
async def oj_assistant(body: OjAssistantRequest) -> OjAssistantResponse:
    reply = await orchestrator.oj_assistant(body)
    return OjAssistantResponse(reply=reply)


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/assistant/stream")
async def oj_assistant_stream(body: OjAssistantRequest):
    """流式输出 OJ 助手回复（SSE）。

    事件格式：
      data: {"type": "token", "content": "..."}   逐段文本
      data: {"type": "done", "content": "全文"}    完成
      data: {"type": "error", "message": "..."}    出错
    """

    async def event_gen():
        parts: list[str] = []
        try:
            async for chunk in orchestrator.oj_assistant_stream(body):
                parts.append(chunk)
                yield _sse({"type": "token", "content": chunk})
            yield _sse({"type": "done", "content": "".join(parts)})
        except Exception as exc:  # noqa: BLE001
            yield _sse({"type": "error", "message": str(exc)})

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
