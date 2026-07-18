"""Deterministic OJ diagnosis rules for stable production fallback."""

from __future__ import annotations

import ast
import re
from typing import Any


def _attribute_owner_name(node: ast.AST) -> str:
    if isinstance(node, ast.Attribute) and node.attr == "next" and isinstance(node.value, ast.Name):
        return node.value.id
    return ""


def _find_reverse_list_save_order_bug(user_code: str) -> dict[str, Any] | None:
    try:
        tree = ast.parse(user_code)
    except SyntaxError:
        return None

    for node in ast.walk(tree):
        if not isinstance(node, ast.While):
            continue
        overwrite: tuple[int, str] | None = None
        for statement in node.body:
            if isinstance(statement, ast.Assign):
                overwritten_here = False
                for target in statement.targets:
                    owner = _attribute_owner_name(target)
                    if owner:
                        overwrite = (statement.lineno, owner)
                        overwritten_here = True
                        break
                if overwritten_here:
                    continue

                if (
                    overwrite is not None
                    and len(statement.targets) == 1
                    and isinstance(statement.targets[0], ast.Name)
                ):
                    next_owner = _attribute_owner_name(statement.value)
                    if next_owner and next_owner == overwrite[1]:
                        return {
                            "overwrite_line": overwrite[0],
                            "save_line": statement.lineno,
                            "current_name": overwrite[1],
                            "next_name": statement.targets[0].id,
                        }
    return None


def _node_ref_brief(snapshot: dict[str, Any] | None) -> str:
    if not snapshot:
        return "未捕获"
    value = snapshot.get("value")
    if snapshot.get("type") != "node_ref" or not isinstance(value, dict):
        return str(value)
    node_id = value.get("node")
    if node_id is None:
        return "null"
    nodes = value.get("nodes") or {}
    node = nodes.get(node_id) if isinstance(nodes, dict) else None
    if isinstance(node, dict) and "val" in node:
        return f"{node_id}(值={node['val']})"
    return str(node_id)


def _find_trace_step(
    trace_steps: list[dict[str, Any]],
    *,
    save_line: int,
    next_name: str,
) -> int:
    candidates = [
        i
        for i, step in enumerate(trace_steps)
        if int(step.get("line") or 0) == save_line
    ]
    for i in candidates:
        step = trace_steps[i]
        if next_name in (step.get("changed") or []) or next_name in (step.get("vars") or {}):
            return i
    if candidates:
        return candidates[0]
    for i, step in enumerate(trace_steps):
        if int(step.get("line") or 0) >= save_line:
            return i
    return max(0, len(trace_steps) - 1)


