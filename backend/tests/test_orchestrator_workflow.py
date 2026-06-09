"""Orchestrator 资源生成 DAG 编排元数据。"""

from __future__ import annotations

from services.orchestrator.core import Orchestrator
from services.orchestrator.core import _observable_agent_event
from services.orchestrator.workflow import RESOURCE_PIPELINE_STAGES, resource_workflow
from schemas.resources import GeneratedResourceItem


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
    assert any(a["id"] == "PptAgent" for a in agents)
    assert any(a["id"] == "VideoScriptAgent" for a in agents)


def test_observable_agent_event_contract() -> None:
    event = _observable_agent_event(
        agent="EvaluationAgent",
        stage="batch_evaluation",
        status="success",
        message="done",
        validation_result={"status": "passed"},
    )
    required = {
        "agent_id",
        "agent_name",
        "stage",
        "status",
        "message",
        "timestamp",
        "duration_ms",
        "validation_result",
    }
    assert required.issubset(event)
    assert event["agent_id"] == "EvaluationAgent"
    assert event["status"] == "success"


def test_generated_resource_schema_accepts_legacy_rows_without_sources() -> None:
    item = GeneratedResourceItem(
        id=1,
        resource_type="document",
        agent_name="ConceptAgent",
        title="旧资源",
        content="旧数据",
        meta={"knowledge_refs": ["legacy-chunk"]},
        created_at="",
    )
    assert item.sources == []
