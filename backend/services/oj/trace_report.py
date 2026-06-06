from __future__ import annotations

import json
from typing import Any

from core.config import settings
from schemas.oj import (
    TraceDiagnosisReport,
    TraceStepBrief,
    VarChangeItem,
)
from services.llm import chat_completion
from services.oj.ai_diagnosis import (
    _fallback_trace_bug_diagnosis,
    _format_snap_brief,
    compress_trace_steps_to_text,
)

TRACE_REPORT_SYSTEM = """你是算法调试教练。根据学生代码、执行轨迹和判题结果，生成结构化诊断报告。

严格只输出 JSON 对象，不要 markdown：
{
  "possible_cause": "<50~150字中文，说明最可能的错误原因>",
  "fix_suggestion": "<50~120字中文，给出具体修复方向，不要给完整代码>"
}"""


def _build_key_variable_changes(
    steps: list[dict[str, Any]],
    bug_step_index: int,
    max_items: int = 6,
) -> list[VarChangeItem]:
    out: list[VarChangeItem] = []
    start = max(0, bug_step_index - 3)
    end = min(len(steps), bug_step_index + 2)
    for i in range(start, end):
        s = steps[i]
        changed = s.get("changed") or []
        vars_dict = s.get("vars") or {}
        prev_vars = (steps[i - 1].get("vars") or {}) if i > 0 else {}
        for k in changed[:4]:
            before_snap = prev_vars.get(k) if isinstance(prev_vars, dict) else None
            after_snap = vars_dict.get(k) if isinstance(vars_dict, dict) else None
            out.append(
                VarChangeItem(
                    step_index=i,
                    line=int(s.get("line", 0)),
                    variable_name=k,
                    before=_format_snap_brief(before_snap) if before_snap else "—",
                    after=_format_snap_brief(after_snap) if after_snap else "?",
                )
            )
        if len(out) >= max_items:
            break
    return out[:max_items]


def _build_trace_steps_brief(
    steps: list[dict[str, Any]],
    bug_step_index: int,
    max_steps: int = 30,
) -> list[TraceStepBrief]:
    out: list[TraceStepBrief] = []
    step_n = 0
    for i, s in enumerate(steps):
        changed = s.get("changed") or []
        if not changed and i > 0:
            continue
        vars_dict = s.get("vars") or {}
        var_summary: dict[str, str] = {}
        for k in changed[:6]:
            snap = vars_dict.get(k) if isinstance(vars_dict, dict) else None
            var_summary[k] = _format_snap_brief(snap) if snap else "?"
        out.append(
            TraceStepBrief(
                step_index=i,
                line=int(s.get("line", 0)),
                changed_vars=list(changed[:6]),
                var_summary=var_summary,
                is_error_step=(i == bug_step_index),
            )
        )
        step_n += 1
        if step_n >= max_steps:
            break
    return out


def _build_failed_test_point(
    judge_verdict: str,
    failed_cases: list[dict[str, Any]],
) -> str:
    if failed_cases:
        c = failed_cases[0]
        idx = c.get("index", 0)
        msg = c.get("message", "")
        inp = c.get("input_preview", "")
        parts = [f"用例 {idx + 1}"]
        if inp:
            parts.append(f"输入: {inp[:80]}")
        if msg:
            parts.append(msg[:100])
        return " · ".join(parts)
    verdict_map = {"WA": "答案错误", "TLE": "超时", "RE": "运行错误", "CE": "编译错误"}
    return verdict_map.get(judge_verdict, judge_verdict or "未通过")


def _fallback_cause_and_fix(
    judge_verdict: str,
    bug_step_index: int,
    steps: list[dict[str, Any]],
    compressed_lines: list[str],
) -> tuple[str, str]:
    if judge_verdict == "TLE":
        return (
            "代码在给定输入规模下超时，常见于嵌套循环未优化或存在死循环。",
            "尝试减少循环嵌套层数，或使用哈希表/双指针替代暴力搜索。",
        )
    if judge_verdict == "RE":
        return (
            "运行时发生异常，常见于数组越界、空指针引用或递归栈溢出。",
            "检查数组下标范围、空值判断，以及递归终止条件。",
        )
    if judge_verdict == "CE":
        return ("编译错误：代码存在语法问题，无法执行。", "根据编译错误信息修复语法问题后重新提交。")

    if bug_step_index < len(steps):
        s = steps[bug_step_index]
        changed = s.get("changed") or []
        line = s.get("line", "?")
        pointer_keys = {"left", "right", "l", "r", "i", "j", "slow", "fast", "curr", "prev"}
        for k in changed:
            if k in pointer_keys:
                return (
                    f"第 {line} 步（Step {bug_step_index}）起变量 {k} 未按预期推进，"
                    f"可能导致逻辑偏差或漏解。",
                    f"检查 {k} 的更新条件是否正确，确保循环不变量在每步保持。",
                )
        if changed:
            return (
                f"第 {line} 步（Step {bug_step_index}）处 "
                f"{'、'.join(changed[:4])} 状态异常，与题目要求不一致。",
                "对照题目不变量，检查该步的赋值或判断逻辑。",
            )

    return (
        f"在 {len(compressed_lines)} 个有效执行步中检测到逻辑偏差。",
        "建议使用可视化调试逐步检查变量变化，对照题目要求定位错误。",
    )


