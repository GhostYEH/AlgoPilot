from typing import Literal

from pydantic import BaseModel, Field

ResourceType = Literal[
    "document",
    "mindmap",
    "exercises",
    "reading",
    "code_case",
    "video_script",
]

RESOURCE_AGENT_META: dict[str, dict[str, str]] = {
    "document": {"agent_name": "DocAgent", "label": "讲解文档"},
    "mindmap": {"agent_name": "MindMapAgent", "label": "思维导图"},
    "exercises": {"agent_name": "QuizAgent", "label": "练习题单"},
    "reading": {"agent_name": "ReadingAgent", "label": "拓展阅读"},
    "code_case": {"agent_name": "CodeAgent", "label": "代码案例"},
    "video_script": {"agent_name": "VideoAgent", "label": "视频脚本"},
}


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


class ResourceListResponse(BaseModel):
    items: list[GeneratedResourceItem]
