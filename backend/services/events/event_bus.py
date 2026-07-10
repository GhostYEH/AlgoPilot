"""进程内轻量 EventBus：同步 handler、错误隔离、事件日志。"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from threading import Lock
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from models.db_models import LearningEventLog
from services.events.event_models import EventPublishResult, LearningEvent

HandlerFn = Callable[[Session, LearningEvent], None]

_MAX_STORE = 2000


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[tuple[str, HandlerFn]]] = {}
        self._store: deque[LearningEvent] = deque(maxlen=_MAX_STORE)
        self._lock = Lock()

    def subscribe(self, event_type: str, handler_name: str, handler: HandlerFn) -> None:
        self._handlers.setdefault(event_type, []).append((handler_name, handler))

    def publish(
        self,
        db: Session | None,
        *,
        event_type: str,
        user_id: int,
        payload: dict[str, Any] | None = None,
        course_id: str = "data_structures_algorithms",
        chapter_id: str = "",
        skill_id: str = "",
    ) -> EventPublishResult:
        event = LearningEvent(
            event_type=event_type,
            user_id=user_id,
            course_id=course_id,
            chapter_id=chapter_id,
            skill_id=skill_id,
            payload=dict(payload or {}),
            status="processing",
        )
        event.log("EventBus", "publish", f"事件 {event_type} 已发布", status="running")

        handlers = self._handlers.get(event_type, [])
        for name, fn in handlers:
            try:
                fn(db, event)
                event.handled_by.append(name)
            except Exception as exc:
                event.handler_errors.append(f"{name}: {exc}")
                event.log("EventBus", "handler_error", f"{name} 失败: {exc}", status="error")

        if event.handler_errors:
            event.status = "partial" if event.handled_by else "failed"
        else:
            event.status = "done"
        event.log("EventBus", "complete", f"处理完成 status={event.status}", status="done")

        with self._lock:
            self._store.append(event)

        if db is not None:
            try:
                self._persist(db, event)
            except Exception as exc:
                db.rollback()
                event.handler_errors.append(f"EventStore: {exc}")
                event.log(
                    "EventStore",
                    "persist_error",
                    f"事件日志落库失败: {exc}",
                    status="error",
                )
                event.status = "partial" if event.handled_by else "failed"

        return EventPublishResult(event=event, ok=event.status != "failed")

    def list_recent(
        self,
        *,
        db: Session | None = None,
        user_id: int | None = None,
        event_type: str = "",
        limit: int = 30,
    ) -> list[LearningEvent]:
        if db is not None:
            query = select(LearningEventLog)
            if user_id is not None:
                query = query.where(LearningEventLog.user_id == user_id)
            if event_type:
                query = query.where(LearningEventLog.event_type == event_type)
            query = query.order_by(desc(LearningEventLog.created_at)).limit(min(limit, 100))
            return [self._from_row(row) for row in db.scalars(query).all()]

        with self._lock:
            items = list(self._store)
        if user_id is not None:
            items = [e for e in items if e.user_id == user_id]
        if event_type:
            items = [e for e in items if e.event_type == event_type]
        items.sort(key=lambda e: e.created_at, reverse=True)
        return items[: min(limit, 100)]

    def get(self, event_id: str, *, db: Session | None = None) -> LearningEvent | None:
        if db is not None:
            row = db.get(LearningEventLog, event_id)
            return self._from_row(row) if row is not None else None

        with self._lock:
            for e in reversed(self._store):
                if e.event_id == event_id:
                    return e
        return None

    @staticmethod
    def _persist(db: Session, event: LearningEvent) -> None:
        row = db.get(LearningEventLog, event.event_id)
        if row is None:
            row = LearningEventLog(event_id=event.event_id, user_id=event.user_id)
            db.add(row)
        row.event_type = event.event_type
        row.course_id = event.course_id
        row.chapter_id = event.chapter_id
        row.skill_id = event.skill_id
        row.payload = dict(event.payload)
        row.handled_by = list(event.handled_by)
        row.status = event.status
        row.agent_logs = [item.model_dump() for item in event.agent_logs]
        row.handler_errors = list(event.handler_errors)
        db.commit()

    @staticmethod
    def _from_row(row: LearningEventLog) -> LearningEvent:
        return LearningEvent(
            event_id=row.event_id,
            event_type=row.event_type,
            user_id=row.user_id,
            course_id=row.course_id,
            chapter_id=row.chapter_id,
            skill_id=row.skill_id,
            payload=dict(row.payload or {}),
            created_at=row.created_at.isoformat() if row.created_at else "",
            handled_by=list(row.handled_by or []),
            status=row.status,
            agent_logs=list(row.agent_logs or []),
            handler_errors=list(row.handler_errors or []),
        )

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


event_bus = EventBus()


def register_default_handlers() -> None:
    from services.events import handlers

    handlers.register_handlers(event_bus)


register_default_handlers()
