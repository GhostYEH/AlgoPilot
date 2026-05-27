"""资源生成编排门面：路由至五类角色 Agent。

ConceptAgent / ScenarioAgent 的 Prompt 与双域 JSON 规范见 resource_roles.py
（domain_narrative 业务域 + structure_logic 结构域，understand-anything 式分离）。
"""

from __future__ import annotations

from schemas.resources import ResourceType
from services.agents.registry import agent_for_resource
from services.agents.resource_roles import get_role_agent
from services.knowledge.retriever import KnowledgeChunk, retriever


class ResourceAgents:
    @staticmethod
    def agent_name(resource_type: ResourceType) -> str:
        return agent_for_resource(resource_type)

    @staticmethod
    async def generate_with_context(
        resource_type: ResourceType,
        *,
        topic: str,
        profile_block: str,
        module_key: str = "",
        focus_hint: str = "",
        chunks: list[KnowledgeChunk],
    ) -> tuple[str, str, dict]:
        agent = get_role_agent(resource_type)
        title, content, meta = await agent.generate(
            topic=topic,
            profile_block=profile_block,
            module_key=module_key,
            focus_hint=focus_hint,
            chunks=chunks,
        )
        meta["agent_id"] = agent.agent_id
        meta["agent_role"] = agent.role
        return title, content, meta

    @staticmethod
    async def generate(
        resource_type: ResourceType,
        *,
        topic: str,
        profile_block: str,
        module_key: str = "",
        focus_hint: str = "",
        chunks: list[KnowledgeChunk] | None = None,
    ) -> tuple[str, str, dict]:
        if chunks is None:
            query = f"{topic} {focus_hint} {module_key}".strip()
            chunks = retriever.search(query, module_key=module_key, top_k=5)
        return await ResourceAgents.generate_with_context(
            resource_type,
            topic=topic,
            profile_block=profile_block,
            module_key=module_key,
            focus_hint=focus_hint,
            chunks=chunks,
        )
