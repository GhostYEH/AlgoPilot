import asyncio

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from core.config import settings
from schemas.tts import TtsSynthesizeRequest
from services.tts import synthesize_speech

router = APIRouter()


@router.post("/synthesize")
async def tts_synthesize(body: TtsSynthesizeRequest) -> Response:
    if not settings.tts_configured:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "语音合成未配置：请在 backend/.env 设置 DASHSCOPE_API_KEY",
        )
    try:
        audio = await asyncio.to_thread(synthesize_speech, body.text, voice=body.voice)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            f"CosyVoice 合成失败：{exc}",
        ) from exc

    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={"Content-Disposition": 'inline; filename="speech.mp3"'},
    )
