"""AI 轨迹诊断：压缩与兜底逻辑单元测试（无需 LLM）。"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.oj.ai_diagnosis import (  # noqa: E402
    _fallback_trace_bug_diagnosis,
    _normalize_bug_step_index,
    compress_trace_steps_to_text,
    diagnose_trace_bug,
)


def test_compress_skips_empty_changed() -> None:
    steps = [
        {"line": 1, "changed": [], "vars": {}},
        {"line": 5, "changed": ["left", "right"], "vars": {"left": {"type": "int", "value": 2}, "right": {"type": "int", "value": 5}}},
    ]
    lines, count = compress_trace_steps_to_text(steps)
    assert count == 1
    assert len(lines) == 1
    assert lines[0].startswith("Step 1")
    assert "left=2" in lines[0]
    assert "right=5" in lines[0]


def test_normalize_bug_step_index_snaps_to_changed() -> None:
    steps = [
        {"line": 1, "changed": [], "vars": {}},
        {"line": 2, "changed": ["i"], "vars": {"i": {"type": "int", "value": 1}}},
    ]
    assert _normalize_bug_step_index(0, steps) == 1
    assert _normalize_bug_step_index(99, steps) == 1


def test_fallback_finds_stagnant_pointer() -> None:
    steps = []
    for i in range(6):
        steps.append(
            {
                "line": 10,
                "changed": ["left"],
                "vars": {"left": {"type": "int", "value": 0}},
            }
        )
    lines, _ = compress_trace_steps_to_text(steps)
    out = _fallback_trace_bug_diagnosis(steps, lines)
    assert out["bug_step_index"] >= 2
    assert "left" in out["diagnosis_title"] or "left" in out["detailed_analysis"]


def test_diagnose_empty_steps() -> None:
    out = asyncio.run(diagnose_trace_bug("sum", "def f(): pass", []))
    assert out["source"] == "empty"
    assert out["bug_step_index"] == 0


def main() -> None:
    test_compress_skips_empty_changed()
    test_normalize_bug_step_index_snaps_to_changed()
    test_fallback_finds_stagnant_pointer()
    test_diagnose_empty_steps()
    print("test_trace_bug_diagnose: OK")


if __name__ == "__main__":
    main()
