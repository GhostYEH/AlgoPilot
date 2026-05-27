"""generate-all 复用资源时仍应填充 PipelineContext。"""

from __future__ import annotations

from services.orchestrator.pipeline_context import PipelineContext


def test_reuse_seeds_doc_summary_for_downstream() -> None:
    ctx = PipelineContext()
    md = "## 数组\n\n数组是连续存储的结构，适合随机访问。"
    ctx.update_from_resource("document", md)
    assert ctx.doc_summary
    assert "ConceptAgent" in (ctx.collaboration_log[-1].get("agent") or "")
