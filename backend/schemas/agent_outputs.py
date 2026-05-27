"""Agent 结构化输出 — Pydantic strict 校验与修复前置。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class QuizQuestion(StrictModel):
    type: Literal["choice", "fill", "code"] = "choice"
    stem: str = Field(min_length=1, max_length=800)
    options: list[str] = Field(default_factory=list)
    hint: str = Field(default="", max_length=400)
    focus: str = Field(default="", max_length=120)
    difficulty: Literal["easy", "medium", "hard"] = "medium"

    @model_validator(mode="after")
    def ensure_choice_options(self) -> QuizQuestion:
        if self.type == "choice" and len(self.options) < 2:
            self.options = ["A", "B", "C", "D"]
        return self


class QuizOutput(StrictModel):
    questions: list[QuizQuestion] = Field(min_length=1, max_length=6)


def validate_quiz_payload(data: dict[str, Any]) -> tuple[QuizOutput | None, list[str]]:
    try:
        return QuizOutput.model_validate(data), []
    except ValidationError as e:
        return None, [f"{err['loc']}: {err['msg']}" for err in e.errors()]
