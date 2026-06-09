from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LearningLoopSummary(BaseModel):
    demo_mode: bool = False
    data_source: str
    profile_summary: dict[str, Any] = Field(default_factory=dict)
    current_path: dict[str, Any] = Field(default_factory=dict)
    generated_resources_count: int = 0
    recent_oj_status: dict[str, Any] = Field(default_factory=dict)
    recent_trace_summary: dict[str, Any] = Field(default_factory=dict)
    evaluation_summary: dict[str, Any] = Field(default_factory=dict)
    replan_suggestion: dict[str, Any] = Field(default_factory=dict)
