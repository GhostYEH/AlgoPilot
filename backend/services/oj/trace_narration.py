"""批量生成可视化调试旁白（演示兜底 → 单次 LLM）。"""

from __future__ import annotations

import json
import re
from typing import Any

from core.config import settings
from services.llm import chat_completion
from services.oj.trace_demo_narration import generate_demo_narration

MAX_STEPS_IN_PROMPT = 80

REVERSE_LIST_SYSTEM = """你是一位耐心的计算机老师，正在为学生讲解「反转链表」的可视化调试回放。

你会收到若干执行步骤的紧凑描述（仅包含发生变化的步）。请为每一步写一句中文旁白（18~50字）：
- 说清指针如何移动（prev / curr / nxt）
- 若涉及 curr.next 改变，说明「断开了哪条链、改指向了谁」
- 不要照抄代码，不要输出 markdown

严格只输出 JSON 数组，每项格式：
{"step_index": <int>, "narration": "<一句话>"}"""

DP_MATRIX_SYSTEM = """你是一位耐心的计算机老师，正在讲解「二维 DP 填表」（如 62. 不同路径）。

输入中每步包含行号、changed、当前坐标 i/j、以及 dp 矩阵相关变化。
当 changed 包含 dp（或二维表）且存在坐标 i,j 时，请重点说明状态转移：
- 当前格 dp[i][j] 的值来自哪几个相邻格（上方、左方）
- 用白话解释「只能从右和下走来」的路径计数

每步一句中文（20~55字）。严格只输出 JSON 数组：
{"step_index": <int>, "narration": "<一句话>"}"""


def _node_label(snap: dict[str, Any]) -> str:
    t = snap.get("type")
    val = snap.get("value") or {}
    if t == "node_ref":
        return str(val.get("node") or "null")
    if t == "linked_list":
        return f"head={val.get('head')}"
    if t == "matrix" and isinstance(val, dict):
        return f"{val.get('rows')}x{val.get('cols')}"
    if t == "int":
        return str(val.get("value"))
    return str(t)


def _dp_coords(vars_map: dict[str, Any]) -> tuple[int | None, int | None]:
    for ri, ci in (("i", "j"), ("r", "c"), ("row", "col")):
        rs = vars_map.get(ri) or {}
        cs = vars_map.get(ci) or {}
        if rs.get("type") == "int" and cs.get("type") == "int":
            return int(rs["value"]), int(cs["value"])
    return None, None


def _matrix_at(vars_map: dict[str, Any], name: str, r: int, c: int) -> Any:
    snap = vars_map.get(name) or {}
    if snap.get("type") != "matrix":
        return None
    cells = (snap.get("value") or {}).get("cells") or []
    try:
        return cells[r][c]
    except (IndexError, TypeError):
        return None


def _format_dp_brief(step: dict[str, Any]) -> str:
    line = step.get("line")
    changed = step.get("changed") or []
    vars_map = step.get("vars") or {}
    i, j = _dp_coords(vars_map)
    parts = [f"Line {line}: changed={json.dumps(changed, ensure_ascii=False)}"]
    if i is not None and j is not None:
        parts.append(f"i={i}, j={j}")
    for name in ("dp", "f", "grid"):
        if name in vars_map or name in changed:
            parts.append(f"{name}={_node_label(vars_map.get(name) or {})}")
            if i is not None and j is not None and name in vars_map:
                v = _matrix_at(vars_map, name, i, j)
                up = _matrix_at(vars_map, name, i - 1, j) if i > 0 else None
                left = _matrix_at(vars_map, name, i, j - 1) if j > 0 else None
                parts.append(f"{name}[{i}][{j}]={v}, up={up}, left={left}")
    return "; ".join(parts)


def _format_ll_brief(step: dict[str, Any]) -> str:
    line = step.get("line")
    changed = step.get("changed") or []
    vars_map = step.get("vars") or {}
    parts = [f"Line {line}: changed: {json.dumps(changed, ensure_ascii=False)}"]
    for name in ("prev", "curr", "nxt", "next", "head"):
        if name in vars_map or name in changed:
            parts.append(f"{name}={_node_label(vars_map.get(name) or {})}")
    return "; ".join(parts)


def _detect_scene(user_code: str, steps: list[dict[str, Any]]) -> str:
    code = user_code.lower().replace(" ", "")
    if "reverselist" in code:
        return "linked_list"
    for s in steps[:24]:
        vm = s.get("vars") or {}
        if any(k in vm for k in ("prev", "curr", "nxt")):
            return "linked_list"
        if any((vm.get(n) or {}).get("type") == "matrix" for n in ("dp", "f", "grid")):
            if _dp_coords(vm)[0] is not None:
                return "dp_matrix"
    if "uniquepaths" in code or "minpathsum" in code:
        return "dp_matrix"
    return "generic"


