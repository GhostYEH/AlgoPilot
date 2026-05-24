from pydantic import BaseModel, Field


class EvaluationDimensionScore(BaseModel):
    key: str
    label: str
    score: int = Field(ge=0, le=100)


class LearningEvaluationResponse(BaseModel):
    agent_name: str = "EvaluationAgent"
    overall_score: int = Field(ge=0, le=100, default=0)
    dimensions: list[EvaluationDimensionScore] = Field(default_factory=list)
    weak_module_keys: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    narrative: str = ""
    push_strategy: str = ""


class PersonaLearningSignal(BaseModel):
    """随学随新：学习行为信号。"""

    event_type: str = Field(max_length=32, description="section_done | oj_submit | module_visit")
    module_key: str = Field(default="", max_length=64)
    detail: str = Field(default="", max_length=500)


class PersonaLearningPatchRequest(BaseModel):
    signals: list[PersonaLearningSignal] = Field(default_factory=list, max_length=20)
    weak_module_keys: list[str] = Field(default_factory=list, max_length=12)