def _build_demo_trace_steps(code: str) -> list[dict[str, Any]]:
    lines = code.strip().splitlines()
    steps: list[dict[str, Any]] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("class ") or stripped.startswith("def "):
            continue
        if "pass" in stripped:
            steps.append({"line": i + 1, "vars": {}, "changed": []})
            continue
        if "=" in stripped and "==" not in stripped:
            var_name = stripped.split("=")[0].strip().split()[-1]
            steps.append(
                {
                    "line": i + 1,
                    "vars": {var_name: {"type": "str", "value": "(执行中)"}},
                    "changed": [var_name],
                }
            )
        elif "return" in stripped:
            steps.append({"line": i + 1, "vars": {}, "changed": ["return"]})
        elif "if" in stripped or "for" in stripped or "while" in stripped:
            steps.append({"line": i + 1, "vars": {}, "changed": []})
    if not steps:
        steps = [{"line": 1, "vars": {}, "changed": []}]
    return steps


def generate_trace_diagnosis_report(
    *,
    user_code: str,
    judge_verdict: str,
    failed_cases: list[dict[str, Any]],
    trace_steps: list[dict[str, Any]],
    bug_step_index: int,
    diagnosis_title: str,
    detailed_analysis: str,
    problem: dict[str, Any],
    slug: str,
    tutoring=None,
    source: str = "fallback",
) -> TraceDiagnosisReport:
    failed_test_point = _build_failed_test_point(judge_verdict, failed_cases)
    key_var_changes = _build_key_variable_changes(trace_steps, bug_step_index)
    error_step_brief = None
    if bug_step_index < len(trace_steps):
        s = trace_steps[bug_step_index]
        changed = s.get("changed") or []
        vars_dict = s.get("vars") or {}
        var_summary = {}
        for k in changed[:6]:
            snap = vars_dict.get(k) if isinstance(vars_dict, dict) else None
            var_summary[k] = _format_snap_brief(snap) if snap else "?"
        error_step_brief = TraceStepBrief(
            step_index=bug_step_index,
            line=int(s.get("line", 0)),
            changed_vars=list(changed[:6]),
            var_summary=var_summary,
            is_error_step=True,
        )
    trace_steps_brief = _build_trace_steps_brief(trace_steps, bug_step_index)

    compressed_lines, _ = compress_trace_steps_to_text(trace_steps)
    possible_cause = ""
    fix_suggestion = ""

    if source == "llm" and detailed_analysis:
        possible_cause = detailed_analysis[:300]
        fix_suggestion = diagnosis_title[:200]
    else:
        possible_cause, fix_suggestion = _fallback_cause_and_fix(
            judge_verdict, bug_step_index, trace_steps, compressed_lines
        )

    recommended_resources = []
    if tutoring and tutoring.recommended_resources:
        recommended_resources = tutoring.recommended_resources

    path_rearrange_triggered = False
    if tutoring and tutoring.path_adjustment_hint:
        path_rearrange_triggered = "巩固" in tutoring.path_adjustment_hint or "插入" in tutoring.path_adjustment_hint

    return TraceDiagnosisReport(
        error_type=judge_verdict or "WA",
        failed_test_point=failed_test_point,
        key_variable_changes=key_var_changes,
        error_step=error_step_brief,
        possible_cause=possible_cause,
        fix_suggestion=fix_suggestion,
        recommended_resources=recommended_resources,
        path_rearrange_triggered=path_rearrange_triggered,
        trace_steps=trace_steps_brief,
        source=source,
        tutoring=tutoring,
    )


async def generate_llm_cause_and_fix(
    user_code: str,
    steps: list[dict[str, Any]],
    judge_verdict: str,
    bug_step_index: int,
) -> tuple[str, str]:
    if not settings.llm_configured:
        return "", ""
    compressed, _ = compress_trace_steps_to_text(steps)
    bug_line = steps[bug_step_index].get("line", "?") if bug_step_index < len(steps) else "?"
    user_body = (
        f"## 判题结果：{judge_verdict}\n"
        f"## Bug 起源步：Step {bug_step_index}（代码第 {bug_line} 行）\n\n"
        f"## 学生代码\n```\n{user_code[:3000]}\n```\n\n"
        f"## 压缩轨迹（仅含 changed≠∅ 的步）\n"
        + "\n".join(compressed[:60])
    )
    try:
        raw = await chat_completion(
            [
                {"role": "system", "content": TRACE_REPORT_SYSTEM},
                {"role": "user", "content": user_body},
            ],
            temperature=0.3,
            max_tokens=500,
        )
        text = raw.strip()
        fence = __import__("re").search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence:
            text = fence.group(1).strip()
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
        parsed = json.loads(text)
        return (
            str(parsed.get("possible_cause", ""))[:300],
            str(parsed.get("fix_suggestion", ""))[:200],
        )
    except Exception:
        return "", ""
