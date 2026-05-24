from typing import Literal

from pydantic import BaseModel, Field

PROFILE_DIMENSION_KEYS = (
    "knowledge_base",
    "learning_goal",
    "cognitive_style",
    "weak_points",
    "pace_preference",
    "interest_focus",
    "preferred_modalities",
)


class ChatHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class PersonaDimensions(BaseModel):
    """学习画像七维（赛题要求不少于六维）。"""

    knowledge_base: str = ""
    learning_goal: str = ""
    cognitive_style: str = ""
    weak_points: str = ""
    pace_preference: str = ""
    interest_focus: str = ""
    preferred_modalities: str = ""


class PersonaChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatHistoryItem] = Field(default_factory=list, max_length=30)


class PersonaProfileResponse(BaseModel):
    summary: str = ""
    dimensions: PersonaDimensions
    updated_at: str | None = None
    dimension_confidence: dict[str, str] = Field(
        default_factory=dict,
        description="explicit=用户明确提供，inferred=模型推断",
    )
    coverage_missing: list[str] = Field(
        default_factory=list,
        description="仍待补全的维度 key",
    )


class PersonaSyncResponse(BaseModel):
    profile: PersonaProfileResponse
    message: str = "画像已更新"
