"""资源防幻觉与内容安全校验结果。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

VerifyStatus = Literal["passed", "warning", "failed"]
FinalDecision = Literal["publish", "draft", "blocked"]


class GroundedChunkRef(BaseModel):
    id: str
    title: str = ""
    snippet: str = ""
    module_id: str = ""
    chapter_title: str = ""
    section_title: str = ""
    source_path: str = ""
    relevance_score: float = 0.0


class ResourceVerificationResult(BaseModel):
    resource_id: int = 0
    resource_type: str = ""
    course_id: str = "data_structures_algorithms"
    chapter_id: str = ""
    verifier_status: VerifyStatus = "warning"
    safety_status: VerifyStatus = "warning"
    grounded_chunks: list[GroundedChunkRef] = Field(default_factory=list)
    hallucination_risks: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    sensitive_risks: list[str] = Field(default_factory=list)
    prompt_injection_risks: list[str] = Field(default_factory=list)
    retry_count: int = 0
    skip_reason: str = Field(default="", description="跳过文本校验时的原因")
    final_decision: FinalDecision = "draft"
    risk_label: str = Field(default="未校验", description="前端展示：无风险/可能幻觉/安全警告/已重试")
    evidence_count: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_meta_dict(self) -> dict:
        return self.model_dump()
