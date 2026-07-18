"""多智能体协作 DAG：检索 → 角色生成（可重试）→ 校验闭环 → 安全过滤。"""

from __future__ import annotations

import hashlib
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from schemas.resources import ResourceType
from services.agents.registry import agent_for_resource
from services.agents.resource_roles import get_role_agent
from services.agents.resources import ResourceAgents
from services.agents.verifier import verifier_agent
from services.knowledge.retriever import build_source_records, retriever
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
        stage_started_at: dict[tuple[str, str], float] = {}

        async def _emit(
            stage: str,
            agent: str,
            status: str,
            detail: str = "",
            *,
            retry_count: int | None = None,
            severity: str = "info",
            validation_result: dict | None = None,
            input_summary: str = "",
            output_summary: str = "",
            failure_reason: str = "",
        ) -> None:
            if emit:
                key = (stage, agent)
                duration_ms = None
                if status == "running":
                    stage_started_at[key] = perf_counter()
                elif key in stage_started_at:
                    duration_ms = max(
                        0, int((perf_counter() - stage_started_at.pop(key)) * 1000)
                    )
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
                        "duration_ms": duration_ms,
                        "validation_result": validation_result,
                        "retry_count": retry_count,
                        "input_summary": input_summary,
                        "output_summary": output_summary,
                        "failure_reason": failure_reason,
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
        await _emit(
            "rag_retrieve",
            "KnowledgeRetriever",
            "running",
            "BM25 匹配知识库",
            input_summary=f"{topic} | {focus_hint or module_key}",
        )
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
        sources = build_source_records(chunks)
        ctx.log("KnowledgeRetriever", "retrieve", f"命中 {len(chunks)} 条", resource_type=resource_type)
        await _emit(
            "rag_retrieve",
            "KnowledgeRetriever",
            "success",
            f"命中 {len(chunks)} 条",
            output_summary=f"Top-{len(chunks)} knowledge chunks",
        )

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
                    "success",
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

            # 重试前向前端发送 regenerate_clear 信号，让前端清空上一轮已显示的流式内容
            if attempt > 1 and emit:
                await emit(
                    {
                        "type": "regenerate_clear",
                        "resource_type": resource_type,
                        "agent_id": role_agent_id,
                        "agent_name": role_agent_id,
                        "attempt": attempt,
                        "reason": revised_hint or "上一轮输出未通过校验，重新生成",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )

            await _emit(
                "agent_generate",
                role_agent_id,
                "running",
                f"第 {attempt} 次生成" if attempt > 1 else role_agent.role,
                retry_count=attempt - 1,
                input_summary=f"{topic} | profile + knowledge chunks + collaboration context",
            )

            async def _stream_delta(delta: str) -> None:
                if emit and delta:
                    await emit(
                        {
                            "type": "content_delta",
                            "resource_type": resource_type,
                            "agent_id": role_agent_id,
                            "agent_name": role_agent_id,
                            "attempt": attempt,
                            "delta": delta,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )

            title, content, gen_meta = await ResourceAgents.generate_with_context(
                resource_type,
                topic=topic,
                profile_block=profile_block,
                module_key=module_key,
                focus_hint=hint,
                chunks=chunks,
                on_delta=_stream_delta,
            )
            ctx.log(
                role_agent_id,
                "generate",
                f"产出 {gen_meta.get('format', 'content')}",
                role=role_agent.role,
                resource_type=resource_type,
            )
            await _emit(
                "agent_generate",
                role_agent_id,
                "success",
                output_summary=f"{title} | {gen_meta.get('format', 'content')}",
                retry_count=attempt - 1,
            )

            if resource_type in _SKIP_VERIFY_TYPES:
                verify_skipped = True
                trace_verdict = str(gen_meta.get("trace_verdict") or "").upper()
                trace_steps = int(gen_meta.get("trace_steps") or 0)
                trace_quality_passed = bool(gen_meta.get("trace_quality_passed"))
                trace_quality_reasons = list(gen_meta.get("trace_quality_reasons") or [])
                trace_ok = (
                    trace_verdict in {"AC", "OK"}
                    and trace_steps >= 4
                    and trace_quality_passed
                )
                passed = trace_ok
                gen_meta["verified"] = trace_ok
                gen_meta["verify_attempts"] = 0
                gen_meta["knowledge_refs"] = [c["id"] for c in chunks]
                gen_meta["content_verification"] = {
                    "passed": trace_ok,
                    "warnings": [] if trace_ok else [
                        f"执行轨迹未通过：verdict={trace_verdict or 'missing'}, steps={trace_steps}"
                        + (f"，{'；'.join(trace_quality_reasons)}" if trace_quality_reasons else "")
                    ],
                    "grounded_terms": [],
                    "unsupported_claims": [] if trace_ok else ["代码未产生可用且成功的执行轨迹"],
                }
                verifier_structured = None
                ctx.log("TraceAgent", "trace_record", trace_verdict or "missing", resource_type=resource_type, status="done" if trace_ok else "warn")
                await _emit(
                    "content_verify",
                    "ContentVerifierAgent",
                    "skipped" if trace_ok else ("retry" if attempt <= MAX_VERIFY_RETRIES else "failed"),
                    "执行轨迹校验通过" if trace_ok else (
                        f"执行轨迹无效：verdict={trace_verdict or 'missing'}, steps={trace_steps}"
                        + (f"，{'；'.join(trace_quality_reasons)}" if trace_quality_reasons else "")
                    ),
                    retry_count=attempt - 1,
                    severity="info" if trace_ok else "warn",
                    validation_result={"status": "passed" if trace_ok else "failed", "trace_verdict": trace_verdict, "trace_steps": trace_steps},
                )
                if trace_ok:
                    break
                revised_hint = (
                    "生成可运行且紧扣课程主题的 Python3 完整程序，确保 stdin 与代码匹配；"
                    "轨迹至少包含 4 个有效步骤、2 个源码位置、2 个可观察且发生变化的变量"
                )
                retry_count = attempt - 1
                if attempt <= MAX_VERIFY_RETRIES:
                    ctx.log(role_agent_id, "retry", revised_hint, role=role_agent.role, resource_type=resource_type, status="retry")
                    continue
                gen_meta["status"] = "draft"
                gen_meta["draft_reason"] = revised_hint
                break

            await _emit(
                "content_verify",
                "ContentVerifierAgent",
                "running",
                input_summary=f"{title} | {len(chunks)} evidence chunks",
            )
            passed, content, citation_ids, revised_hint, verifier_structured = await verifier_agent.verify(
                content, chunks, topic=topic, resource_type=resource_type
            )
            retry_count = attempt - 1
            gen_meta["knowledge_refs"] = citation_ids
            gen_meta["verified"] = passed
            gen_meta["verify_attempts"] = attempt
            gen_meta["content_verification"] = verifier_structured.to_display_dict()

            if passed:
                ctx.log("ContentVerifierAgent", "verify_pass", "校验通过", resource_type=resource_type)
                await _emit(
                    "content_verify",
                    "ContentVerifierAgent",
                    "success",
                    "校验通过",
                    validation_result={
                        "status": "passed",
                        "evidence_count": len(citation_ids),
                    },
                    output_summary=f"passed | {len(citation_ids)} citations",
                    retry_count=retry_count,
                )
                break
            ctx.log("ContentVerifierAgent", "verify_fail", revised_hint or "未通过", resource_type=resource_type, status="warn")
            await _emit(
                "content_verify",
                "ContentVerifierAgent",
                "retry" if attempt <= MAX_VERIFY_RETRIES else "failed",
                revised_hint or "校验未通过",
                retry_count=attempt - 1,
                severity="warn",
                validation_result={
                    "status": "failed",
                    "evidence_count": len(citation_ids),
                },
                failure_reason=revised_hint or "content verification failed",
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

        if passed:
            ctx.update_from_resource(resource_type, content)
        gen_meta["collaboration_log"] = list(ctx.collaboration_log)

        await _emit(
            "safety_filter",
            "SafetyAgent",
            "running",
            input_summary=f"{title} | verified={passed}",
        )
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
                "failed",
                safety_logs[-1].get("detail", "") if safety_logs else "审查未通过",
                severity="error",
                validation_result={"status": safety_structured.status},
                failure_reason=safety_logs[-1].get("detail", "") if safety_logs else "safety audit failed",
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
        if "content_verification" not in gen_meta:
            gen_meta["content_verification"] = (
                verifier_structured.to_display_dict()
                if verifier_structured
                else {
                    "passed": bool(passed),
                    "warnings": [],
                    "grounded_terms": [],
                    "unsupported_claims": [],
                }
            )
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
        gen_meta["sources"] = sources
        gen_meta["grounding_basis"] = {
            "course_id": course_id,
            "module_id": module_key,
            "chapter_id": chapter_id_final,
            "retrieval": "BM25 + synonym expansion",
        }
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
            "success" if passed_safety else "failed",
            safety_logs[-1].get("detail", "") if safety_logs else "审查完成",
            severity="info" if passed_safety else "warn",
            validation_result={
                "status": safety_structured.status,
                "sensitive_risks": len(safety_structured.sensitive_risks),
                "prompt_injection_risks": len(safety_structured.prompt_injection_risks),
            },
            output_summary="safe content" if passed_safety else "blocked as draft",
        )
        await _emit(
            "persist",
            "Orchestrator",
            "success" if gen_meta.get("status") == "published" else "failed",
            gen_meta.get("status", ""),
            severity="info" if gen_meta.get("status") == "published" else "warn",
            validation_result={"final_decision": verification.final_decision},
            output_summary=f"resource status={gen_meta.get('status', '')}",
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
