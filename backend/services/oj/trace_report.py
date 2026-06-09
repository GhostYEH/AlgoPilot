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
    _format_snap_brief,
    compress_trace_steps_to_text,
)
from services.oj.rule_diagnosis import diagnose_known_error_pattern

TRACE_REPORT_SYSTEM = """你是算法调试教练。根据学生代码、执行轨迹、判题结果和 bug 起源步，生成结构化诊断报告。

分析要求：
1. possible_cause：必须引用**具体的代码行号和变量名**，说明该步变量应有值与实际值
2. fix_suggestion：给出**具体的修复方向**（如"将第5行的 < 改为 <="），不要给完整代码

严格只输出 JSON 对象，不要 markdown：
{
  "possible_cause": "<80~200字中文，必须包含：①出错代码行号 ②关键变量应有值vs实际值 ③违反的不变量>",
  "fix_suggestion": "<60~150字中文，给出具体修复方向，如修改哪行、改哪个条件、加什么判断>"
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
            "代码在给定输入规模下超时，常见于嵌套循环未优化或存在死循环。"
            "请检查内层循环是否可以用哈希表或双指针替代，以及循环终止条件是否正确更新。",
            "尝试减少循环嵌套层数，或使用哈希表/双指针替代暴力搜索；"
            "若为递归，检查是否有重复子问题可记忆化。",
        )
    if judge_verdict == "RE":
        return (
            "运行时发生异常，常见于数组越界、空指针引用或递归栈溢出。"
            "请检查数组下标是否可能为负或超出范围，以及空值/None 判断是否遗漏。",
            "检查数组下标范围（特别是 n-1 vs n）、空值判断（if not x），以及递归终止条件。",
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
                    f"可能导致逻辑偏差或漏解。"
                    f"请检查 {k} 的更新条件是否在正确的分支中执行，以及循环不变量是否保持。",
                    f"检查 {k} 的更新条件是否正确（如 while 循环中是否遗漏了 {k} 的递增），"
                    f"确保循环不变量在每步保持。",
                )
        if changed:
            var_list = "、".join(changed[:4])
            return (
                f"第 {line} 步（Step {bug_step_index}）处 "
                f"{var_list} 状态异常，与题目要求不一致。"
                f"请对照题目不变量，检查该步的赋值或判断逻辑。",
                f"对照题目不变量，检查第 {line} 行 {var_list} 的赋值或判断逻辑是否正确。"
                f"建议用可视化调试逐步检查变量变化。",
            )

    return (
        f"在 {len(compressed_lines)} 个有效执行步中检测到逻辑偏差。"
        f"请使用可视化调试逐步检查变量变化，对照题目要求定位错误。",
        "建议使用可视化调试逐步检查变量变化，对照题目要求定位错误。"
        "重点关注循环边界、指针更新和边界条件。",
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
    fix_suggestion: str = "",
) -> TraceDiagnosisReport:
    known = diagnose_known_error_pattern(
        slug=slug,
        user_code=user_code,
        trace_steps=trace_steps,
    )
    if known:
        source = str(known["source"])
        bug_step_index = int(known["bug_step_index"])

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
    error_category = ""
    error_category_label = ""
    why_failed = ""
    recommended_knowledge_points: list[str] = []
    intervention_suggestion = ""

    if known:
        possible_cause = str(known["detailed_analysis"])
        fix_suggestion = str(known["fix_suggestion"])
        error_category = str(known["error_type"])
        error_category_label = str(known["error_type_label"])
        why_failed = str(known["why_failed"])
        recommended_knowledge_points = list(known["recommended_knowledge_points"])
        intervention_suggestion = str(known["intervention_suggestion"])
    elif source == "llm" and detailed_analysis:
        possible_cause = detailed_analysis[:400]
        # fix_suggestion 优先使用外部传入的 LLM 生成结果
        if not fix_suggestion:
            fix_suggestion = diagnosis_title[:200]
        # 为 LLM 诊断生成 why_failed
        if bug_step_index < len(trace_steps):
            s = trace_steps[bug_step_index]
            ch = s.get("changed") or []
            line = s.get("line", "?")
            why_failed = (
                f"在 Step {bug_step_index}（代码第 {line} 行）处，"
                f"{'、'.join(ch[:4]) if ch else '程序状态'} 偏离预期，"
                f"导致最终输出与标准答案不一致，判为 {judge_verdict}。"
            )
        else:
            why_failed = possible_cause
    else:
        possible_cause, fallback_fix = _fallback_cause_and_fix(
            judge_verdict, bug_step_index, trace_steps, compressed_lines
        )
        if not fix_suggestion:
            fix_suggestion = fallback_fix

    recommended_resources = []
    if tutoring and tutoring.recommended_resources:
        recommended_resources = tutoring.recommended_resources

    path_rearrange_triggered = False
    if tutoring and tutoring.path_adjustment_hint:
        path_rearrange_triggered = "巩固" in tutoring.path_adjustment_hint or "插入" in tutoring.path_adjustment_hint

    return TraceDiagnosisReport(
        error_type=judge_verdict or "WA",
        error_category=error_category or (tutoring.error_pattern if tutoring else ""),
        error_category_label=error_category_label or (
            tutoring.error_pattern_label if tutoring else ""
        ),
        failed_test_point=failed_test_point,
        key_variable_changes=key_var_changes,
        error_step=error_step_brief,
        possible_cause=possible_cause,
        why_failed=why_failed or possible_cause,
        fix_suggestion=fix_suggestion,
        recommended_knowledge_points=recommended_knowledge_points,
        intervention_suggestion=intervention_suggestion or (
            tutoring.path_adjustment_hint if tutoring else ""
        ),
        learning_intervention_generated=bool(
            intervention_suggestion
            or (tutoring and (tutoring.recommended_resources or tutoring.path_adjustment_hint))
        ),
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
    *,
    problem_description: str = "",
    failed_cases: list[dict[str, Any]] | None = None,
) -> tuple[str, str]:
    if not settings.llm_configured:
        return "", ""
    compressed, _ = compress_trace_steps_to_text(steps)
    bug_line = steps[bug_step_index].get("line", "?") if bug_step_index < len(steps) else "?"
    bug_changed = []
    bug_vars = {}
    if bug_step_index < len(steps):
        bug_changed = steps[bug_step_index].get("changed") or []
        bug_vars = steps[bug_step_index].get("vars") or {}
    bug_var_summary = ", ".join(
        f"{k}={_format_snap_brief(bug_vars.get(k))}" for k in bug_changed[:6]
    ) if bug_changed else "无变量变化"

    failed_hint = ""
    if failed_cases:
        failed_hint = "\n\n## 失败用例\n" + "\n".join(
            f"- 用例 {c.get('index', '?')}: 输入 {str(c.get('input_preview', ''))[:80]} → {str(c.get('message', ''))[:60]}"
            for c in failed_cases[:3]
        )

    user_body = (
        f"## 判题结果：{judge_verdict}\n"
        f"## Bug 起源步：Step {bug_step_index}（代码第 {bug_line} 行）\n"
        f"## Bug 步变量变化：{bug_var_summary}\n\n"
        f"## 学生代码\n```\n{user_code[:3000]}\n```\n\n"
        f"## 压缩轨迹（仅含 changed≠∅ 的步）\n"
        + "\n".join(compressed[:60])
        + failed_hint
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
