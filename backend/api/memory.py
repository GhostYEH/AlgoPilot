"""学生学习记忆 API。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.deps import get_current_user
from core.database import get_db
from models.db_models import User
from schemas.memory import (
    LearningEvidenceItem,
    MemoryEventCreateRequest,
    MemoryEventCreateResponse,
    MemoryRecentResponse,
    MemorySummaryResponse,
)
from services.memory.memory_service import MemoryService
from services.memory.memory_summarizer import get_summary_payload

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("/events", response_model=MemoryEventCreateResponse)
def create_memory_event(
    body: MemoryEventCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MemoryEventCreateResponse:
    svc = MemoryService(db)
    event = svc.record_event(user.id, body)
    return MemoryEventCreateResponse(event=event)


@router.get("/summary", response_model=MemorySummaryResponse)
def get_memory_summary(
    course_id: str = Query(default="data_structures_algorithms"),
    chapter_id: str = Query(default=""),
    skill_id: str = Query(default=""),
    limit: int = Query(default=12, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MemorySummaryResponse:
    payload = get_summary_payload(
        db,
        user.id,
        course_id=course_id,
        chapter_id=chapter_id,
        skill_id=skill_id,
        limit=limit,
    )
    recent = [
        LearningEvidenceItem.model_validate(x) for x in payload.get("recent_evidence") or []
    ]
    return MemorySummaryResponse(
        course_id=payload.get("course_id", course_id),
        learning_memory_summary=payload.get("learning_memory_summary", ""),
        weak_patterns=payload.get("weak_patterns", []),
        recent_count=int(payload.get("recent_count", 0)),
        dimension_evidence=payload.get("dimension_evidence", {}),
        update_reason=payload.get("update_reason", ""),
        recent_evidence=recent,
        generated_at=payload.get("generated_at", ""),
    )


@router.get("/recent", response_model=MemoryRecentResponse)
def get_recent_memories(
    course_id: str = Query(default="data_structures_algorithms"),
    chapter_id: str = Query(default=""),
    skill_id: str = Query(default=""),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MemoryRecentResponse:
    items = MemoryService(db).list_recent(
        user.id,
        course_id=course_id,
        chapter_id=chapter_id,
        skill_id=skill_id,
        limit=limit,
    )
    return MemoryRecentResponse(items=items, total=len(items))
