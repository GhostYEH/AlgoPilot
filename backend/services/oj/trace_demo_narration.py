"""确定性固定旁白：按题号 slug 预置，并在无 LLM 时由规则生成。"""

from __future__ import annotations

import re
from typing import Any

# slug 别名 → 演示配置 profile
_SLUG_PROFILES: dict[str, str] = {
    "reverse-linked-list": "linked_list",
    "reverse-linked-list-ii": "linked_list",
    "unique-paths": "dp_matrix",
    "unique-paths-ii": "dp_matrix",
    "minimum-path-sum": "dp_matrix",
    "climbing-stairs": "dp_1d",
}

_PROFILE_BY_KEYWORD: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"reverse\s*list|反转链表", re.I), "linked_list"),
    (re.compile(r"unique\s*paths?|不同路径|唯一路径", re.I), "dp_matrix"),
    (re.compile(r"uniquePaths|minPathSum|路径", re.I), "dp_matrix"),
]


def resolve_demo_profile(slug: str, user_code: str) -> str | None:
    s = (slug or "").strip().lower()
    if s in _SLUG_PROFILES:
        return _SLUG_PROFILES[s]
    for key, prof in _SLUG_PROFILES.items():
        if key in s or s in key:
            return prof
    code = user_code or ""
    for pat, prof in _PROFILE_BY_KEYWORD:
        if pat.search(code):
            return prof
    return None


def _scalar(vars_map: dict, *names: str) -> int | None:
    for n in names:
        snap = vars_map.get(n) or {}
        if snap.get("type") == "int" and isinstance(snap.get("value"), int):
            return int(snap["value"])
    return None


def _node_ref(vars_map: dict, *names: str) -> str | None:
    for name in names:
        snap = vars_map.get(name) or {}
        if snap.get("type") != "node_ref":
            continue
        value = snap.get("value") or {}
        node_id = value.get("node") if isinstance(value, dict) else None
        return str(node_id) if node_id is not None else None
    return None


def _matrix_cell(vars_map: dict, name: str, r: int, c: int) -> Any:
    snap = vars_map.get(name) or {}
    if snap.get("type") != "matrix":
        return None
    val = snap.get("value") or {}
    cells = val.get("cells") or []
    try:
        return cells[r][c]
    except (IndexError, TypeError):
        return None


def _demo_linked_list(steps: list[dict[str, Any]]) -> list[dict[str, int | str]]:
    out: list[dict[str, int | str]] = []
    for i, s in enumerate(steps):
        ch = s.get("changed") or []
        if not ch and i > 0:
            continue
        line = s.get("line", 0)
        vars_map = s.get("vars") or {}
        parts: list[str] = []
        if "prev" in ch and _scalar(vars_map, "prev") is None:
            parts.append("prev 置为空，准备反转")
        if "curr" in ch:
            parts.append("curr 指向当前待处理节点")
        if "nxt" in ch or "next" in ch:
            current_ref = _node_ref(vars_map, "curr", "current")
            next_ref = _node_ref(vars_map, "nxt", "next")
            if current_ref is not None and next_ref is None:
                parts.append("nxt 变为 null：后继指针保存过晚，原链表已断开")
            else:
                parts.append("用 nxt 保存原后继，避免反转后断链")
        if any("next" in x for x in ch) or "curr" in ch and "prev" in ch:
            parts.append("把 curr.next 改指向前驱，完成局部反转")
        if "prev" in ch and "curr" in ch and _scalar(vars_map, "curr") is None:
            parts.append("循环结束，prev 即为新链表头")
        if not parts:
            parts.append(f"更新 {', '.join(ch[:4])}")
        out.append({"step_index": i, "text": f"第 {line} 行：{'；'.join(parts)}"[:220]})
    return out


def _demo_dp_matrix(steps: list[dict[str, Any]]) -> list[dict[str, int | str]]:
    out: list[dict[str, int | str]] = []
    dp_names = ("dp", "f", "grid", "memo")

    for i, s in enumerate(steps):
        ch = s.get("changed") or []
        if not ch and i > 0:
            continue
        line = s.get("line", 0)
        vars_map = s.get("vars") or {}
        dp_name = next((n for n in dp_names if n in vars_map or n in ch), "dp")
        r = _scalar(vars_map, "i", "r", "row")
        c = _scalar(vars_map, "j", "c", "col")
        text = ""

        if dp_name in ch and r is not None and c is not None:
            cur_v = _matrix_cell(vars_map, dp_name, r, c)
            up = _matrix_cell(vars_map, dp_name, r - 1, c) if r > 0 else None
            left = _matrix_cell(vars_map, dp_name, r, c - 1) if c > 0 else None
            if r == 0 and c == 0:
                text = f"初始化 {dp_name}[0][0]，起点只有 1 种走法"
            elif r == 0:
                text = f"首行 {dp_name}[0][{c}]：只能一直向右，等于左邻 {left}"
            elif c == 0:
                text = f"首列 {dp_name}[{r}][0]：只能一直向下，等于上邻 {up}"
            else:
                text = (
                    f"填 {dp_name}[{r}][{c}]：只能从上方或左方来，"
                    f"路径数 = 上 {up} + 左 {left} = {cur_v}"
                )
        elif dp_name in ch:
            text = f"更新二维 DP 表 {dp_name} 的单元格"
        elif r is not None and c is not None:
            text = f"移动下标到 ({r},{c})，准备计算该格"
        else:
            text = f"DP 步骤：{', '.join(ch[:4])}"

        out.append({"step_index": i, "text": f"第 {line} 行：{text}"[:220]})

    return out


def _demo_dp_1d(steps: list[dict[str, Any]]) -> list[dict[str, int | str]]:
    out: list[dict[str, int | str]] = []
    for i, s in enumerate(steps):
        ch = s.get("changed") or []
        if not ch and i > 0:
            continue
        line = s.get("line", 0)
        vars_map = s.get("vars") or {}
        idx = _scalar(vars_map, "i", "n")
        if "dp" in ch:
            text = f"更新 dp[{idx if idx is not None else '?'}]（一维递推）"
        else:
            text = f"递推：{', '.join(ch[:4])}"
        out.append({"step_index": i, "text": f"第 {line} 行：{text}"[:220]})
    return out


_GENERATORS = {
    "linked_list": _demo_linked_list,
    "dp_matrix": _demo_dp_matrix,
    "dp_1d": _demo_dp_1d,
}


def generate_demo_narration(
    slug: str,
    user_code: str,
    steps: list[dict[str, Any]],
) -> list[dict[str, int | str]] | None:
    """
    若命中预置/规则 profile 则返回旁白列表；否则返回 None（走 LLM）。
    """
    if not steps:
        return []
    profile = resolve_demo_profile(slug, user_code)
    if not profile:
        return None
    gen = _GENERATORS.get(profile)
    if not gen:
        return None
    lines = gen(steps)
    return lines if lines else None


def demo_narration_enabled(slug: str, user_code: str, *, force: bool = False) -> bool:
    """是否应优先使用演示旁白（force 或已注册 slug/profile）。"""
    if force:
        return resolve_demo_profile(slug, user_code) is not None
    return resolve_demo_profile(slug, user_code) is not None