def diagnose_known_error_pattern(
    *,
    slug: str,
    user_code: str,
    trace_steps: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Return a high-quality rule diagnosis for a known, narrowly matched bug."""
    if slug == "valid-parentheses":
        compact = re.sub(r"\s+", "", user_code)
        has_push = any(token in compact for token in (".push(", ".append("))
        has_pop = ".pop(" in compact
        if has_push and not has_pop:
            bug_step_index = 0
            closing_candidates: list[int] = []
            for i, step in enumerate(trace_steps):
                vars_map = step.get("vars") or {}
                c_snap = vars_map.get("c") or vars_map.get("ch") or {}
                c_text = str(c_snap.get("value") if isinstance(c_snap, dict) else c_snap)
                if any(mark in c_text for mark in (")", "]", "}")):
                    closing_candidates.append(i)
                    if "top" in vars_map:
                        bug_step_index = i
                        break
            else:
                if closing_candidates:
                    bug_step_index = closing_candidates[0]
            step = trace_steps[bug_step_index]
            line = int(step.get("line") or 0)
            vars_map = step.get("vars") or {}
            stack_name = next((name for name in ("st", "stack", "stk") if name in vars_map), "st")
            stack_value = str((vars_map.get(stack_name) or {}).get("value", "未捕获"))
            return {
                "bug_step_index": bug_step_index,
                "diagnosis_title": "右括号匹配成功后，栈顶左括号没有弹出",
                "detailed_analysis": (
                    f"Step {bug_step_index + 1}（代码第 {line} 行附近）处理右括号时，"
                    f"{stack_name} 仍为 {stack_value}。代码只读取并比较栈顶，却没有在匹配成功后移除它。"
                    "括号匹配的不变量是：栈中只保留尚未匹配的左括号；因此已匹配元素持续残留，"
                    "最终栈非空，合法的非空括号串也会输出 false。"
                ),
                "actual_state": f"匹配检查完成后，{stack_name} 仍保留已匹配的左括号：{stack_value}",
                "expected_state": f"匹配成功后应移除 {stack_name} 的栈顶，只留下尚未匹配的左括号",
                "invariant": "每处理完一个匹配的右括号，栈中只保留尚未匹配的左括号",
                "observation_question": "右括号与栈顶匹配成功后，栈的大小有没有减少？",
                "hints": [
                    {"level": 1, "title": "先观察", "content": "对比右括号处理前后的栈内容和大小。"},
                    {"level": 2, "title": "再推理", "content": "已经配对的左括号不应继续留在“尚未匹配”的栈中。"},
                    {"level": 3, "title": "修改方向", "content": "在确认括号类型匹配之后，补上一次栈顶移除操作。"},
                ],
                "fix_suggestion": "在不匹配判断通过之后移除栈顶元素，再继续处理下一个字符。",
                "verification": "使用最小输入 () 重跑；处理右括号后栈应为空，最终输出 true。",
                "confidence": "high",
                "error_type": "state_transition_error",
                "error_type_label": "栈状态更新遗漏",
                "why_failed": "已匹配左括号未出栈，最终非空检查失败。",
                "recommended_knowledge_points": ["栈的 LIFO 语义", "括号匹配循环不变量"],
                "source": "rule:valid_parentheses_missing_pop",
            }
        return None

    if slug != "reverse-linked-list":
        return None
    match = _find_reverse_list_save_order_bug(user_code)
    if not match or not trace_steps:
        return None

    bug_step_index = _find_trace_step(
        trace_steps,
        save_line=int(match["save_line"]),
        next_name=str(match["next_name"]),
    )
    step = trace_steps[bug_step_index]
    vars_map = step.get("vars") or {}
    current_name = str(match["current_name"])
    next_name = str(match["next_name"])
    current_value = _node_ref_brief(vars_map.get(current_name))
    next_value = _node_ref_brief(vars_map.get(next_name))
    overwrite_line = int(match["overwrite_line"])
    save_line = int(match["save_line"])

    return {
        "bug_step_index": bug_step_index,
        "diagnosis_title": "后继指针保存过晚，首轮反转后链表断开",
        "detailed_analysis": (
            f"Step {bug_step_index + 1}（代码第 {save_line} 行）显示 "
            f"{current_name}={current_value}，但 {next_name}={next_value}。"
            f"第 {overwrite_line} 行已经把 {current_name}.next 改为 prev，随后才读取 "
            f"{next_name}={current_name}.next，保存到的已不是原后继。"
            f"因此 curr 很快变为 null，后续节点失去入口，输出只保留首节点，导致 WA。"
        ),
        "error_type": "pointer_update_error",
        "error_type_label": "指针更新顺序错误",
        "why_failed": (
            "原链表后继在保存前被覆盖，循环提前结束；样例期望完整逆序，实际仅输出首节点，"
            "输出与标准答案不一致，因此判为 WA。"
        ),
        "fix_suggestion": (
            f"先执行 {next_name} = {current_name}.next 保存原后继，再令 "
            f"{current_name}.next = prev，最后依次推进 prev 与 {current_name}。"
        ),
        "recommended_knowledge_points": [
            "链表反转的三指针循环不变量",
            "next 指针的保存与更新顺序",
            "断链风险与单节点边界",
        ],
        "intervention_suggestion": (
            "本次失败已生成学习干预：建议在当前路径插入“链表指针更新巩固”，"
            "完成指针更新动画、边界条件练习与错题复盘卡；连续受挫达到阈值后由 "
            "PlannerAgent 自动重排路径。"
        ),
        "variable_evidence": [
            f"{current_name}: {current_value}",
            f"{next_name}: {next_value}",
            "prev: 已接管当前节点，但原后继已无法继续访问",
        ],
        "source": "rule:reverse_linked_list_save_order",
    }
