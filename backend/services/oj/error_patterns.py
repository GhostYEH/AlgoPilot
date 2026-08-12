"""OJ 错因类型枚举与规则分类。"""

from __future__ import annotations

import re
from typing import Literal

ErrorType = Literal[
    "boundary_condition_error",
    "initialization_error",
    "loop_condition_error",
    "pointer_update_error",
    "recursion_base_case_error",
    "state_transition_error",
    "data_structure_misuse",
    "time_complexity_issue",
    "unknown",
]

ERROR_TYPE_LABELS: dict[str, str] = {
    "boundary_condition_error": "边界条件错误",
    "initialization_error": "初始化错误",
    "loop_condition_error": "循环条件错误",
    "pointer_update_error": "指针更新错误",
    "recursion_base_case_error": "递归基线错误",
    "state_transition_error": "状态转移错误",
    "data_structure_misuse": "数据结构误用",
    "time_complexity_issue": "时间复杂度问题",
    "unknown": "未分类逻辑错误",
}


def classify_error_type(
    *,
    slug: str = "",
    title: str = "",
    analysis: str = "",
    trace_summary: str = "",
    edge_category: str = "",
    verdict: str = "",
    code: str = "",
) -> ErrorType:
    text = f"{slug} {title} {analysis} {trace_summary} {edge_category} {code}".lower()
    v = (verdict or "").upper()

    if v == "TLE" or "超时" in text or "死循环" in text or "复杂度" in text:
        if "pointer" in text and "停滞" in text:
            return "loop_condition_error"
        return "time_complexity_issue"

    if any(k in text for k in ("递归", "recursion", "栈溢出", "stack overflow", "base case", "基线", "终止条件")):
        return "recursion_base_case_error"

    if any(
        k in text
        for k in (
            "next",
            "指针",
            "pointer",
            "prev",
            "head",
            "断链",
            "链表",
            "linked",
            "curr",
            "dummy",
        )
    ) and any(k in text for k in ("移动", "更新", "反转", "reverse", "未移动", "停滞", "null")):
        return "pointer_update_error"

    if any(k in text for k in ("初始化", "init", "dp[0]", "边界", "空数组", "empty", "边界条件", "下标 0")):
        if "dp" in text or "状态" in text or "转移" in slug or "climb" in slug or "path" in slug:
            return "initialization_error"
        return "boundary_condition_error"

    if any(k in text for k in ("边界", "boundary", "edge", "空输入", "零长度", "n=0", "越界", "overflow")):
        return "boundary_condition_error"

    if any(k in text for k in ("转移", "transition", "状态", "dp[", "方程", "递推")):
        return "state_transition_error"

    if any(k in text for k in ("while", "for ", "循环", "loop", "未推进", "窗口", "left", "right")):
        if "停滞" in text or "未移动" in text or "未收缩" in text:
            return "loop_condition_error"

    if any(k in text for k in ("栈", "队列", "stack", "queue", "哈希", "hash", "树", "tree")):
        if "误用" in text or "错用" in text:
            return "data_structure_misuse"

    if re.search(r"dp|动态规划|背包|climbing|unique.*path", slug + title, re.I):
        if any(k in text for k in ("初始化", "边界", "dp[0]", "首行", "首列")):
            return "initialization_error"
        return "state_transition_error"

    if re.search(r"list|linked|node|reverse", slug + title, re.I):
        return "pointer_update_error"

    return "unknown"
