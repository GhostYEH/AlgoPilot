from typing import Any

from pydantic import BaseModel, Field


class LearningProgressOut(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)


class LearningProgressUpdate(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)
