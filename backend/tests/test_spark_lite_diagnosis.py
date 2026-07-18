from __future__ import annotations

import json

from services.llm import client
from services.oj.ai_diagnosis import _parse_trace_bug_diagnosis
from services.oj.rule_diagnosis import diagnose_known_error_pattern


def test_spark_lite_moves_system_instruction_into_user_message(monkeypatch):
    monkeypatch.setattr(client.settings, "spark_model", "lite")
    prepared = client._prepare_messages(
        [
            {"role": "system", "content": "只输出 JSON"},
            {"role": "user", "content": "分析这段轨迹"},
        ]
    )
    assert [m["role"] for m in prepared] == ["user"]
    assert "只输出 JSON" in prepared[0]["content"]
    assert "分析这段轨迹" in prepared[0]["content"]


def test_guided_diagnosis_keeps_useful_evidence_when_wording_is_not_exact():
    steps = [
        {
            "line": 18,
            "changed": ["st"],
            "vars": {"st": {"type": "stack", "value": ["("]}},
        }
    ]
    raw = json.dumps(
        {
            "bug_step_index": 0,
            "diagnosis_title": "匹配后栈顶元素没有弹出",
            "detailed_analysis": "代码第18行完成匹配检查后，实际栈仍保留左括号；正确状态应移除已匹配元素。",
            "actual_state": "st=['(']",
            "expected_state": "st=[]",
            "invariant": "处理完一对匹配括号后，栈中只保留尚未匹配的左括号",
            "observation_question": "右括号匹配成功后，栈顶发生了什么变化？",
            "hints": [
                {"level": 1, "title": "先观察", "content": "查看匹配前后的栈。"},
                {"level": 2, "title": "再推理", "content": "已匹配元素不应继续留在栈中。"},
                {"level": 3, "title": "修改方向", "content": "在匹配成功分支更新栈。"},
            ],
            "fix_suggestion": "匹配成功后移除栈顶元素。",
            "verification": "使用输入 ()，最终栈应为空。",
            "confidence": "high",
        },
        ensure_ascii=False,
    )
    result = _parse_trace_bug_diagnosis(raw, max_step=0, steps=steps)
    assert result["bug_step_index"] == 0
    assert result["actual_state"] == "st=['(']"
    assert len(result["hints"]) == 3
    assert result["confidence"] == "high"


def test_valid_parentheses_missing_pop_has_verified_rule_diagnosis():
    result = diagnose_known_error_pattern(
        slug="valid-parentheses",
        user_code="for (char c : s) { st.push(c); char top = st.top(); }",
        trace_steps=[
            {
                "line": 16,
                "changed": ["c"],
                "vars": {
                    "c": {"type": "str", "value": ")"},
                    "st": {"type": "stack", "value": ["("]},
                },
            }
        ],
    )
    assert result is not None
    assert result["source"] == "rule:valid_parentheses_missing_pop"
    assert "没有弹出" in result["diagnosis_title"]
    assert result["confidence"] == "high"
    assert len(result["hints"]) == 3
