"""多智能体注册表（赛题角色对齐，供编排层与文档引用）。"""

from __future__ import annotations

from typing import TypedDict


class AgentMeta(TypedDict):
    id: str
    display_name: str
    role: str
    layer: str


# layer: profiling | resource | path | tutor | safety | eval
AGENT_REGISTRY: list[AgentMeta] = [
    {"id": "ProfilingAgent", "display_name": "ProfilingAgent", "role": "对话式画像构建", "layer": "profiling"},
    {"id": "DocAgent", "display_name": "DocAgent", "role": "课程讲解文档", "layer": "resource"},
    {"id": "MindMapAgent", "display_name": "MindMapAgent", "role": "思维导图", "layer": "resource"},
    {"id": "QuizAgent", "display_name": "QuizAgent", "role": "个性化题库", "layer": "resource"},
    {"id": "ReadingAgent", "display_name": "ReadingAgent", "role": "拓展阅读", "layer": "resource"},
    {"id": "CodeAgent", "display_name": "CodeAgent", "role": "代码实操案例", "layer": "resource"},
    {"id": "VideoAgent", "display_name": "VideoAgent", "role": "教学视频/动画脚本", "layer": "resource"},
    {"id": "LearningPathAgent", "display_name": "LearningPathAgent", "role": "学习路径规划", "layer": "path"},
    {"id": "TutorAgent", "display_name": "TutorAgent", "role": "智能辅导答疑", "layer": "tutor"},
    {"id": "OjAssistantAgent", "display_name": "OjAssistantAgent", "role": "OJ 刷题辅导", "layer": "tutor"},
    {"id": "OjDiagnosisAgent", "display_name": "OjDiagnosisAgent", "role": "OJ AI 深度诊断", "layer": "tutor"},
    {"id": "ContentVerifierAgent", "display_name": "ContentVerifierAgent", "role": "防幻觉校验", "layer": "safety"},
    {"id": "EvaluationAgent", "display_name": "EvaluationAgent", "role": "学习效果评估", "layer": "eval"},
    {"id": "KnowledgeRetriever", "display_name": "KnowledgeRetriever", "role": "知识库检索", "layer": "safety"},
]

RESOURCE_TYPE_TO_AGENT: dict[str, str] = {
    "document": "DocAgent",
    "mindmap": "MindMapAgent",
    "exercises": "QuizAgent",
    "reading": "ReadingAgent",
    "code_case": "CodeAgent",
    "video_script": "VideoAgent",
}


def list_agents() -> list[AgentMeta]:
    return list(AGENT_REGISTRY)


def agent_for_resource(resource_type: str) -> str:
    return RESOURCE_TYPE_TO_AGENT.get(resource_type, "DocAgent")
