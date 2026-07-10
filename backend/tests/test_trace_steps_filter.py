from __future__ import annotations

from services.oj.trace_runner import TraceStepOut
from services.oj.trace_steps_filter import collapse_consecutive_same_line_steps


def test_collapse_same_line_keeps_initialized_container_frame() -> None:
    steps = [
        TraceStepOut(
            line=4,
            vars={"a": {"type": "sequence", "view_hint": "array", "value": [0, 999]}},
            changed=["a"],
        ),
        TraceStepOut(
            line=4,
            vars={"a": {"type": "sequence", "view_hint": "array", "value": [3, 4]}},
            changed=["a"],
        ),
        TraceStepOut(
            line=5,
            vars={
                "a": {"type": "sequence", "view_hint": "array", "value": [3, 4]},
                "i": {"type": "int", "value": 0},
            },
            changed=["i"],
        ),
    ]

    collapsed = collapse_consecutive_same_line_steps(steps)

    assert [step.line for step in collapsed] == [4, 5]
    assert collapsed[0].vars["a"]["value"] == [3, 4]
    assert collapsed[0].changed == ["a"]
    assert collapsed[1].changed == ["i"]


def test_collapse_same_line_preserves_multiple_statements() -> None:
    steps = [
        TraceStepOut(line=1, vars={"a": {"type": "int", "value": 0}}, changed=["a"]),
        TraceStepOut(line=1, vars={"a": {"type": "int", "value": 1}}, changed=["a"]),
        TraceStepOut(
            line=1,
            vars={"a": {"type": "int", "value": 1}, "b": {"type": "int", "value": 2}},
            changed=["b"],
        ),
        TraceStepOut(
            line=1,
            vars={
                "a": {"type": "int", "value": 1},
                "b": {"type": "int", "value": 2},
                "c": {"type": "int", "value": 3},
            },
            changed=["c"],
        ),
    ]

    collapsed = collapse_consecutive_same_line_steps(steps)

    assert len(collapsed) == 3
    assert [step.changed for step in collapsed] == [["a"], ["b"], ["c"]]
