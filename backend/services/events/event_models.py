"""学习事件模型。"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

EventType = Literal[
    "on_profile_updated",
    "on_resource_generated",
    "on_quiz_completed",
    "on_oj_submission_failed",
    "on_oj_submission_accepted",
    "on_trace_diagnosed",
    "on_mastery_recalculated",
    "on_path_adjusted",
    "on_gamified_practice_completed",
]

EventStatus = Literal["pending", "processing", "done", "partial", "failed"]


class AgentLogEntry(BaseModel):
    agent: str
    action: str
    detail: str = ""
    status: str = "done"


class LearningEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    event_type: str
    user_id: int
    course_id: str = "data_structures_algorithms"
    chapter_id: str = ""
    skill_id: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    handled_by: list[str] = Field(default_factory=list)
    status: EventStatus = "pending"
    agent_logs: list[AgentLogEntry] = Field(default_factory=list)
    handler_errors: list[str] = Field(default_factory=list)

    def log(
        self,
        agent: str,
        action: str,
        detail: str = "",
        *,
        status: str = "done",
    ) -> None:
        self.agent_logs.append(AgentLogEntry(agent=agent, action=action, detail=detail, status=status))


class EventPublishResult(BaseModel):
    event: LearningEvent
    ok: bool = True
    persisted: bool = False

    @property
    def agent_logs(self) -> list[AgentLogEntry]:
        return self.event.agent_logs


class EventLogQuery(BaseModel):
    items: list[LearningEvent] = Field(default_factory=list)
    total: int = 0
