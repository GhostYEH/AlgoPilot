"""学习事件日志 API。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import get_current_user
from models.db_models import User
from schemas.events import EventLogQuery, LearningEvent
from services.events.event_bus import event_bus

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/recent", response_model=EventLogQuery)
def list_recent_events(
    event_type: str = Query(default=""),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
) -> EventLogQuery:
    items = event_bus.list_recent(user_id=user.id, event_type=event_type, limit=limit)
    return EventLogQuery(items=items, total=len(items))


@router.get("/{event_id}", response_model=LearningEvent)
def get_event(
    event_id: str,
    user: User = Depends(get_current_user),
) -> LearningEvent:
    event = event_bus.get(event_id)
    if event is None or event.user_id != user.id:
        raise HTTPException(404, "事件不存在")
    return event
