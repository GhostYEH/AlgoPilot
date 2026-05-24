"""多智能体协作 DAG：检索 → 生成（可重试）→ 校验闭环 → 安全过滤。"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from schemas.resources import ResourceType
from services.agents.registry import agent_for_resource
from services.agents.resources import ResourceAgents
from services.agents.verifier import verifier_agent
from services.knowledge.retriever import format_context_block, retriever
from services.orchestrator.pipeline_context import PipelineContext
from services.safety.content_filter import content_filter

EmitFn = Callable[[dict[str, Any]], Awaitable[None]]

RESOURCE_PIPELINE_STAGES = [
    ("rag_retrieve", "KnowledgeRetriever", "BM25 检索课程知识库"),
    ("agent_generate", "role_agent", "角色智能体生成（可接收协作上下文）"),
    ("content_verify", "ContentVerifierAgent", "对照知识库校验（失败可回流重试）"),
    ("safety_filter", "ContentSafety", "敏感词与风险过滤"),
    ("persist", "Orchestrator", "校验通过落库 / 未通过标草稿"),
]

MAX_VERIFY_RETRIES = 2


class ResourceGenerationWorkflow:
    """单资源 DAG：检索 → 生成 ⇄ 校验闭环 → 安全过滤。"""

    async def run(
        self,
        resource_type: ResourceType,
        *,
        topic: str,
        profile_block: str,
        module_key: str = "",
        focus_hint: str = "",
        emit: EmitFn | None = None,
        pipeline_ctx: PipelineContext | None = None,
    ) -> tuple[str, str, dict]:
        role_agent = agent_for_resource(resource_type)
        ctx = pipeline_ctx or PipelineContext()

        async def _emit(stage: str, agent: str, status: str, detail: str = "") -> None:
            if emit:
                await emit(
                    {
                        "type": "workflow",
                        "stage": stage,
                        "agent": agent,
                        "status": status,
                        "resource_type": resource_type,
                        "detail": detail,
                    }
                )

        await _emit("rag_retrieve", "KnowledgeRetriever", "running", "BM25 匹配知识库")
        query = f"{topic} {focus_hint} {module_key}".strip()
        chunks = retriever.search(query, module_key=module_key, top_k=5)
        await _emit("rag_retrieve", "KnowledgeRetriever", "done", f"命中 {len(chunks)} 条")

        collab = ctx.agent_hints_block()
        revised_hint = ""
        title = ""
        content = ""
        gen_meta: dict = {}
        passed = False

        for attempt in range(1, MAX_VERIFY_RETRIES + 2):
            hint = focus_hint
            if revised_hint:
                hint = f"{focus_hint}；校验修订：{revised_hint}".strip("；")
            if collab:
                hint = (hint + "\n" + collab).strip() if hint else collab

            await _emit(
                "agent_generate",
                role_agent,
                "running",
                f"第 {attempt} 次生成" if attempt > 1 else "",
            )
            title, content, gen_meta = await ResourceAgents.generate_with_context(
                resource_type,
                topic=topic,
                profile_block=profile_block,
                module_key=module_key,
                focus_hint=hint,
                chunks=chunks,
            )
            await _emit("agent_generate", role_agent, "done")

            await _emit("content_verify", "ContentVerifierAgent", "running")
            passed, content, citation_ids, revised_hint = await verifier_agent.verify(
                content, chunks, topic=topic
            )
            gen_meta["knowledge_refs"] = citation_ids
            gen_meta["verified"] = passed
            gen_meta["verify_attempts"] = attempt

            if passed:
                await _emit("content_verify", "ContentVerifierAgent", "done", "校验通过")
                break
            await _emit(
                "content_verify",
                "ContentVerifierAgent",
                "warn",
                revised_hint or "校验未通过",
            )
            if attempt > MAX_VERIFY_RETRIES:
                gen_meta["status"] = "draft"
                gen_meta["draft_reason"] = revised_hint or "未通过知识库校验"
                ctx.log("ContentVerifierAgent", "draft", gen_meta["draft_reason"])
                break
            ctx.log(role_agent, "retry", revised_hint)
            await _emit("agent_generate", role_agent, "retry", revised_hint)

        if passed:
            gen_meta["status"] = "published"
        else:
            gen_meta["status"] = "draft"

        ctx.update_from_resource(resource_type, content)
        gen_meta["collaboration_log"] = list(ctx.collaboration_log)

        await _emit("safety_filter", "ContentSafety", "running")
        safety = content_filter.check(content)
        if safety.blocked:
            await _emit("safety_filter", "ContentSafety", "error", "；".join(safety.reasons))
            raise ValueError("；".join(safety.reasons) or "内容未通过安全过滤")
        gen_meta["safety_warnings"] = content_filter.warn_hallucination_risk(safety.text)
        await _emit("safety_filter", "ContentSafety", "done")
        await _emit("persist", "Orchestrator", "done" if passed else "warn", gen_meta.get("status", ""))

        return title, safety.text, gen_meta

    @staticmethod
    def describe_pipeline() -> list[dict[str, str]]:
        return [
            {"stage": s[0], "agent": s[1], "label": s[2]}
            for s in RESOURCE_PIPELINE_STAGES
        ]


resource_workflow = ResourceGenerationWorkflow()
