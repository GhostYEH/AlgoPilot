"""多智能体注册表。"""

from __future__ import annotations

from typing import TypedDict


class AgentMeta(TypedDict):
    id: str
    display_name: str
    role: str
    layer: str


# layer: profiling | resource | path | tutor | safety | eval
AGENT_REGISTRY: list[AgentMeta] = [
    {
        "id": "ProfilingAgent",
        "display_name": "ProfilingAgent",
        "role": "六维动态学生画像构建",
        "layer": "profiling",
    },
    {
        "id": "ConceptAgent",
        "display_name": "ConceptAgent",
        "role": "概念导师 · 定制化课程讲解",
        "layer": "resource",
    },
    {
        "id": "GraphAgent",
        "display_name": "GraphAgent",
        "role": "拓扑专家 · 知识思维导图",
        "layer": "resource",
    },
    {
        "id": "ScenarioAgent",
        "display_name": "ScenarioAgent",
        "role": "互动编剧 · 剧本沙盒",
        "layer": "resource",
    },
    {
        "id": "TraceAgent",
        "display_name": "TraceAgent",
        "role": "动画总导演 · 执行轨迹动画",
        "layer": "resource",
    },
    {
        "id": "ReadingAgent",
        "display_name": "ReadingAgent",
        "role": "学术/工程阅读策展人 · 基础/进阶/挑战分层阅读",
        "layer": "resource",
    },
    {
        "id": "ExerciseAgent",
        "display_name": "ExerciseAgent",
        "role": "练习导师 · 选择/填空/代码题个性化题单",
        "layer": "resource",
    },
    {
        "id": "PptAgent",
        "display_name": "PptAgent",
        "role": "演示文稿资源生成扩展节点",
        "layer": "resource",
    },
    {
        "id": "VideoScriptAgent",
        "display_name": "VideoScriptAgent",
        "role": "教学短视频脚本生成扩展节点",
        "layer": "resource",
    },
    {"id": "PlannerAgent", "display_name": "PlannerAgent", "role": "千人千面学习路径 DAG 规划", "layer": "path"},
    {
        "id": "LearningPathAgent",
        "display_name": "LearningPathAgent",
        "role": "学习路径规划（PlannerAgent 实现）",
        "layer": "path",
    },
    {"id": "TutorAgent", "display_name": "TutorAgent", "role": "智能辅导答疑", "layer": "tutor"},
    {"id": "OjAssistantAgent", "display_name": "OjAssistantAgent", "role": "OJ 刷题辅导", "layer": "tutor"},
    {"id": "OjDiagnosisAgent", "display_name": "OjDiagnosisAgent", "role": "OJ AI 深度诊断", "layer": "tutor"},
    {
        "id": "ASTAnalyzerAgent",
        "display_name": "ASTAnalyzerAgent",
        "role": "静态语法诊断 · 死循环/越界熔断",
        "layer": "safety",
    },
    {"id": "ContentVerifierAgent", "display_name": "ContentVerifierAgent", "role": "防幻觉校验", "layer": "safety"},
    {"id": "SafetyAgent", "display_name": "SafetyAgent", "role": "内容安全审查与防幻觉把关", "layer": "safety"},
    {"id": "EvaluatorAgent", "display_name": "EvaluatorAgent", "role": "OJ 学情评估与动态降级", "layer": "eval"},
    {"id": "EvaluationAgent", "display_name": "EvaluationAgent", "role": "学习效果评估", "layer": "eval"},
    {
        "id": "MasteryAgent",
        "display_name": "MasteryAgent",
        "role": "章节/技能掌握度可解释评估",
        "layer": "eval",
    },
    {
        "id": "EventBus",
        "display_name": "EventBus",
        "role": "学习事件编排与多智能体闭环",
        "layer": "eval",
    },
    {"id": "KnowledgeRetriever", "display_name": "KnowledgeRetriever", "role": "知识库检索", "layer": "safety"},
]

RESOURCE_TYPE_TO_AGENT: dict[str, str] = {
    "document": "ConceptAgent",
    "mindmap": "GraphAgent",
    "exercises": "ExerciseAgent",
    "code_case": "ScenarioAgent",
    "trace_animation": "TraceAgent",
    "reading": "ReadingAgent",
    "ppt": "PptAgent",
    "video_script": "VideoScriptAgent",
}


def list_agents() -> list[AgentMeta]:
    return list(AGENT_REGISTRY)


def agent_for_resource(resource_type: str) -> str:
    return RESOURCE_TYPE_TO_AGENT.get(resource_type, "ConceptAgent")
