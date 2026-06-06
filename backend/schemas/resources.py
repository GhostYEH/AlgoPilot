from typing import Literal

from pydantic import BaseModel, Field

ResourceType = Literal[
    "document",
    "mindmap",
    "exercises",
    "code_case",
    "trace_animation",
    "reading",
]

# 赛题展示资源 ↔ 角色 Agent
RESOURCE_AGENT_META: dict[str, dict[str, str]] = {
    "document": {
        "agent_name": "ConceptAgent",
        "label": "概念讲解",
        "role": "概念导师",
    },
    "mindmap": {
        "agent_name": "GraphAgent",
        "label": "知识思维导图",
        "role": "拓扑专家",
    },
    "exercises": {
        "agent_name": "QuizAgent",
        "label": "个性化题单",
        "role": "考题官",
    },
    "code_case": {
        "agent_name": "ScenarioAgent",
        "label": "剧本沙盒",
        "role": "互动编剧",
    },
    "trace_animation": {
        "agent_name": "TraceAgent",
        "label": "轨迹动画",
        "role": "动画总导演",
    },
    "reading": {
        "agent_name": "ReadingAgent",
        "label": "分层拓展阅读",
        "role": "学术/工程阅读策展人",
    },
}

# 批量生成流水线
CORE_RESOURCE_PIPELINE: list[ResourceType] = [
    "document",
    "mindmap",
    "exercises",
    "code_case",
    "trace_animation",
    "reading",
]

PARALLEL_PHASES: list[list[ResourceType]] = [
    ["document"],
    ["mindmap", "exercises"],
    ["code_case"],
    ["trace_animation", "reading"],
]


class AgentLogEntry(BaseModel):
    agent: str
    role: str = ""
    action: str
    detail: str = ""
    resource_type: str = ""
    status: str = "done"


class ResourceGenerateRequest(BaseModel):
    resource_type: ResourceType
    topic: str = Field(default="数据结构与算法", max_length=200)
    module_key: str = Field(default="", max_length=64)
    focus_hint: str = Field(default="", max_length=500)


class ResourceGenerateAllRequest(BaseModel):
    """批量 generate-all：无需指定 resource_type。"""

    topic: str = Field(default="数据结构与算法", max_length=200)
    module_key: str = Field(default="", max_length=64)
    focus_hint: str = Field(default="", max_length=500)


class GeneratedResourceItem(BaseModel):
    id: int
    resource_type: str
    agent_name: str
    title: str
    content: str
    meta: dict = Field(default_factory=dict)
    created_at: str
    verification: dict | None = Field(
        default=None,
        description="防幻觉与内容安全校验证据（与 meta.verification 同步）",
    )
    explain: str = Field(
        default="",
        description="个性化推荐理由，结合画像维度、掌握度、OJ 表现等生成",
    )


class ResourceGenerateResponse(BaseModel):
    resource: GeneratedResourceItem
    agent_logs: list[AgentLogEntry] = Field(
        default_factory=list,
        description="本次生成各 Agent 协同分工日志",
    )


class ResourceListResponse(BaseModel):
    items: list[GeneratedResourceItem]
