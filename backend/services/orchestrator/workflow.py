"""多智能体协作 DAG：检索 → 角色生成（可重试）→ 校验闭环 → 安全过滤。"""

from __future__ import annotations

import hashlib
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
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

        async def _emit(
            stage: str,
            agent: str,
            status: str,
            detail: str = "",
            *,
            retry_count: int | None = None,
            severity: str = "info",
        ) -> None:
            if emit:
                await emit(
                    {
                        "type": "workflow",
                        "stage": stage,
                        "agent": agent,
                        "status": status,
                        "resource_type": resource_type,
                        "detail": detail,
                        "event_type": stage,
                        "agent_id": agent,
                        "agent_name": agent,
                        "message": detail,
                        "progress": None,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "retry_count": retry_count,
                        "severity": severity,
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
        chapter_id = ""
        try:
            from services.knowledge.course_loader import chapter_id_for_module, load_manifest

            chapter_id = chapter_id_for_module(load_manifest(), module_key) or ""
        except Exception:
            pass
        chunks = retriever.search(
            query,
            module_key=module_key,
            course_id="data_structures_algorithms",
            chapter_id=chapter_id,
            top_k=5,
        )
        from services.knowledge.retriever import primary_course_context

        course_ctx = primary_course_context(chunks)
        ctx.log("KnowledgeRetriever", "retrieve", f"命中 {len(chunks)} 条", resource_type=resource_type)
        await _emit("rag_retrieve", "KnowledgeRetriever", "done", f"命中 {len(chunks)} 条")

        skill_route_score = 0.0
        skill_route_reasons: list[str] = []
        skill_focus = ""
        matched_skill_card = None
        try:
            from services.skills.recommend import build_route_request
            from services.skills.skill_context import format_skill_prompt_block
            from services.skills.skill_router import get_skill_router

            route_req = build_route_request(
                module_key=module_key,
                topic=topic,
                profile_block=profile_block,
                user_query=focus_hint,
            )
            route_req.chapter_id = course_ctx.get("chapter_id") or route_req.chapter_id
            route_result = get_skill_router().route(route_req)
            if route_result.skill_card:
                matched_skill_card = route_result.skill_card
                skill_focus = format_skill_prompt_block(
                    matched_skill_card, resource_type=resource_type
                )
                if route_result.matches:
                    skill_route_score = route_result.matches[0].score
                    skill_route_reasons = list(route_result.matches[0].reasons)
                ctx.log(
                    "SkillRouter",
                    "match",
                    f"{matched_skill_card.id} · {matched_skill_card.name}",
                    resource_type=resource_type,
                )
                await _emit(
                    "skill_route",
                    "SkillRouter",
                    "done",
                    f"命中技能卡 {matched_skill_card.id}",
                )
        except Exception:
            pass

        revised_hint = ""
        title = ""
        content = ""
        gen_meta: dict = {}
        passed = False
        verify_skipped = False
        verifier_structured = None
        retry_count = 0
        course_id = course_ctx.get("course_id") or "data_structures_algorithms"
        chapter_id_final = course_ctx.get("chapter_id") or chapter_id

        for attempt in range(1, MAX_VERIFY_RETRIES + 2):
            collab = ctx.agent_hints_block()
            hint_parts = [p for p in (focus_hint, skill_focus, collab) if p]
            hint = "\n\n".join(hint_parts)
            if revised_hint:
                hint = (hint + f"\n\n校验修订：{revised_hint}").strip()

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
                verify_skipped = True
                gen_meta["verified"] = True
                gen_meta["verify_attempts"] = 0
                gen_meta["knowledge_refs"] = [c["id"] for c in chunks]
                verifier_structured = None
                ctx.log("TraceAgent", "trace_record", gen_meta.get("trace_verdict", "done"), resource_type=resource_type)
                await _emit("content_verify", "ContentVerifierAgent", "skipped", "轨迹资源跳过文本校验")
                break

            await _emit("content_verify", "ContentVerifierAgent", "running")
            passed, content, citation_ids, revised_hint, verifier_structured = await verifier_agent.verify(
                content, chunks, topic=topic
            )
            retry_count = attempt - 1
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
                retry_count=attempt - 1,
                severity="warn",
            )
            if attempt > MAX_VERIFY_RETRIES:
                gen_meta["status"] = "draft"
                gen_meta["draft_reason"] = revised_hint or "未通过知识库校验"
                break
            ctx.log(role_agent_id, "retry", revised_hint, role=role_agent.role, resource_type=resource_type, status="retry")
            await _emit("agent_generate", role_agent_id, "retry", revised_hint, retry_count=attempt - 1, severity="warn")

        if passed:
            gen_meta["status"] = "published"
        else:
            gen_meta["status"] = "draft"

        ctx.update_from_resource(resource_type, content)
        gen_meta["collaboration_log"] = list(ctx.collaboration_log)

        await _emit("safety_filter", "SafetyAgent", "running")
        safety_structured = safety_agent.audit_structured(content, resource_type=resource_type)
        safe_text = safety_structured.text or content
        passed_safety = safety_structured.passed
        safety_logs = safety_structured.logs
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
                severity="error",
            )
            gen_meta["status"] = "draft"
            gen_meta["draft_reason"] = safety_logs[-1].get("detail", "") if safety_logs else "内容未通过安全审查"
            safe_text = (content[:2000] + "\n\n> ⚠️ 内容未通过安全审查，已标记为草稿供人工复核。") if content else ""
        elif passed:
            gen_meta["status"] = "published"
        else:
            gen_meta["status"] = "draft"

        gen_meta["safety_warnings"] = [
            w
            for entry in safety_logs
            if entry.get("status") == "warn"
            for w in [entry.get("detail", "")]
            if w
        ]
        gen_meta["safety_warnings"].extend(safety_structured.hallucination_warnings)

        from services.verification.builder import (
            build_verification_result,
            chunks_to_grounded,
            verification_for_skipped_type,
        )

        if verify_skipped:
            verification = verification_for_skipped_type(
                resource_type,
                course_id=course_id,
                chapter_id=chapter_id_final,
                chunks=chunks,
                trace_verdict=str(gen_meta.get("trace_verdict") or ""),
            )
            verification.safety_status = safety_structured.status  # type: ignore[assignment]
            if not passed_safety:
                verification.final_decision = "blocked"
                verification.risk_label = "安全警告"
        else:
            v_status = verifier_structured.status if verifier_structured else "warning"
            if passed and v_status != "passed":
                v_status = "passed"
            verification = build_verification_result(
                resource_type=resource_type,
                course_id=course_id,
                chapter_id=chapter_id_final,
                verifier_status=v_status,  # type: ignore[arg-type]
                safety_status=safety_structured.status,  # type: ignore[arg-type]
                grounded_chunks=chunks_to_grounded(chunks),
                hallucination_risks=list(
                    (verifier_structured.hallucination_risks if verifier_structured else [])
                    + safety_structured.hallucination_warnings
                ),
                unsupported_claims=list(verifier_structured.unsupported_claims if verifier_structured else []),
                sensitive_risks=list(safety_structured.sensitive_risks),
                prompt_injection_risks=list(safety_structured.prompt_injection_risks),
                retry_count=retry_count,
                final_decision=gen_meta.get("status", "draft") if passed_safety else "blocked",
            )
            if gen_meta.get("status") == "published" and passed_safety:
                verification.final_decision = "publish"

        gen_meta["verification"] = verification.to_meta_dict()
        gen_meta["safety_panel"] = {
            "shield": "green"
            if verification.final_decision == "publish"
            else ("red" if verification.final_decision == "blocked" else "yellow"),
            "knowledge_source": _source_label(gen_meta.get("knowledge_refs") or [], module_key),
            "complexity_verified": verification.verifier_status == "passed",
            "sensitive_filter_passed": verification.safety_status != "failed",
            "agents": ["ContentVerifierAgent", "SafetyAgent"],
            "verification": verification.to_meta_dict(),
            "oj_sandbox": {
                "time_limit": "Python trace 8s / OJ 题目级限时",
                "memory_limit": "题目级内存限制",
                "syscall_policy": "禁用 system/fork/exec 与危险头文件",
                "isolation": "子进程执行；生产部署建议 Docker/容器隔离",
            },
        }
        gen_meta["agent_logs"] = list(ctx.agent_logs)
        gen_meta["course_id"] = course_id
        gen_meta["chapter_id"] = chapter_id_final
        gen_meta["knowledge_chunk_ids"] = [c["id"] for c in chunks]
        gen_meta["_evidence_version"] = 1
        gen_meta["_content_hash"] = hashlib.sha256(safe_text.encode()).hexdigest()[:16] if safe_text else ""

        from services.evidence.builder import build_evidence_from_meta
        gen_meta["evidence"] = build_evidence_from_meta(
            resource_id=0,
            agent_name=role_agent_id,
            meta={**gen_meta, "_content_for_hash": safe_text},
            created_at="",
            profile_summary="",
        ).model_dump()
        if matched_skill_card:
            from services.skills.skill_context import skill_card_meta_payload

            gen_meta["skill_card"] = skill_card_meta_payload(
                matched_skill_card,
                score=skill_route_score,
                reasons=skill_route_reasons,
            )
        await _emit(
            "safety_filter",
            "SafetyAgent",
            "done" if passed_safety else "warn",
            safety_logs[-1].get("detail", "") if safety_logs else "审查完成",
            severity="info" if passed_safety else "warn",
        )
        await _emit(
            "persist",
            "Orchestrator",
            "done" if gen_meta.get("status") == "published" else "warn",
            gen_meta.get("status", ""),
            severity="info" if gen_meta.get("status") == "published" else "warn",
        )

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
