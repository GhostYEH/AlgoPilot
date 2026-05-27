"""Orchestrator 资源生成 DAG 编排元数据。"""

from __future__ import annotations

from services.orchestrator.core import Orchestrator
from services.orchestrator.workflow import RESOURCE_PIPELINE_STAGES, resource_workflow


def test_resource_pipeline_stage_order() -> None:
    stages = resource_workflow.describe_pipeline()
    assert len(stages) == len(RESOURCE_PIPELINE_STAGES)
    assert stages[0]["stage"] == "rag_retrieve"
    assert stages[-1]["stage"] == "persist"
    agents = [s["agent"] for s in stages]
    assert "KnowledgeRetriever" in agents
    assert "SafetyAgent" in agents


def test_resource_dag_mermaid_contains_key_agents() -> None:
    mermaid = Orchestrator.describe_resource_dag_mermaid()
    for token in ("ProfilingAgent", "ConceptAgent", "SafetyAgent", "ContentVerifier"):
        assert token in mermaid


def test_list_agents_via_orchestrator() -> None:
    orch = Orchestrator()
    agents = orch.list_agents()
    assert any(a["id"] == "ProfilingAgent" for a in agents)
