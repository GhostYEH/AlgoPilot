from typing import Literal

from pydantic import BaseModel, Field

ResourceType = Literal[
    "document",
    "mindmap",
    "exercises",
    "code_case",
    "trace_animation",
    # 兼容旧库记录
    "reading",
    "video_script",
]

# 赛题五类核心资源 ↔ 角色 Agent
RESOURCE_AGENT_META: dict[str, dict[str, str]] = {
    "document": {
        "agent_name": "ConceptAgent",
        "label": "概念讲解",
        "role": "概念导师",
    },
    "mindmap": {
        "agent_name": "GraphAgent",
        "label": "知识图谱",
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
    # 旧类型兼容
    "reading": {
        "agent_name": "ConceptAgent",
        "label": "拓展阅读",
        "role": "概念导师",
    },
    "video_script": {
        "agent_name": "TraceAgent",
        "label": "教学动画",
        "role": "动画总导演",
    },
}

# 批量生成流水线（赛题要求的 5 类）
CORE_RESOURCE_PIPELINE: list[ResourceType] = [
    "document",
    "mindmap",
    "exercises",
    "code_case",
    "trace_animation",
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


class GeneratedResourceItem(BaseModel):
    id: int
    resource_type: str
    agent_name: str
    title: str
    content: str
    meta: dict = Field(default_factory=dict)
    created_at: str


class ResourceGenerateResponse(BaseModel):
    resource: GeneratedResourceItem
    agent_logs: list[AgentLogEntry] = Field(
        default_factory=list,
        description="本次生成各 Agent 协同分工日志",
    )


class ResourceListResponse(BaseModel):
    items: list[GeneratedResourceItem]
