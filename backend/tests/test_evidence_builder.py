from schemas.evidence import TrustEvidence
from services.evidence.builder import build_evidence_from_meta


def test_build_evidence_basic():
    meta = {
        "verification": {
            "verifier_status": "passed",
            "safety_status": "passed",
            "grounded_chunks": [
                {"id": "chunk-01", "title": "数组基础", "snippet": "数组是线性表…"},
            ],
            "hallucination_risks": [],
            "unsupported_claims": [],
            "retry_count": 0,
            "final_decision": "publish",
        },
        "agent_logs": [
            {"agent": "KnowledgeRetriever", "action": "retrieve", "detail": "命中 3 条"},
            {"agent": "ConceptAgent", "action": "generate", "detail": "产出 content"},
            {"agent": "ContentVerifierAgent", "action": "verify_pass", "detail": "校验通过"},
            {"agent": "SafetyAgent", "action": "audit", "detail": "内容安全审查通过"},
        ],
        "knowledge_refs": ["chunk-01"],
        "verify_attempts": 1,
        "status": "published",
        "_content_for_hash": "测试内容",
    }
    ev = build_evidence_from_meta(
        resource_id=42,
        agent_name="ConceptAgent",
        meta=meta,
        created_at="2026-06-01T10:00:00",
        profile_summary="初学者，偏视觉型",
    )
    assert isinstance(ev, TrustEvidence)
    assert ev.resource_id == 42
    assert ev.agent_name == "ConceptAgent"
    assert ev.verifier_status == "passed"
    assert ev.safety_status == "passed"
    assert ev.final_decision == "publish"
    assert len(ev.knowledge_chunks) == 1
    assert ev.knowledge_chunks[0].chunk_id == "chunk-01"
    assert ev.human_review == "not_required"
    assert ev.used_fallback is False
    assert ev.content_hash != ""
    assert ev.profile_summary == "初学者，偏视觉型"
    assert len(ev.timeline) >= 5


def test_build_evidence_fallback():
    meta = {
        "verification": {
            "verifier_status": "warning",
            "safety_status": "passed",
            "grounded_chunks": [],
            "retry_count": 0,
            "final_decision": "publish",
        },
        "agent_logs": [],
        "fallback": True,
        "fallback_reason": "LLM key missing",
        "generated_by": "TemplateFallbackAgent",
        "status": "published",
        "_content_for_hash": "模板内容",
    }
    ev = build_evidence_from_meta(
        resource_id=99,
        agent_name="TemplateFallbackAgent",
        meta=meta,
        created_at="2026-06-01T10:00:00",
    )
    assert ev.used_fallback is True
    assert ev.fallback_reason == "LLM key missing"
    assert ev.human_review == "not_required"


def test_build_evidence_draft():
    meta = {
        "verification": {
            "verifier_status": "failed",
            "safety_status": "warning",
            "grounded_chunks": [],
            "hallucination_risks": ["含可疑题号"],
            "unsupported_claims": [],
            "retry_count": 2,
            "final_decision": "draft",
        },
        "agent_logs": [],
        "status": "draft",
        "_content_for_hash": "有问题的内容",
    }
    ev = build_evidence_from_meta(
        resource_id=100,
        agent_name="QuizAgent",
        meta=meta,
        created_at="2026-06-01T10:00:00",
    )
    assert ev.verifier_status == "failed"
    assert ev.safety_status == "warning"
    assert ev.retry_count == 2
    assert ev.final_decision == "draft"
    assert ev.human_review == "pending"
    assert len(ev.hallucination_risks) == 1


def test_build_evidence_old_data_compat():
    meta = {
        "verified": True,
        "status": "published",
        "knowledge_refs": ["chunk-old-1", "chunk-old-2"],
        "agent_logs": [
            {"agent": "KnowledgeRetriever", "action": "retrieve", "detail": "命中 2 条"},
        ],
        "_content_for_hash": "旧内容",
    }
    ev = build_evidence_from_meta(
        resource_id=1,
        agent_name="ConceptAgent",
        meta=meta,
        created_at="2025-12-01T08:00:00",
    )
    assert ev.resource_id == 1
    assert len(ev.knowledge_chunks) == 2
    assert ev.knowledge_chunks[0].chunk_id == "chunk-old-1"
    assert ev.used_fallback is False
