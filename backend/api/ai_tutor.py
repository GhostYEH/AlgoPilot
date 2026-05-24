

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_optional_user
from core.database import get_db
from models.db_models import StudentProfile, User
from schemas.ai_tutor import AiTutorChatRequest, AiTutorChatResponse
from services.orchestrator import orchestrator
from services.orchestrator.core import _format_profile_block

router = APIRouter()


@router.post("/tutor/chat", response_model=AiTutorChatResponse)
async def tutor_chat(
    body: AiTutorChatRequest,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> AiTutorChatResponse:
    profile_block = ""
    if user:
        row = db.get(StudentProfile, user.id)
        profile_block = _format_profile_block(row)
    reply = await orchestrator.tutor_chat(body, profile_block=profile_block)
    return AiTutorChatResponse(reply=reply)
