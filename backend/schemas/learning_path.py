from pydantic import BaseModel, Field


class ModuleProgressInput(BaseModel):
    key: str = Field(max_length=64)
    label: str = Field(max_length=64)
    phase: str = Field(max_length=32)
    available: bool = True
    percent: int = Field(ge=0, le=100, default=0)
    done_count: int = Field(default=0, ge=0)
    total_count: int = Field(default=0, ge=0)


class LearningPathReplanRequest(BaseModel):
    modules: list[ModuleProgressInput] = Field(default_factory=list)
    overall_percent: int = Field(default=0, ge=0, le=100)


class PathStepItem(BaseModel):
    module_key: str
    rank: int
    reason: str = ""
    phase: str = ""


class LearningPathPlanResponse(BaseModel):
    agent_name: str = "学习路径 Agent"
    summary: str = ""
    rationale: str = ""
    next_module_key: str | None = None
    ordered_keys: list[str] = Field(default_factory=list)
    steps: list[PathStepItem] = Field(default_factory=list)
    updated_at: str | None = None
