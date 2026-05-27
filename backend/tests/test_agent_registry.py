"""Agent Registry 初始化与资源类型映射。"""

from __future__ import annotations

from services.agents.registry import (
    AGENT_REGISTRY,
    RESOURCE_TYPE_TO_AGENT,
    agent_for_resource,
    list_agents,
)


def test_registry_non_empty_and_unique_ids() -> None:
    agents = list_agents()
    assert len(agents) >= 10
    ids = [a["id"] for a in agents]
    assert len(ids) == len(set(ids))


def test_registry_layers_cover_core_domains() -> None:
    layers = {a["layer"] for a in AGENT_REGISTRY}
    for expected in ("profiling", "resource", "path", "tutor", "safety", "eval"):
        assert expected in layers


def test_resource_type_maps_to_known_agent() -> None:
    for rtype in ("document", "mindmap", "exercises", "code_case", "trace_animation"):
        agent_id = agent_for_resource(rtype)
        assert agent_id in {a["id"] for a in AGENT_REGISTRY}
        assert RESOURCE_TYPE_TO_AGENT[rtype] == agent_id
