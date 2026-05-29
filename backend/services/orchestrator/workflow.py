"""多智能体协作 DAG：检索 → 角色生成（可重试）→ 校验闭环 → 安全过滤。"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from schemas.resources import ResourceType
from services.agents.registry import agent_for_resource
from services.agents.resource_roles import get_role_agent
from services.agents.resources import ResourceAgents
from services.agents.verifier import verifier_agent
from services.knowledge.retriever import retriever
from services.orchestrator.pipeline_context import PipelineContext
from services.safety.content_filter import safety_agent

EmitFn = Callable[[dict[str, Any]], Awaitable[None]]

RESOURCE_PIPELINE_STAGES = [
    ("rag_retrieve", "KnowledgeRetriever", "BM25 检索课程知识库"),
    ("agent_generate", "role_agent", "五类角色 Agent 生成（接收画像与协作上下文）"),
    ("content_verify", "ContentVerifierAgent", "对照知识库校验（失败可回流重试）"),
    ("safety_filter", "SafetyAgent", "内容安全审查与防幻觉把关"),
    ("persist", "Orchestrator", "校验通过落库 / 未通过标草稿"),
]

MAX_VERIFY_RETRIES = 2

# trace_animation 由 TraceAgent 内部调用 trace_runner，跳过文本校验回流
_SKIP_VERIFY_TYPES = frozenset({"trace_animation"})


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
        role_agent_id = agent_for_resource(resource_type)
        role_agent = get_role_agent(resource_type)
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

        ctx.log(
            role_agent_id,
            "dispatch",
            f"开始生成 {resource_type}",
            role=role_agent.role,
            resource_type=resource_type,
            status="running",
        )
        await _emit("rag_retrieve", "KnowledgeRetriever", "running", "BM25 匹配知识库")
        query = f"{topic} {focus_hint} {module_key}".strip()
        chunks = retriever.search(query, module_key=module_key, top_k=5)
        ctx.log("KnowledgeRetriever", "retrieve", f"命中 {len(chunks)} 条", resource_type=resource_type)
        await _emit("rag_retrieve", "KnowledgeRetriever", "done", f"命中 {len(chunks)} 条")

        revised_hint = ""
        title = ""
        content = ""
        gen_meta: dict = {}
        passed = False

        for attempt in range(1, MAX_VERIFY_RETRIES + 2):
            collab = ctx.agent_hints_block()
            hint = focus_hint
            if revised_hint:
                hint = f"{focus_hint}；校验修订：{revised_hint}".strip("；")
            if collab:
                hint = (hint + "\n" + collab).strip() if hint else collab

            await _emit(
                "agent_generate",
                role_agent_id,
                "running",
                f"第 {attempt} 次生成" if attempt > 1 else role_agent.role,
            )
            title, content, gen_meta = await ResourceAgents.generate_with_context(
                resource_type,
                topic=topic,
                profile_block=profile_block,
                module_key=module_key,
                focus_hint=hint,
                chunks=chunks,
            )
            ctx.log(
                role_agent_id,
                "generate",
                f"产出 {gen_meta.get('format', 'content')}",
                role=role_agent.role,
                resource_type=resource_type,
            )
            await _emit("agent_generate", role_agent_id, "done")

            if resource_type in _SKIP_VERIFY_TYPES:
                passed = True
                gen_meta["verified"] = True
                gen_meta["verify_attempts"] = 0
                gen_meta["knowledge_refs"] = []
                ctx.log("TraceAgent", "trace_record", gen_meta.get("trace_verdict", "done"), resource_type=resource_type)
                await _emit("content_verify", "ContentVerifierAgent", "skipped", "轨迹资源跳过文本校验")
                break

            await _emit("content_verify", "ContentVerifierAgent", "running")
            passed, content, citation_ids, revised_hint = await verifier_agent.verify(
                content, chunks, topic=topic
            )
            gen_meta["knowledge_refs"] = citation_ids
            gen_meta["verified"] = passed
            gen_meta["verify_attempts"] = attempt

            if passed:
                ctx.log("ContentVerifierAgent", "verify_pass", "校验通过", resource_type=resource_type)
                await _emit("content_verify", "ContentVerifierAgent", "done", "校验通过")
                break
            ctx.log("ContentVerifierAgent", "verify_fail", revised_hint or "未通过", resource_type=resource_type, status="warn")
            await _emit(
                "content_verify",
                "ContentVerifierAgent",
                "warn",
                revised_hint or "校验未通过",
            )
            if attempt > MAX_VERIFY_RETRIES:
                gen_meta["status"] = "draft"
                gen_meta["draft_reason"] = revised_hint or "未通过知识库校验"
                break
            ctx.log(role_agent_id, "retry", revised_hint, role=role_agent.role, resource_type=resource_type, status="retry")
            await _emit("agent_generate", role_agent_id, "retry", revised_hint)

        if passed:
            gen_meta["status"] = "published"
        else:
            gen_meta["status"] = "draft"

        ctx.update_from_resource(resource_type, content)
        gen_meta["collaboration_log"] = list(ctx.collaboration_log)

        await _emit("safety_filter", "SafetyAgent", "running")
        safe_text, safety_logs, passed_safety = safety_agent.audit(
            content, resource_type=resource_type
        )
        for entry in safety_logs:
            ctx.log(
                entry["agent"],
                entry.get("action", "audit"),
                entry.get("detail", ""),
                resource_type=resource_type,
                status=entry.get("status", "done"),
            )
            gen_meta.setdefault("agent_logs", []).append(entry)
        if not passed_safety:
            await _emit(
                "safety_filter",
                "SafetyAgent",
                "error",
                safety_logs[-1].get("detail", "") if safety_logs else "审查未通过",
            )
            raise ValueError(
                safety_logs[-1].get("detail", "") if safety_logs else "内容未通过安全审查"
            )
        gen_meta["safety_warnings"] = [
            w
            for entry in safety_logs
            if entry.get("status") == "warn"
            for w in [entry.get("detail", "")]
            if w
        ]
        gen_meta["safety_panel"] = {
            "shield": "green" if passed and passed_safety else "yellow",
            "knowledge_source": _source_label(gen_meta.get("knowledge_refs") or [], module_key),
            "complexity_verified": bool(passed),
            "sensitive_filter_passed": bool(passed_safety),
            "agents": ["ContentVerifierAgent", "SafetyAgent"],
            "oj_sandbox": {
                "time_limit": "Python trace 8s / OJ 题目级限时",
                "memory_limit": "题目级内存限制",
                "syscall_policy": "禁用 system/fork/exec 与危险头文件",
                "isolation": "子进程执行；生产部署建议 Docker/容器隔离",
            },
        }
        gen_meta["agent_logs"] = list(ctx.agent_logs)
        await _emit(
            "safety_filter",
            "SafetyAgent",
            "done",
            safety_logs[-1].get("detail", "") if safety_logs else "审查通过",
        )
        await _emit("persist", "Orchestrator", "done" if passed else "warn", gen_meta.get("status", ""))

        return title, safe_text, gen_meta

    @staticmethod
    def describe_pipeline() -> list[dict[str, str]]:
        return [
            {"stage": s[0], "agent": s[1], "label": s[2]}
            for s in RESOURCE_PIPELINE_STAGES
        ]


resource_workflow = ResourceGenerationWorkflow()


def _source_label(refs: list[str], module_key: str) -> str:
    if refs:
        return "、".join(str(r) for r in refs[:3])
    if module_key:
        return f"knowledge_base/{module_key}"
    return "课程知识库检索片段"
