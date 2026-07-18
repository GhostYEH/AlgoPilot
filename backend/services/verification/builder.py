"""资源校验结果构建。"""

from __future__ import annotations

from services.knowledge.retriever import KnowledgeChunk
from schemas.verification import GroundedChunkRef, ResourceVerificationResult, VerifyStatus


def chunks_to_grounded(chunks: list[KnowledgeChunk]) -> list[GroundedChunkRef]:
    out: list[GroundedChunkRef] = []
    for c in chunks:
        content = str(c.get("content") or "")
        out.append(
            GroundedChunkRef(
                id=str(c.get("id") or ""),
                title=str(c.get("title") or ""),
                snippet=content[:120].replace("\n", " "),
                module_id=str(c.get("module_id") or c.get("module_key") or ""),
                chapter_title=str(c.get("chapter_title") or ""),
                section_title=str(c.get("section_title") or c.get("section") or ""),
                source_path=str(c.get("source_path") or ""),
                relevance_score=float(c.get("relevance_score") or 0.0),
            )
        )
    return out


def _risk_label(
    *,
    verifier_status: VerifyStatus,
    safety_status: VerifyStatus,
    hallucination_risks: list[str],
    sensitive_risks: list[str],
    prompt_injection_risks: list[str],
    retry_count: int,
) -> str:
    labels: list[str] = []
    if retry_count > 0:
        labels.append("已重试")
    if prompt_injection_risks or sensitive_risks or safety_status == "failed":
        labels.append("安全警告")
    elif safety_status == "warning":
        labels.append("安全警告")
    if hallucination_risks or verifier_status == "warning":
        labels.append("可能幻觉")
    if not labels and verifier_status == "passed" and safety_status == "passed":
        return "无风险"
    return " / ".join(dict.fromkeys(labels)) if labels else "待复核"


def build_verification_result(
    *,
    resource_id: int = 0,
    resource_type: str,
    course_id: str = "data_structures_algorithms",
    chapter_id: str = "",
    verifier_status: VerifyStatus = "warning",
    safety_status: VerifyStatus = "warning",
    grounded_chunks: list[GroundedChunkRef] | None = None,
    hallucination_risks: list[str] | None = None,
    unsupported_claims: list[str] | None = None,
    sensitive_risks: list[str] | None = None,
    prompt_injection_risks: list[str] | None = None,
    retry_count: int = 0,
    skip_reason: str = "",
    final_decision: str = "draft",
) -> ResourceVerificationResult:
    v_status = verifier_status
    s_status = safety_status
    hall = list(hallucination_risks or [])
    unsup = list(unsupported_claims or [])
    sens = list(sensitive_risks or [])
    inj = list(prompt_injection_risks or [])
    grounded = list(grounded_chunks or [])

    decision = final_decision
    if decision not in ("publish", "draft", "blocked"):
        if s_status == "failed" or inj:
            decision = "blocked"
        elif v_status == "failed":
            decision = "draft"
        elif v_status == "passed" and s_status == "passed" and not hall:
            decision = "publish"
        else:
            decision = "draft"

    return ResourceVerificationResult(
        resource_id=resource_id,
        resource_type=resource_type,
        course_id=course_id,
        chapter_id=chapter_id,
        verifier_status=v_status,
        safety_status=s_status,
        grounded_chunks=grounded,
        hallucination_risks=hall,
        unsupported_claims=unsup,
        sensitive_risks=sens,
        prompt_injection_risks=inj,
        retry_count=retry_count,
        skip_reason=skip_reason,
        final_decision=decision,  # type: ignore[arg-type]
        risk_label=_risk_label(
            verifier_status=v_status,
            safety_status=s_status,
            hallucination_risks=hall,
            sensitive_risks=sens,
            prompt_injection_risks=inj,
            retry_count=retry_count,
        ),
        evidence_count=len(grounded),
    )


def verification_for_skipped_type(
    resource_type: str,
    *,
    course_id: str = "data_structures_algorithms",
    chapter_id: str = "",
    chunks: list[KnowledgeChunk] | None = None,
    trace_verdict: str = "",
) -> ResourceVerificationResult:
    reason = (
        f"{resource_type} 由专用执行管线生成（如 trace_runner），跳过 ContentVerifier 文本对照校验；"
        f"仍执行 SafetyAgent 审查。trace_verdict={trace_verdict or 'n/a'}"
    )
    trace_ok = resource_type != "trace_animation" or trace_verdict.upper() in {"AC", "OK"}
    return build_verification_result(
        resource_type=resource_type,
        course_id=course_id,
        chapter_id=chapter_id,
        verifier_status="warning",
        safety_status="passed",
        grounded_chunks=chunks_to_grounded(chunks or []),
        skip_reason=reason,
        retry_count=0,
        final_decision="publish" if trace_ok else "draft",
    )
