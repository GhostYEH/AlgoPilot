from pydantic import BaseModel, Field

from schemas.learning_path import ModuleProgressInput


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


class OjStruggleEvaluationRequest(BaseModel):
    """OJ 连续受挫触发的学情评估请求。"""

    module_key: str = Field(default="", max_length=64)
    problem_slug: str = Field(default="", max_length=128)
    knowledge_point: str = Field(default="", max_length=128, description="当前知识点，如「动态规划」")
    verdict: str = Field(default="WA", max_length=8)
    consecutive_failures: int = Field(default=3, ge=1, le=20)
    error_pattern: str = Field(default="", max_length=256, description="如「边界溢出」「下标越界」")
    overall_percent: int = Field(default=0, ge=0, le=100)
    modules: list[ModuleProgressInput] = Field(default_factory=list)


class AgentLogItem(BaseModel):
    agent: str
    action: str
    detail: str = ""
    status: str = "done"


class OjStruggleEvaluationResponse(BaseModel):
    agent_name: str = "EvaluationAgent"
    struggle_detected: bool = False
    consecutive_failures: int = 0
    remediation_module_key: str | None = None
    remediation_label: str = ""
    planner_notified: bool = False
    path_updated: bool = False
    agent_logs: list[AgentLogItem] = Field(default_factory=list)
    plan_summary: str = ""
