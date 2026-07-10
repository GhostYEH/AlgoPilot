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
    context_items: list[VarChangeItem] = []
    bug_items: list[VarChangeItem] = []
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
            item = VarChangeItem(
                step_index=i,
                line=int(s.get("line", 0)),
                variable_name=k,
                before=_format_snap_brief(before_snap) if before_snap else "—",
                after=_format_snap_brief(after_snap) if after_snap else "?",
            )
            if i == bug_step_index:
                bug_items.append(item)
            else:
                context_items.append(item)

    # 错误步骤的变量证据必须保留，不能被前置上下文挤出报告。
    kept_context = context_items[: max(0, max_items - len(bug_items))]
    return sorted(
        [*kept_context, *bug_items[:max_items]],
        key=lambda item: (item.step_index, item.variable_name),
    )


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
                    f"轨迹在 Step {bug_step_index + 1}（代码第 {line} 行）记录到变量 {k} 更新。"
                    "仅凭该次状态变化还不能证明它就是根因，需要结合失败输入与题目不变量核对"
                    f" {k} 的期望值和实际值。",
                    f"在代码第 {line} 行前后增加边界输入的逐步核对，确认 {k} 每次更新后的值"
                    "是否满足题目不变量；证据不足时不要直接改动无关逻辑。",
                )
        if changed:
            var_list = "、".join(changed[:4])
            return (
                f"轨迹在 Step {bug_step_index + 1}（代码第 {line} 行）记录到 "
                f"{var_list} 发生变化，但当前规则无法从轨迹本身推导出唯一的正确期望值，"
                "因此不能把该步直接判定为确定根因。",
                f"使用报告中的失败用例，在代码第 {line} 行核对 {var_list} 的实际值与手算期望值；"
                "确认首次偏离后再修改对应赋值或分支条件。",
            )

    return (
        f"当前仅获得 {len(compressed_lines)} 个有效执行步，尚不足以从规则中唯一确定根因。"
        "报告保留失败用例和轨迹事实，但不会把任意中间步骤描述为已证实错误。",
        "先用最小失败用例手算期望状态，再逐步对照 Trace；优先检查首次出现差异的"
        "循环边界、指针更新或状态转移。",
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
    trace_case_reproduced: bool = False,
    trace_case_verdict: str = "",
    trace_case_message: str = "",
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
    resolved_fix_suggestion = fix_suggestion
    error_category = ""
    error_category_label = ""
    why_failed = ""
    recommended_knowledge_points: list[str] = []
    intervention_suggestion = ""

    if known:
        possible_cause = str(known["detailed_analysis"])
        resolved_fix_suggestion = str(known["fix_suggestion"])
        error_category = str(known["error_type"])
        error_category_label = str(known["error_type_label"])
        why_failed = str(known["why_failed"])
        recommended_knowledge_points = list(known["recommended_knowledge_points"])
        intervention_suggestion = str(known["intervention_suggestion"])
    elif source == "llm" and detailed_analysis:
        possible_cause = detailed_analysis[:400]
        # 优先使用外部传入的 LLM 生成结果。
        if not resolved_fix_suggestion:
            resolved_fix_suggestion = diagnosis_title[:200]
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
        if not resolved_fix_suggestion:
            resolved_fix_suggestion = fallback_fix

    recommended_resources = []
    if tutoring and tutoring.recommended_resources:
        recommended_resources = tutoring.recommended_resources

    path_adjustment_hint = (
        tutoring.path_adjustment_hint if tutoring and tutoring.path_adjustment_hint else ""
    )
    combined_intervention = " ".join(
        part for part in (intervention_suggestion, path_adjustment_hint) if part
    )

    path_rearrange_triggered = bool(
        path_adjustment_hint
        and any(
            keyword in path_adjustment_hint
            for keyword in ("巩固", "插入", "前置", "重排")
        )
    )
    if source.startswith("rule:"):
        diagnosis_confidence = "high" if trace_case_reproduced else "medium"
    elif source == "llm":
        diagnosis_confidence = "medium" if trace_case_reproduced else "low"
    else:
        diagnosis_confidence = "low"

    if trace_case_reproduced:
        evidence_summary = (
            f"服务端已重新执行目标失败用例并复现 {trace_case_verdict or judge_verdict}。"
            "报告中的代码行、变量变化和执行步骤来自该次真实 Trace。"
        )
    else:
        detail = trace_case_message[:120] if trace_case_message else "目标失败未在诊断阶段稳定复现"
        evidence_summary = (
            f"{detail}。当前报告仅提供静态或规则线索，不应把“可能原因”视为已证实根因。"
        )

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
        fix_suggestion=resolved_fix_suggestion,
        recommended_knowledge_points=recommended_knowledge_points,
        intervention_suggestion=combined_intervention,
        learning_intervention_generated=bool(
            combined_intervention
            or (tutoring and tutoring.recommended_resources)
        ),
        recommended_resources=recommended_resources,
        path_rearrange_triggered=path_rearrange_triggered,
        trace_steps=trace_steps_brief,
        source=source,
        diagnosis_confidence=diagnosis_confidence,
        evidence_summary=evidence_summary,
        trace_case_reproduced=trace_case_reproduced,
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
        f"## 题目描述\n{problem_description[:2000] or '（无描述）'}\n\n"
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
        cause = str(parsed.get("possible_cause", ""))[:300]
        fix = str(parsed.get("fix_suggestion", ""))[:200]
        evidence_text = f"{cause} {fix}"
        from services.oj.ai_diagnosis import _mentions_code_line

        if not _mentions_code_line(evidence_text, bug_line):
            return "", ""
        if bug_changed and not any(str(name) in evidence_text for name in bug_changed):
            return "", ""
        return cause, fix
    except Exception:
        return "", ""
