"""Agent 输出 strict schema。"""

from __future__ import annotations

from schemas.agent_outputs import validate_quiz_payload


def test_quiz_strict_accepts_valid() -> None:
    out, issues = validate_quiz_payload(
        {
            "questions": [
                {
                    "type": "choice",
                    "stem": "测试题",
                    "options": ["A", "B"],
                    "hint": "提示",
                    "focus": "边界",
                    "difficulty": "easy",
                }
            ]
        }
    )
    assert out is not None
    assert not issues


def test_quiz_strict_rejects_extra_fields() -> None:
    out, issues = validate_quiz_payload(
        {
            "questions": [
                {
                    "type": "choice",
                    "stem": "x",
                    "options": ["A", "B"],
                    "unknown_field": True,
                }
            ]
        }
    )
    assert out is None
    assert issues
