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
    prerequisites: list[str] = Field(default_factory=list, description="前置 module_key 列表")
    difficulty: str = Field(default="标准", description="入门 | 标准 | 进阶")
    is_remediation: bool = Field(default=False, description="是否为学情降级临时插播节点")
    explain: str = Field(
        default="",
        description="个性化推荐理由，结合画像维度、掌握度、OJ 表现等生成",
    )


class LearningPathPlanResponse(BaseModel):
    agent_name: str = "学习路径 Agent"
    summary: str = ""
    rationale: str = ""
    next_module_key: str | None = None
    ordered_keys: list[str] = Field(default_factory=list)
    steps: list[PathStepItem] = Field(default_factory=list)
    updated_at: str | None = None
    remediation_inserted: bool = Field(
        default=False,
        description="本次规划是否插入了降级巩固节点",
    )
