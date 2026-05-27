"""画像指纹与增量复用逻辑。"""

from __future__ import annotations

from services.orchestrator.persona_fingerprint import (
    cache_key,
    fingerprint_for_resource,
    should_skip_generation,
)


class _FakeProfile:
    def __init__(self, summary: str = "测试", dimensions: dict | None = None):
        self.summary = summary
        self.dimensions = dimensions or {
            "_dimension_scores": {
                "knowledge_base": 5,
                "coding_ability": 5,
            }
        }


class _FakeResource:
    resource_type = "document"

    def __init__(self, meta: dict):
        self.meta = meta


def test_fingerprint_stable_for_same_input() -> None:
    row = _FakeProfile()
    a = fingerprint_for_resource(
        row,
        resource_type="document",
        topic="栈",
        module_key="stack-queue",
        focus_hint="",
    )
    b = fingerprint_for_resource(
        row,
        resource_type="document",
        topic="栈",
        module_key="stack-queue",
        focus_hint="",
    )
    assert a == b


def test_skip_when_fingerprint_unchanged() -> None:
    row = _FakeProfile(
        dimensions={
            "_dimension_scores": {"knowledge_base": 6},
            "_resource_generation_fps": {
                cache_key("document", "栈", "stack-queue"): fingerprint_for_resource(
                    _FakeProfile(dimensions={"_dimension_scores": {"knowledge_base": 6}}),
                    resource_type="document",
                    topic="栈",
                    module_key="stack-queue",
                    focus_hint="",
                )
            },
        }
    )
    fp = fingerprint_for_resource(
        row,
        resource_type="document",
        topic="栈",
        module_key="stack-queue",
        focus_hint="",
    )
    row.dimensions["_resource_generation_fps"][cache_key("document", "栈", "stack-queue")] = fp
    existing = _FakeResource({"topic": "栈", "module_key": "stack-queue"})
    skip, reason = should_skip_generation(
        row,
        existing,  # type: ignore[arg-type]
        resource_type="document",
        topic="栈",
        module_key="stack-queue",
        focus_hint="",
    )
    assert skip is True
    assert "复用" in reason
