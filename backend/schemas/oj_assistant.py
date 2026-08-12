from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class OjAssistantRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    mode: Literal["ds_hint", "code_hint"]
    problem_slug: str = Field(max_length=128, validation_alias=AliasChoices("problem_slug", "problemSlug"))
    problem_title: str = Field(max_length=200, validation_alias=AliasChoices("problem_title", "problemTitle"))
    problem_description: str = Field(max_length=8000)
    difficulty: str = Field(default="medium", max_length=32)
    judge_mode: str = Field(default="stdio", max_length=32)
    entry_method: str | None = Field(default=None, max_length=64)
    language: str = Field(default="cpp", max_length=16)
    user_code: str = Field(default="", max_length=12000)
    samples_text: str = Field(default="", max_length=4000)


class OjAssistantResponse(BaseModel):
    reply: str