def _condense_steps(steps: list[dict[str, Any]], scene: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, s in enumerate(steps[:MAX_STEPS_IN_PROMPT]):
        changed = s.get("changed") or []
        if not changed and i > 0:
            continue
        if scene == "dp_matrix":
            text_line = _format_dp_brief({**s, "vars": s.get("vars") or {}})
        elif scene == "linked_list":
            text_line = _format_ll_brief({**s, "vars": s.get("vars") or {}})
        else:
            text_line = f"Line {s.get('line')}: changed={changed}"
        out.append(
            {
                "step_index": i,
                "line": s.get("line"),
                "changed": changed,
                "text_line": text_line,
            }
        )
    return out


def _parse_narration_json(raw: str, step_count: int) -> list[dict[str, int | str]]:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    items = data if isinstance(data, list) else data.get("narrations") or data.get("lines") or []
    out: list[dict[str, int | str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        idx = int(item.get("step_index", item.get("step", -1)))
        txt = str(
            item.get("narration") or item.get("text") or item.get("narration_text") or ""
        ).strip()
        if 0 <= idx < step_count and txt:
            out.append({"step_index": idx, "text": txt[:220]})
    return out


def _fallback_dp(condensed: list[dict[str, Any]]) -> list[dict[str, int | str]]:
    out: list[dict[str, int | str]] = []
    for c in condensed:
        ch = c.get("changed") or []
        if not ch:
            continue
        line = c.get("line")
        text = c.get("text_line", "")
        if "dp[" in text or "dp" in ch:
            out.append(
                {
                    "step_index": int(c["step_index"]),
                    "text": f"第 {line} 行：更新 DP 表（见坐标与相邻格）"[:200],
                }
            )
        elif "i=" in text:
            out.append(
                {
                    "step_index": int(c["step_index"]),
                    "text": f"第 {line} 行：移动下标，准备填当前格"[:200],
                }
            )
    return out


def _fallback_linked_list(condensed: list[dict[str, Any]]) -> list[dict[str, int | str]]:
    out: list[dict[str, int | str]] = []
    for c in condensed:
        ch = c.get("changed") or []
        if not ch:
            continue
        line = c.get("line")
        hints = []
        if "curr" in ch:
            hints.append("curr 前进")
        if "prev" in ch:
            hints.append("prev 跟进")
        if any("next" in x or x == "nxt" for x in ch):
            hints.append("修改 next 指针")
        out.append(
            {
                "step_index": int(c["step_index"]),
                "text": f"第 {line} 行：" + ("；".join(hints) if hints else ", ".join(ch[:4])),
            }
        )
    return out


async def generate_trace_narration(
    *,
    slug: str = "",
    user_code: str,
    steps: list[dict[str, Any]],
    problem_title: str = "",
    prefer_demo: bool = True,
) -> list[dict[str, int | str]]:
    if not steps:
        return []

    if prefer_demo:
        demo = generate_demo_narration(slug, user_code, steps)
        if demo:
            return demo

    scene = _detect_scene(user_code, steps)
    condensed = _condense_steps(steps, scene)

    if not settings.llm_configured:
        demo = generate_demo_narration(slug, user_code, steps)
        if demo:
            return demo
        if scene == "dp_matrix":
            return _fallback_dp(condensed)
        if scene == "linked_list":
            return _fallback_linked_list(condensed)
        return []

    if scene == "linked_list":
        system = REVERSE_LIST_SYSTEM
        user_body = (
            f"题目：{problem_title or '反转链表'}\n\n"
            + "\n".join(f"[{c['step_index']}] {c['text_line']}" for c in condensed)
        )
    elif scene == "dp_matrix":
        system = DP_MATRIX_SYSTEM
        user_body = (
            f"题目：{problem_title or '不同路径 / 二维 DP'}\n\n"
            "每步说明：\n" + "\n".join(f"[{c['step_index']}] {c['text_line']}" for c in condensed)
        )
    else:
        system = (
            "你是算法可视化调试解说员。用一句中文说明每步数据变化。"
            '仅输出 JSON：[{"step_index":0,"narration":"…"}]'
        )
        user_body = json.dumps(
            {"problem": problem_title, "steps": condensed},
            ensure_ascii=False,
        )

    try:
        raw = await chat_completion(
            [{"role": "system", "content": system}, {"role": "user", "content": user_body}],
            temperature=0.35,
            max_tokens=2048,
        )
        parsed = _parse_narration_json(raw, len(steps))
        if parsed:
            return parsed
    except Exception:
        pass

    demo = generate_demo_narration(slug, user_code, steps)
    if demo:
        return demo
    if scene == "dp_matrix":
        return _fallback_dp(condensed)
    return _fallback_linked_list(condensed)
