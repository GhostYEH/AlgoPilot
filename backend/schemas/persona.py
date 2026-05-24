from typing import Literal

from pydantic import BaseModel, Field

# 赛题标准六维动态学生画像
PROFILE_DIMENSION_KEYS = (
    "knowledge_base",
    "cognitive_style",
    "coding_ability",
    "learning_goals",
    "error_preference",
    "grit_level",
)

# 历史维度 → 新维度映射（兼容旧库数据）
_LEGACY_DIMENSION_ALIASES: dict[str, str] = {
    "learning_goal": "learning_goals",
    "weak_points": "error_preference",
    "pace_preference": "grit_level",
    "interest_focus": "learning_goals",
    "preferred_modalities": "cognitive_style",
}


def migrate_dimension_payload(raw: dict | None) -> dict[str, str]:
    """将旧版七维画像 JSON 迁移为赛题六维。"""
    if not raw:
        return {k: "" for k in PROFILE_DIMENSION_KEYS}
    out: dict[str, str] = {}
    for key in PROFILE_DIMENSION_KEYS:
        val = str(raw.get(key, "") or "").strip()
        if val and val not in ("待补充", "暂无", "未知"):
            out[key] = val
    for old_key, new_key in _LEGACY_DIMENSION_ALIASES.items():
        legacy = str(raw.get(old_key, "") or "").strip()
        if not legacy or legacy in ("待补充", "暂无", "未知"):
            continue
        if new_key not in out or not out[new_key]:
            out[new_key] = legacy
        elif legacy not in out[new_key]:
            out[new_key] = f"{out[new_key]}；{legacy}"
    return {k: out.get(k, "") for k in PROFILE_DIMENSION_KEYS}


class ChatHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class PersonaDimensions(BaseModel):
    """学习画像六维（中国软件杯赛题标准）。"""

    knowledge_base: str = Field(default="", description="知识基础")
    cognitive_style: str = Field(default="", description="认知风格，如视觉型/文本型")
    coding_ability: str = Field(default="", description="代码实操能力")
    learning_goals: str = Field(default="", description="学习目标")
    error_preference: str = Field(default="", description="易错点偏好")
    grit_level: str = Field(default="", description="抗挫折心理能力")

    @classmethod
    def from_storage(cls, raw: dict | None) -> "PersonaDimensions":
        return cls.model_validate(migrate_dimension_payload(raw))


class PersonaChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatHistoryItem] = Field(default_factory=list, max_length=30)


class PersonaProfileResponse(BaseModel):
    summary: str = ""
    dimensions: PersonaDimensions
    updated_at: str | None = None
    dimension_scores: dict[str, int] = Field(
        default_factory=dict,
        description="六维量化分值 1-10，用于雷达图与路径规划",
    )
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
