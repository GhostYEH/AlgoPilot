from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


EvidenceStatus = Literal["passed", "warning", "failed"]
HumanReviewStatus = Literal["pending", "not_required", "approved", "rejected"]


class EvidenceChunkRef(BaseModel):
    chunk_id: str = Field(default="", description="知识库 chunk_id 或 source_id")
    title: str = ""
    snippet: str = ""


class EvidenceTimelineStep(BaseModel):
    stage: str
    agent: str
    status: EvidenceStatus
    detail: str = ""
    timestamp: str = ""


class TrustEvidence(BaseModel):
    resource_id: int
    agent_name: str = ""
    agent_role: str = ""
    profile_summary: str = ""
    knowledge_chunks: list[EvidenceChunkRef] = Field(default_factory=list)
    verifier_status: EvidenceStatus = "warning"
    safety_status: EvidenceStatus = "warning"
    retry_count: int = 0
    used_fallback: bool = False
    fallback_reason: str = ""
    generated_at: str = ""
    content_hash: str = ""
    version: int = 1
    human_review: HumanReviewStatus = "not_required"
    timeline: list[EvidenceTimelineStep] = Field(default_factory=list)
    hallucination_risks: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    final_decision: Literal["publish", "draft", "blocked"] = "draft"
