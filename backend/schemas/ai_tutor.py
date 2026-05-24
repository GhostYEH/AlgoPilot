from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class ChatHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class LearnSectionContext(BaseModel):
    id: str
    title: str
    subtitle: str = ""
    difficulty: str = ""
    est_minutes: int = 0
    keywords: list[str] = Field(default_factory=list)
    overview: str | None = None
    points: list[str] = Field(default_factory=list)
    topic_blocks: list[dict] = Field(default_factory=list)
    pitfalls: list[str] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list)
    complexity_hint: str | None = None
    code_sketch: str | None = None


class AiTutorChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatHistoryItem] = Field(default_factory=list, max_length=20)
    module_key: str = Field(
        max_length=64,
        validation_alias=AliasChoices("module_key", "moduleKey"),
    )
    module_title: str = Field(
        max_length=200,
        validation_alias=AliasChoices("module_title", "moduleTitle"),
    )
    chapter_tag: str = Field(
        max_length=64,
        validation_alias=AliasChoices("chapter_tag", "chapterTag"),
    )
    module_intro: str = Field(
        max_length=4000,
        validation_alias=AliasChoices("module_intro", "moduleIntro"),
    )
    section: LearnSectionContext


class AiTutorChatResponse(BaseModel):
    reply: str
