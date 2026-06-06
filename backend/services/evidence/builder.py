from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from schemas.evidence import (
    EvidenceChunkRef,
    EvidenceTimelineStep,
    TrustEvidence,
)


def build_evidence_from_meta(
    *,
    resource_id: int,
    agent_name: str,
    meta: dict,
    created_at: str,
    profile_summary: str = "",
) -> TrustEvidence:
    verification = meta.get("verification") or {}
    safety_panel = meta.get("safety_panel") or {}
    agent_logs = meta.get("agent_logs") or []
    knowledge_refs = meta.get("knowledge_refs") or []
    knowledge_chunk_ids = meta.get("knowledge_chunk_ids") or []
    chunks_raw = verification.get("grounded_chunks") or []

    chunks: list[EvidenceChunkRef] = []
    for c in chunks_raw:
        if isinstance(c, dict):
            chunks.append(
                EvidenceChunkRef(
                    chunk_id=str(c.get("id") or c.get("chunk_id") or ""),
                    title=str(c.get("title") or ""),
                    snippet=str(c.get("snippet") or ""),
                )
            )
    if not chunks and knowledge_chunk_ids:
        for cid in knowledge_chunk_ids:
            chunks.append(EvidenceChunkRef(chunk_id=str(cid)))
    if not chunks and knowledge_refs:
        for ref in knowledge_refs:
            chunks.append(EvidenceChunkRef(chunk_id=str(ref)))

    verifier_status = verification.get("verifier_status") or "warning"
    safety_status = verification.get("safety_status") or "warning"
    retry_count = int(verification.get("retry_count") or meta.get("verify_attempts") or 0)
    final_decision = verification.get("final_decision") or meta.get("status") or "draft"
    if final_decision == "published":
        final_decision = "publish"
    used_fallback = bool(meta.get("fallback") or meta.get("generated_by") == "TemplateFallbackAgent")
    fallback_reason = str(meta.get("fallback_reason") or "")
    if not fallback_reason and used_fallback:
        fallback_reason = "LLM 不可用，使用课程知识库模板降级生成"

    content_hash = ""
    content = meta.get("_content_for_hash") or ""
    if content:
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

    human_review = "not_required"
    if final_decision == "draft":
        human_review = "pending"
    elif final_decision == "blocked":
        human_review = "pending"

    timeline = _build_timeline(
        agent_logs=agent_logs,
        safety_panel=safety_panel,
        verification=verification,
        used_fallback=used_fallback,
        fallback_reason=fallback_reason,
        created_at=created_at,
    )

    return TrustEvidence(
        resource_id=resource_id,
        agent_name=agent_name,
        agent_role=str(meta.get("agent_role") or ""),
        profile_summary=profile_summary,
        knowledge_chunks=chunks,
        verifier_status=verifier_status,
        safety_status=safety_status,
        retry_count=retry_count,
        used_fallback=used_fallback,
        fallback_reason=fallback_reason,
        generated_at=created_at,
        content_hash=content_hash,
        version=int(meta.get("_evidence_version") or 1),
        human_review=human_review,
        timeline=timeline,
        hallucination_risks=list(verification.get("hallucination_risks") or []),
        unsupported_claims=list(verification.get("unsupported_claims") or []),
        final_decision=final_decision,
    )


def _build_timeline(
    *,
    agent_logs: list,
    safety_panel: dict,
    verification: dict,
    used_fallback: bool,
    fallback_reason: str,
    created_at: str,
) -> list[EvidenceTimelineStep]:
    steps: list[EvidenceTimelineStep] = []
    now = datetime.now(timezone.utc).isoformat()

    rag_done = False
    agent_done = False
    verify_done = False
    safety_done = False

    for entry in agent_logs:
        if not isinstance(entry, dict):
            continue
        agent = str(entry.get("agent") or "")
        action = str(entry.get("action") or "")
        detail = str(entry.get("detail") or "")

        if agent == "KnowledgeRetriever" and not rag_done:
            rag_done = True
            steps.append(
                EvidenceTimelineStep(
                    stage="rag_retrieve",
                    agent="KnowledgeRetriever",
                    status="passed" if "命中" in detail else "warning",
                    detail=detail or "BM25 检索课程知识库",
                    timestamp=now,
                )
            )
        elif action == "generate" and not agent_done:
            agent_done = True
            steps.append(
                EvidenceTimelineStep(
                    stage="agent_generate",
                    agent=agent,
                    status="passed",
                    detail=detail or "角色 Agent 生成内容",
                    timestamp=now,
                )
            )
        elif action in ("verify_pass", "verify_fail") and not verify_done:
            verify_done = True
            v_status = verification.get("verifier_status") or "warning"
            steps.append(
                EvidenceTimelineStep(
                    stage="content_verify",
                    agent="ContentVerifierAgent",
                    status=v_status if v_status in ("passed", "warning", "failed") else "warning",
                    detail=detail or ("校验通过" if action == "verify_pass" else "校验未通过"),
                    timestamp=now,
                )
            )
        elif agent == "SafetyAgent" and ("安全" in detail or "审查" in detail) and not safety_done:
            safety_done = True
            s_status = verification.get("safety_status") or "warning"
            steps.append(
                EvidenceTimelineStep(
                    stage="safety_filter",
                    agent="SafetyAgent",
                    status=s_status if s_status in ("passed", "warning", "failed") else "warning",
                    detail=detail,
                    timestamp=now,
                )
            )

    if not rag_done:
        steps.insert(
            0,
            EvidenceTimelineStep(
                stage="rag_retrieve",
                agent="KnowledgeRetriever",
                status="warning",
                detail="检索记录缺失",
                timestamp=now,
            ),
        )
    if not agent_done:
        steps.append(
            EvidenceTimelineStep(
                stage="agent_generate",
                agent="—",
                status="warning",
                detail="生成记录缺失",
                timestamp=now,
            ),
        )
    if not verify_done:
        v_status = verification.get("verifier_status") or "warning"
        steps.append(
            EvidenceTimelineStep(
                stage="content_verify",
                agent="ContentVerifierAgent",
                status=v_status if v_status in ("passed", "warning", "failed") else "warning",
                detail=verification.get("skip_reason") or "校验记录缺失",
                timestamp=now,
            ),
        )
    if not safety_done:
        s_status = verification.get("safety_status") or "warning"
        steps.append(
            EvidenceTimelineStep(
                stage="safety_filter",
                agent="SafetyAgent",
                status=s_status if s_status in ("passed", "warning", "failed") else "warning",
                detail="安全审查记录缺失",
                timestamp=now,
            ),
        )

    steps.append(
        EvidenceTimelineStep(
            stage="persist",
            agent="Orchestrator",
            status="passed" if verification.get("final_decision") == "publish" else "warning",
            detail="已落库" + ("（模板降级）" if used_fallback else ""),
            timestamp=created_at or now,
        )
    )

    return steps
