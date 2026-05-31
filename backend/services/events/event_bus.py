"""进程内轻量 EventBus：同步 handler、错误隔离、事件日志。"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from threading import Lock
from typing import Any

from sqlalchemy.orm import Session

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

        return EventPublishResult(event=event, ok=event.status != "failed")

    def list_recent(
        self,
        *,
        user_id: int | None = None,
        event_type: str = "",
        limit: int = 30,
    ) -> list[LearningEvent]:
        with self._lock:
            items = list(self._store)
        if user_id is not None:
            items = [e for e in items if e.user_id == user_id]
        if event_type:
            items = [e for e in items if e.event_type == event_type]
        items.sort(key=lambda e: e.created_at, reverse=True)
        return items[: min(limit, 100)]

    def get(self, event_id: str) -> LearningEvent | None:
        with self._lock:
            for e in reversed(self._store):
                if e.event_id == event_id:
                    return e
        return None

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


event_bus = EventBus()


def register_default_handlers() -> None:
    from services.events import handlers

    handlers.register_handlers(event_bus)


register_default_handlers()
