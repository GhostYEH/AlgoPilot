"""信任证据链构建（evidence builder）单元测试。

AlgoPilot 核心创新：AI 生成资源必须携带可验证的信任证据链，
而非纯自然语言。覆盖 build_evidence_from_meta 对各种 meta 的解析。
"""

from __future__ import annotations

from services.evidence.builder import build_evidence_from_meta


class TestBuildEvidenceFromMeta:
    def test_minimal_meta(self):
        ev = build_evidence_from_meta(
            resource_id=1,
            agent_name="ConceptAgent",
            meta={},
            created_at="2026-08-12T00:00:00Z",
        )
        assert ev.resource_id == 1
        assert ev.agent_name == "ConceptAgent"
        assert ev.verifier_status == "warning"
        assert ev.safety_status == "warning"
        assert ev.retry_count == 0
        assert ev.used_fallback is False
        assert ev.knowledge_chunks == []

    def test_published_decision(self):
        ev = build_evidence_from_meta(
            resource_id=2,
            agent_name="GraphAgent",
            meta={"verification": {"final_decision": "published"}},
            created_at="2026-08-12T00:00:00Z",
        )
        assert ev.final_decision == "publish"
        assert ev.human_review == "not_required"

    def test_draft_decision_requires_human_review(self):
        ev = build_evidence_from_meta(
            resource_id=3,
            agent_name="ScenarioAgent",
            meta={"status": "draft"},
            created_at="2026-08-12T00:00:00Z",
        )
        assert ev.final_decision == "draft"
        assert ev.human_review == "pending"

    def test_blocked_decision_requires_human_review(self):
        ev = build_evidence_from_meta(
            resource_id=4,
            agent_name="TraceAgent",
            meta={"verification": {"final_decision": "blocked"}},
            created_at="2026-08-12T00:00:00Z",
        )
        assert ev.final_decision == "blocked"
        assert ev.human_review == "pending"

    def test_fallback_flag(self):
        ev = build_evidence_from_meta(
            resource_id=5,
            agent_name="ConceptAgent",
            meta={"fallback": True},
            created_at="2026-08-12T00:00:00Z",
        )
        assert ev.used_fallback is True
        assert ev.fallback_reason

    def test_template_fallback_agent(self):
        ev = build_evidence_from_meta(
            resource_id=6,
            agent_name="ConceptAgent",
            meta={"generated_by": "TemplateFallbackAgent"},
            created_at="2026-08-12T00:00:00Z",
        )
        assert ev.used_fallback is True

    def test_knowledge_chunks_from_sources(self):
        ev = build_evidence_from_meta(
            resource_id=7,
            agent_name="ConceptAgent",
            meta={
                "sources": [
                    {
                        "chunk_id": "c1",
                        "chapter_title": "二分查找",
                        "excerpt": "有序数组 O(log n)",
                        "module_id": "array",
                        "relevance_score": 0.92,
                    }
                ]
            },
            created_at="2026-08-12T00:00:00Z",
        )
        assert len(ev.knowledge_chunks) == 1
        chunk = ev.knowledge_chunks[0]
        assert chunk.chunk_id == "c1"
        assert chunk.chapter_title == "二分查找"
        assert chunk.relevance_score == pytest_approx(0.92)

    def test_retry_count_from_verification(self):
        ev = build_evidence_from_meta(
            resource_id=8,
            agent_name="ConceptAgent",
            meta={"verification": {"retry_count": 2}},
            created_at="2026-08-12T00:00:00Z",
        )
        assert ev.retry_count == 2

    def test_hallucination_risks_propagated(self):
        risks = ["未在知识库中找到支撑", "引用了不存在的定理"]
        ev = build_evidence_from_meta(
            resource_id=9,
            agent_name="ConceptAgent",
            meta={"verification": {"hallucination_risks": risks}},
            created_at="2026-08-12T00:00:00Z",
        )
        assert ev.hallucination_risks == risks

    def test_content_hash_stable(self):
        meta = {"_content_for_hash": "二分查找讲解"}
        ev1 = build_evidence_from_meta(
            resource_id=10, agent_name="ConceptAgent", meta=meta, created_at="2026-08-12T00:00:00Z"
        )
        ev2 = build_evidence_from_meta(
            resource_id=11, agent_name="ConceptAgent", meta=meta, created_at="2026-08-12T00:00:00Z"
        )
        assert ev1.content_hash == ev2.content_hash
        assert len(ev1.content_hash) == 16

    def test_timeline_built(self):
        ev = build_evidence_from_meta(
            resource_id=12,
            agent_name="ConceptAgent",
            meta={
                "agent_logs": [
                    {"agent": "ConceptAgent", "status": "ok", "latency_ms": 1200}
                ],
                "verification": {"verifier_status": "passed", "safety_status": "passed"},
            },
            created_at="2026-08-12T00:00:00Z",
        )
        assert len(ev.timeline) > 0


def pytest_approx(expected: float, rel: float = 1e-9):
    import pytest

    return pytest.approx(expected, rel=rel)