"""多智能体角色：仅通过 Orchestrator 调度。"""

from services.agents.learning_path import LearningPathAgent
from services.agents.persona import PersonaAgent
from services.agents.tutor import TutorAgent
from services.agents.oj_assistant import OjAssistantAgent
from services.agents.resources import ResourceAgents
from services.agents.resource_roles import (
    ConceptAgent,
    GraphAgent,
    ScenarioAgent,
    TraceAgent,
)

__all__ = [
    "PersonaAgent",
    "TutorAgent",
    "OjAssistantAgent",
    "ResourceAgents",
    "LearningPathAgent",
    "ConceptAgent",
    "GraphAgent",
    "ScenarioAgent",
    "TraceAgent",
]
