"""模板降级资源工作流：检索 → TemplateFallbackAgent → 规则校验 → SafetyAgent。"""

from __future__ import annotations

import hashlib
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from schemas.resources import ResourceType
from services.agents.template_fallback import GENERATED_BY, generate_fallback_resource
from services.agents.verifier import _rule_check_structured
from services.knowledge.retriever import build_source_records, retriever
from services.orchestrator.pipeline_context import PipelineContext
from services.safety.content_filter import SafetyStructuredResult, safety_agent
from services.verification.builder import build_verification_result, chunks_to_grounded, verification_for_skipped_type

EmitFn = Callable[[dict[str, Any]], Awaitable[None]]

_SKIP_VERIFY_TYPES = frozenset({"trace_animation"})


class FallbackResourceWorkflow:
    async def run(
        self,
        resource_type: ResourceType,
        *,
        topic: str,
        profile_block: str,
        module_key: str = "",
        focus_hint: str = "",
        fallback_reason: str,
        emit: EmitFn | None = None,
        pipeline_ctx: PipelineContext | None = None,
    ) -> tuple[str, str, dict]:
        ctx = pipeline_ctx or PipelineContext()
        stage_started_at: dict[tuple[str, str], float] = {}

        async def _emit(
            stage: str,
            agent: str,
            status: str,
            detail: str = "",
            *,
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
                        "agent_id": agent,
                        "agent_name": agent,
                        "status": status,
                        "resource_type": resource_type,
                        "detail": detail,
                        "message": detail,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "duration_ms": duration_ms,
                        "validation_result": validation_result,
                        "retry_count": 0,
                        "input_summary": input_summary,
                        "output_summary": output_summary,
                        "failure_reason": failure_reason,
                    }
                )

        ctx.log(
            GENERATED_BY,
            "dispatch",
            f"模板降级生成 {resource_type}",
            role="课程知识库模板",
            resource_type=resource_type,
            status="running",
        )
        await _emit(
            "rag_retrieve",
            "KnowledgeRetriever",
            "running",
            "BM25 匹配课程知识库",
            input_summary=f"{topic} | {focus_hint or module_key}",
        )

        chapter_id = ""
        try:
            from services.knowledge.course_loader import chapter_id_for_module, load_manifest

            chapter_id = chapter_id_for_module(load_manifest(), module_key) or ""
        except Exception:
            pass

        query = f"{topic} {focus_hint} {module_key}".strip()
        chunks = retriever.search(
            query,
            module_key=module_key,
            course_id="data_structures_algorithms",
            chapter_id=chapter_id,
            top_k=5,
        )
        from services.knowledge.retriever import primary_course_context

        course_ctx = primary_course_context(chunks)
        course_id = course_ctx.get("course_id") or "data_structures_algorithms"
        chapter_id_final = course_ctx.get("chapter_id") or chapter_id
        sources = build_source_records(chunks)

        ctx.log("KnowledgeRetriever", "retrieve", f"命中 {len(chunks)} 条", resource_type=resource_type)
        await _emit(
            "rag_retrieve",
            "KnowledgeRetriever",
            "success",
            f"命中 {len(chunks)} 条",
            output_summary=f"Top-{len(chunks)} knowledge chunks",
        )

        await _emit(
            "agent_generate",
            GENERATED_BY,
            "running",
            fallback_reason,
            input_summary=f"{topic} | course template + knowledge chunks",
        )
        title, content, gen_meta = generate_fallback_resource(
            resource_type,
            topic=topic,
            profile_block=profile_block,
            module_key=module_key,
            focus_hint=focus_hint,
            chunks=chunks,
            fallback_reason=fallback_reason,
        )
        ctx.log(GENERATED_BY, "generate", "模板拼装完成", resource_type=resource_type)
        await _emit(
            "agent_generate",
            GENERATED_BY,
            "success",
            "模板资源已生成",
            output_summary=f"{title} | template fallback",
        )

        verify_skipped = resource_type in _SKIP_VERIFY_TYPES
        verifier_structured = None
        passed_safety = True
        safety_structured = None
        if verify_skipped:
            await _emit(
                "content_verify",
                "ContentVerifierAgent",
                "skipped",
                "轨迹占位资源跳过 LLM 文本校验",
                validation_result={"status": "skipped", "reason": "trace resource"},
            )
            gen_meta["verified"] = True
            gen_meta["verify_attempts"] = 0
            gen_meta["content_verification"] = {
                "passed": True,
                "warnings": ["该资源由专用执行管线校验，跳过文本事实对照"],
                "grounded_terms": [],
                "unsupported_claims": [],
            }
        else:
            await _emit("content_verify", "ContentVerifierAgent", "running", "规则快检（无 LLM）")
            verifier_structured, rule_failed = _rule_check_structured(content, chunks, topic=topic)
            citation_ids = verifier_structured.grounded_chunk_ids
            gen_meta["knowledge_refs"] = citation_ids
            gen_meta["verified"] = verifier_structured.passed and not rule_failed
            gen_meta["verify_attempts"] = 1
            gen_meta["content_verification"] = verifier_structured.to_display_dict()
            if rule_failed:
                await _emit(
                    "content_verify",
                    "ContentVerifierAgent",
                    "failed",
                    verifier_structured.revised_hint or "规则快检提示",
                    validation_result={"status": "failed"},
                    failure_reason=verifier_structured.revised_hint or "rule verification failed",
                )
                gen_meta["status"] = "draft"
            else:
                await _emit(
                    "content_verify",
                    "ContentVerifierAgent",
                    "success",
                    "规则快检通过",
                    validation_result={
                        "status": "passed",
                        "evidence_count": len(citation_ids),
                    },
                )

        await _emit("safety_filter", "SafetyAgent", "running")
        try:
            safety_structured = safety_agent.audit_structured(content, resource_type=resource_type)
            passed_safety = safety_structured.passed
            safe_text = safety_structured.text or content
            for entry in safety_structured.logs:
                ctx.log(
                    entry["agent"],
                    entry.get("action", "audit"),
                    entry.get("detail", ""),
                    resource_type=resource_type,
                    status=entry.get("status", "done"),
                )
                gen_meta.setdefault("agent_logs", []).append(entry)
            await _emit(
                "safety_filter",
                "SafetyAgent",
                "success" if passed_safety else "failed",
                "安全审查完成" if passed_safety else "安全审查告警",
                validation_result={"status": safety_structured.status},
            )
        except Exception as exc:
            # 安全审查异常时采用 fail-closed 策略：标记为草稿且不向前端下发原文，
            # 与主工作流 workflow.py 的安全语义保持一致。
            passed_safety = False
            safe_text = ""
            detail = f"SafetyAgent 异常，已降级为草稿：{exc}"
            safety_structured = SafetyStructuredResult(
                status="failed",
                passed=False,
                text="",
                logs=[
                    {
                        "agent": "SafetyAgent",
                        "action": "skipped",
                        "detail": detail,
                        "status": "skipped",
                        "resource_type": resource_type,
                    }
                ],
            )
            ctx.log("SafetyAgent", "skipped", detail, resource_type=resource_type, status="skipped")
            gen_meta.setdefault("agent_logs", []).append(
                {
                    "agent": "SafetyAgent",
                    "action": "skipped",
                    "detail": detail,
                    "status": "skipped",
                    "resource_type": resource_type,
                }
            )
            await _emit("safety_filter", "SafetyAgent", "skipped", detail)

        if verify_skipped:
            verification = verification_for_skipped_type(
                resource_type,
                course_id=course_id,
                chapter_id=chapter_id_final,
                chunks=chunks,
                trace_verdict=str(gen_meta.get("trace_verdict") or "SKIPPED"),
            )
            if safety_structured is not None:
                verification.safety_status = safety_structured.status  # type: ignore[assignment]
        else:
            v_status = verifier_structured.status if verifier_structured else "warning"
            verification = build_verification_result(
                resource_type=resource_type,
                course_id=course_id,
                chapter_id=chapter_id_final,
                verifier_status=v_status,  # type: ignore[arg-type]
                safety_status=(safety_structured.status if safety_structured else "warning"),  # type: ignore[arg-type]
                grounded_chunks=chunks_to_grounded(chunks),
                hallucination_risks=list(verifier_structured.hallucination_risks if verifier_structured else []),
                unsupported_claims=list(verifier_structured.unsupported_claims if verifier_structured else []),
                sensitive_risks=list(safety_structured.sensitive_risks if safety_structured else []),
                prompt_injection_risks=list(safety_structured.prompt_injection_risks if safety_structured else []),
                retry_count=0,
                final_decision="publish" if gen_meta.get("verified") and passed_safety else "draft",
            )

        gen_meta["status"] = "published" if verification.final_decision == "publish" else "draft"
        gen_meta["verification"] = verification.to_meta_dict()
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
        gen_meta["collaboration_log"] = list(ctx.collaboration_log)
        gen_meta["agent_logs"] = list(ctx.agent_logs)
        gen_meta["_evidence_version"] = 1
        gen_meta["_content_hash"] = hashlib.sha256(safe_text.encode()).hexdigest()[:16] if safe_text else ""
        gen_meta["fallback"] = True
        gen_meta["fallback_reason"] = fallback_reason
        gen_meta["generated_by"] = GENERATED_BY

        from services.evidence.builder import build_evidence_from_meta
        gen_meta["evidence"] = build_evidence_from_meta(
            resource_id=0,
            agent_name=GENERATED_BY,
            meta={**gen_meta, "_content_for_hash": safe_text},
            created_at="",
            profile_summary="",
        ).model_dump()
        ctx.update_from_resource(resource_type, safe_text)
        await _emit(
            "persist",
            "Orchestrator",
            "success" if gen_meta.get("status") == "published" else "failed",
            gen_meta.get("status", ""),
            validation_result={"final_decision": verification.final_decision},
        )
        return title, safe_text, gen_meta


fallback_resource_workflow = FallbackResourceWorkflow()
