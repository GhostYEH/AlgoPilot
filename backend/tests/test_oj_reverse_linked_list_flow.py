"""链表反转 WA -> Trace -> 规则诊断 -> 学习干预闭环。"""

from __future__ import annotations

from dataclasses import asdict

import pytest
from fastapi.testclient import TestClient

from main import app
from services.oj.ai_diagnosis import diagnose_trace_bug
from services.oj.problem_store import get_cases, get_problem
from services.oj.stdio_runner import run_cases_stdio
from services.oj.trace_demo_narration import generate_demo_narration
from services.oj.trace_report import generate_trace_diagnosis_report
from services.oj.trace_runner import run_trace_stdio
from services.oj.tutoring_pipeline import apply_oj_tutoring

client = TestClient(app)

DEMO_WRONG_CODE = """import sys


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def main():
    data = list(map(int, sys.stdin.read().split()))
    n = data[0]
    values = data[1:1 + n]

    dummy = ListNode()
    tail = dummy
    for value in values:
        tail.next = ListNode(value)
        tail = tail.next

    prev = None
    curr = dummy.next
    while curr:
        curr.next = prev
        nxt = curr.next
        prev = curr
        curr = nxt

    answer = []
    curr = prev
    while curr:
        answer.append(curr.val)
        curr = curr.next
    print(*answer)


if __name__ == '__main__':
    main()
"""


def _demo_trace() -> tuple[dict, list[dict]]:
    problem = get_problem("reverse-linked-list")
    first_case = get_cases("reverse-linked-list", mode="submit")[0]
    summary = run_trace_stdio(DEMO_WRONG_CODE, case=first_case, language="python")
    assert summary.verdict == "OK", summary.message
    return problem, [asdict(step) for step in summary.steps]


def test_reverse_linked_list_demo_code_is_real_wrong_answer() -> None:
    cases = get_cases("reverse-linked-list", mode="submit")
    summary = run_cases_stdio(DEMO_WRONG_CODE, cases=cases, language="python")

    assert summary.passed == 0
    assert summary.cases[0].verdict == "WA"
    assert summary.cases[0].expected_preview == "5 4 3 2 1"
    assert summary.cases[0].actual_preview == "1"


@pytest.mark.asyncio
async def test_reverse_linked_list_rule_diagnosis_does_not_call_llm(monkeypatch) -> None:
    problem, steps = _demo_trace()

    async def _llm_must_not_run(*_args, **_kwargs):
        raise AssertionError("known demo diagnosis must not call the LLM")

    monkeypatch.setattr("services.llm.client.chat_completion", _llm_must_not_run)

    diagnosis = await diagnose_trace_bug(
        problem.get("description", ""),
        DEMO_WRONG_CODE,
        steps,
        slug="reverse-linked-list",
    )

    bug_step = steps[diagnosis["bug_step_index"]]
    save_line = next(
        index
        for index, line in enumerate(DEMO_WRONG_CODE.splitlines(), start=1)
        if line.strip() == "nxt = curr.next"
    )
    assert diagnosis["source"] == "rule:reverse_linked_list_save_order"
    assert diagnosis["error_type"] == "pointer_update_error"
    assert diagnosis["error_type_label"] == "指针更新顺序错误"
    assert bug_step["line"] == save_line
    assert bug_step["vars"]["nxt"]["value"]["node"] is None
    assert "WA" in diagnosis["why_failed"]
    assert "nxt = curr.next" in diagnosis["fix_suggestion"]
    assert "链表反转的三指针循环不变量" in diagnosis["recommended_knowledge_points"]


def test_reverse_linked_list_report_generates_intervention_and_resources() -> None:
    problem, steps = _demo_trace()
    tutoring = apply_oj_tutoring(
        None,
        None,
        slug="reverse-linked-list",
        problem=problem,
        bug_step_index=0,
        diagnosis_title="规则诊断",
        detailed_analysis="后继指针保存过晚，链表断链",
        edge_verdict="WA",
        code=DEMO_WRONG_CODE,
        write_memory=False,
    )
    report = generate_trace_diagnosis_report(
        user_code=DEMO_WRONG_CODE,
        judge_verdict="WA",
        failed_cases=[
            {
                "index": 0,
                "verdict": "WA",
                "message": "答案不匹配",
                "expected_preview": "5 4 3 2 1",
                "actual_preview": "1",
            }
        ],
        trace_steps=steps,
        bug_step_index=0,
        diagnosis_title="规则诊断",
        detailed_analysis="",
        problem=problem,
        slug="reverse-linked-list",
        tutoring=tutoring,
    )

    topics = {item.topic for item in report.recommended_resources}
    assert report.error_category == "pointer_update_error"
    assert report.error_category_label == "指针更新顺序错误"
    assert any(
        item.variable_name == "nxt" and item.after == "node@None"
        for item in report.key_variable_changes
    )
    assert report.learning_intervention_generated is True
    assert report.path_rearrange_triggered is True
    assert "链表三指针循环不变量" in report.intervention_suggestion
    assert "插入" in report.intervention_suggestion
    assert topics == {"指针更新动画", "边界条件练习", "错题复盘卡"}


def test_reverse_linked_list_demo_narration_marks_broken_link() -> None:
    _, steps = _demo_trace()
    narrations = generate_demo_narration(
        "reverse-linked-list",
        DEMO_WRONG_CODE,
        steps,
    )

    assert narrations is not None
    assert any("nxt 变为 null" in str(item["text"]) for item in narrations)


def test_trace_report_replays_the_actual_failed_case() -> None:
    response = client.post(
        "/api/oj/problems/reverse-linked-list/trace-report",
        json={
            "code": DEMO_WRONG_CODE,
            "language": "python",
            "judge_verdict": "WA",
            "failed_cases": [
                {
                    "index": 0,
                    "verdict": "WA",
                    "message": "答案不匹配",
                    "input_preview": "5 1 2 3 4 5",
                    "expected_preview": "5 4 3 2 1",
                    "actual_preview": "1",
                }
            ],
        },
    )

    assert response.status_code == 200, response.text
    report = response.json()
    assert report["trace_case_reproduced"] is True
    assert report["diagnosis_confidence"] == "high"
    assert "复现 WA" in report["evidence_summary"]
    assert report["source"] == "rule:reverse_linked_list_save_order"
