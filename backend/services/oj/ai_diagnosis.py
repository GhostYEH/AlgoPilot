"""AI 深度诊断：边界测例生成、轨迹破案式旁白、复杂度具象化报告。"""

from __future__ import annotations

import json
import re
from typing import Any, Literal

from core.config import settings
from services.agents.ast_analyzer import ASTAnalyzerAgent, AstAuditResult
from services.llm import chat_completion
from services.oj.stdio_io import ensure_stdio_fields

MAX_STEPS_IN_PROMPT = 80
MAX_TRACE_BUG_STEPS = 120


def gate_code_before_dynamic_analysis(
    user_code: str,
    *,
    language: str = "python",
) -> AstAuditResult:
    """静动结合：动态 trace_runner / GDB 执行前的 AST 熔断门闸。"""
    return ASTAnalyzerAgent.audit(user_code, language=language)

TRACE_BUG_DIAGNOSIS_SYSTEM = """你是一个算法竞赛金牌教练与调试侦探。
你将收到：题目描述、学生代码、以及压缩后的执行轨迹（仅含 changed 非空的步，每步一行文本快照）。

任务：对比题目要求与学生轨迹，找出**逻辑开始偏离预期的最早一步**（bug 起源步）。
- 不要只给修正后的完整代码
- 重点说明：在哪一步（Step 索引）、哪些变量状态不符合题意
- 若涉及死循环，指出指针/循环变量为何未按预期推进
- bug_step_index 必须是轨迹中的 **0-based 步序号**（与输入 "Step N" 中的 N 一致）

严格只输出一个 JSON 对象，不要 markdown，不要额外字段：
{
  "bug_step_index": <int>,
  "diagnosis_title": "<15~40字中文标题>",
  "detailed_analysis": "<80~280字中文，说明该步为何错误及应如何理解>"
}"""

EDGE_CASE_SYSTEM = """你是算法竞赛助教。根据题目描述、已有样例与学生代码，生成一个**最小边界测例**（Minimal Failing Testcase），
使该学生代码在此测例上很可能出错（WA/RE/TLE），但测例本身规模尽量小（如空数组、单元素、全负数、边界值等）。

严格只输出 JSON 对象，不要 markdown：
{
  "stdin": "<洛谷 stdin 字符串，含换行>",
  "stdout": "<期望 stdout，含换行>",
  "reason": "<为何此测例能暴露 bug，20~60字>",
  "category": "<edge 类型，如 empty|single|all_negative|duplicate|overflow>"
}

若题目为力扣式 args/expected（非 stdin），则改为：
{
  "args": [...],
  "expected": ...,
  "reason": "...",
  "category": "..."
}

不要输出完整修正代码。"""

TRACE_DIAGNOSIS_SYSTEM = """你是算法调试侦探。根据执行轨迹的 condensed steps（每步 line、changed、关键变量），
找出**逻辑开始出错的关键步**（通常 1~3 步），并给出破案式旁白。

要求：
- 不要逐步流水账；只在 bug 起源步或关键转折步输出
- 旁白像侦探指出证据：「注意！在这里，你的 left 指针没有向右移动…」
- 每步 25~80 字中文
- critical=true 表示这是 bug 关键步（前端会标红）

严格只输出 JSON 数组：
[{"step_index": <int>, "text": "<旁白>", "critical": true|false}]"""

COMPLEXITY_SYSTEM = """你是算法复杂度分析助教。根据输入规模 N 与 trace 步数（含 changed 的步数），
生成一份微型复杂度报告，帮助学生具象理解 O(N) vs O(N^2)。

严格只输出 JSON：
{
  "input_size_n": <int>,
  "meaningful_steps": <int>,
  "estimated_complexity": "<如 O(N^2)>",
  "report": "<80~180字中文报告，含本次数据与预期>",
  "alternative_hint": "<更优解法复杂度提示，可选>"
}"""


def _parse_json_object(raw: str) -> dict[str, Any]:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


def _parse_json_array(raw: str) -> list[Any]:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


def _estimate_input_size(case: dict[str, Any], steps: list[dict[str, Any]]) -> int:
    stdin = case.get("stdin") or ""
    if stdin:
        lines = [ln.strip() for ln in stdin.strip().split("\n") if ln.strip()]
        if lines:
            try:
                n = int(lines[0])
                if n >= 0:
                    return max(1, n)
            except ValueError:
                pass
        return max(1, len(lines))
    args = case.get("args") or []
    for arg in args:
        if isinstance(arg, list):
            return max(1, len(arg))
    for s in steps[:8]:
        for snap in (s.get("vars") or {}).values():
            if snap.get("type") == "list" and isinstance(snap.get("value"), list):
                return max(1, len(snap["value"]))
    return max(1, len(args) if args else 5)


def _meaningful_step_count(steps: list[dict[str, Any]]) -> int:
    return sum(1 for s in steps if s.get("changed"))


def _format_snap_brief(snap: dict[str, Any] | None) -> str:
    if not snap:
        return "?"
    t = str(snap.get("type") or "?")
    v = snap.get("value")
    hint = snap.get("view_hint")
    if t in ("int", "float", "bool", "str", "none"):
        return "None" if v is None else str(v)
    if t == "sequence" and isinstance(v, list):
        items = [str(x) for x in v[:10]]
        tail = "…" if len(v) > 10 else ""
        label = hint or "seq"
        return f"{label}[{','.join(items)}{tail}]"
    if t in ("list", "stack", "queue") and isinstance(v, list):
        items = [str(x) for x in v[:10]]
        tail = "…" if len(v) > 10 else ""
        return f"{t}[{','.join(items)}{tail}]"
    if t == "associative" and isinstance(v, list):
        pairs: list[str] = []
        for e in v[:6]:
            if isinstance(e, dict):
                pairs.append(f"{e.get('key')}→{e.get('value')}")
        tail = "…" if len(v) > 6 else ""
        label = hint or "map"
        return f"{label}{{{','.join(pairs)}{tail}}}"
    if t == "matrix" and isinstance(v, dict):
        rows = v.get("rows", "?")
        cols = v.get("cols", "?")
        return f"matrix({rows}x{cols})"
    if t == "node_ref" and isinstance(v, dict):
        return f"node@{v.get('node')}"
    if t == "linked_list" and isinstance(v, dict):
        nodes = v.get("nodes") or {}
        return f"list(len={len(nodes)})"
    if t == "tree" and isinstance(v, dict):
        nodes = v.get("nodes") or {}
        return f"tree(len={len(nodes)})"
    if isinstance(v, (list, dict)):
        s = json.dumps(v, ensure_ascii=False)
        return s[:48] + ("…" if len(s) > 48 else "")
    return t


def compress_trace_steps_to_text(steps: list[dict[str, Any]]) -> tuple[list[str], int]:
    """
    过滤 changed 为空的步，压缩为 LLM 可读文本行。
    返回 (lines, meaningful_count)。
    """
    lines: list[str] = []
    for i, s in enumerate(steps):
        if i >= MAX_TRACE_BUG_STEPS:
            lines.append(f"... (truncated, total {len(steps)} steps)")
            break
        changed = s.get("changed") or []
        if not changed:
            continue
        vars_dict = s.get("vars") or {}
        parts: list[str] = []
        for k in changed[:10]:
            snap = vars_dict.get(k) if isinstance(vars_dict, dict) else None
            parts.append(f"{k}={_format_snap_brief(snap)}")
        if len(changed) > 10:
            parts.append(f"+{len(changed) - 10} more")
        line_no = s.get("line", "?")
        lines.append(f"Step {i} (code line {line_no}): {', '.join(parts)}")
    return lines, len(lines)


def _normalize_bug_step_index(idx: int, steps: list[dict[str, Any]]) -> int:
    """将 LLM 返回的步序号钳制到合法范围，并尽量落到 changed 非空的步。"""
    if not steps:
        return 0
    idx = max(0, min(int(idx), len(steps) - 1))
    if steps[idx].get("changed"):
        return idx
    for delta in range(1, len(steps)):
        for candidate in (idx - delta, idx + delta):
            if 0 <= candidate < len(steps) and steps[candidate].get("changed"):
                return candidate
    return idx


def _parse_trace_bug_diagnosis(
    raw: str, *, max_step: int, steps: list[dict[str, Any]]
) -> dict[str, Any]:
    parsed = _parse_json_object(raw)
    raw_idx = parsed.get("bug_step_index", -1)
    try:
        idx = int(raw_idx)
    except (TypeError, ValueError):
        raise ValueError("invalid bug_step_index") from None
    title = str(parsed.get("diagnosis_title") or "").strip()
    analysis = str(parsed.get("detailed_analysis") or "").strip()
    if not (0 <= idx <= max_step):
        raise ValueError("invalid bug_step_index")
    if not title or not analysis:
        raise ValueError("missing diagnosis fields")
    idx = _normalize_bug_step_index(idx, steps)
    return {
        "bug_step_index": idx,
        "diagnosis_title": title[:80],
        "detailed_analysis": analysis[:600],
    }


def _fallback_trace_bug_diagnosis(
    steps: list[dict[str, Any]],
    compressed_lines: list[str],
) -> dict[str, Any]:
    """无 LLM 时：选首个有 changed 的中后段步或指针停滞步。"""
    pointer_keys = ("left", "right", "l", "r", "i", "j", "slow", "fast", "curr")
    stagnant: dict[str, int] = {}
    bug_idx = -1

    for i, s in enumerate(steps):
        changed = s.get("changed") or []
        if not changed:
            continue
        if bug_idx < 0 and i >= max(1, len(steps) // 4):
            bug_idx = i
        for k in changed:
            if k in pointer_keys:
                stagnant[k] = stagnant.get(k, 0) + 1
                if stagnant[k] >= 3:
                    bug_idx = i
                    return {
                        "bug_step_index": i,
                        "diagnosis_title": f"{k} 指针未及时移动",
                        "detailed_analysis": (
                            f"第 {s.get('line')} 步（Step {i}）起，变量 {k} 多次重复出现在 changed 中，"
                            f"常见于窗口未收缩或循环未推进，可能导致 WA 或 TLE。请核对此处与题目不变量。"
                        ),
                        "source": "fallback",
                    }
            else:
                stagnant.pop(k, None)

    if bug_idx < 0:
        for i, s in enumerate(steps):
            if s.get("changed"):
                bug_idx = i
                break

    if bug_idx < 0:
        bug_idx = 0

    s = steps[bug_idx] if bug_idx < len(steps) else steps[0]
    ch = s.get("changed") or []
    return {
        "bug_step_index": bug_idx,
        "diagnosis_title": "关键变量状态异常",
        "detailed_analysis": (
            f"在第 {s.get('line')} 步（Step {bug_idx}）处，"
            f"{('、'.join(ch[:5]) if ch else '程序状态')} 发生变化，"
            f"请对照题目检查此处逻辑是否与预期一致。"
            + (f" 压缩轨迹共 {len(compressed_lines)} 个有效步。" if compressed_lines else "")
        ),
        "source": "fallback",
    }


async def diagnose_trace_bug(
    problem_description: str,
    user_code: str,
    trace_steps: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    根据已有 trace 步序列，定位 bug 起源步并返回结构化诊断。
    """
    if not trace_steps:
        return {
            "bug_step_index": 0,
            "diagnosis_title": "无可用轨迹",
            "detailed_analysis": "当前没有可分析的执行步，请先运行「可视化调试」生成轨迹后再诊断。",
            "source": "empty",
        }

    max_idx = len(trace_steps) - 1
    compressed_lines, _ = compress_trace_steps_to_text(trace_steps)

    if not compressed_lines:
        return {
            "bug_step_index": 0,
            "diagnosis_title": "轨迹无变量变化",
            "detailed_analysis": "所有步的 changed 均为空，无法定位逻辑分歧。请确认追踪已捕获局部变量。",
            "source": "empty",
        }

    if settings.siliconflow_api_key:
        user_body = (
            f"## 题目描述\n{(problem_description or '（无描述）')[:2000]}\n\n"
            f"## 学生代码\n```\n{user_code[:3500]}\n```\n\n"
            f"## 压缩轨迹（共 {len(trace_steps)} 步，以下仅含 changed≠∅ 的步）\n"
            + "\n".join(compressed_lines[:MAX_STEPS_IN_PROMPT])
        )
        if len(compressed_lines) > MAX_STEPS_IN_PROMPT:
            user_body += f"\n...（已截断，仅展示前 {MAX_STEPS_IN_PROMPT} 行）"

        try:
            raw = await chat_completion(
                [
                    {"role": "system", "content": TRACE_BUG_DIAGNOSIS_SYSTEM},
                    {"role": "user", "content": user_body},
                ],
                temperature=0.25,
                max_tokens=900,
            )
            out = _parse_trace_bug_diagnosis(raw, max_step=max_idx, steps=trace_steps)
            out["source"] = "llm"
            return out
        except Exception:
            pass

    out = _fallback_trace_bug_diagnosis(trace_steps, compressed_lines)
    out["bug_step_index"] = _normalize_bug_step_index(out["bug_step_index"], trace_steps)
    return out


def _format_condensed_step(step_index: int, s: dict[str, Any]) -> dict[str, Any]:
    changed = s.get("changed") or []
    vars_brief: dict[str, str] = {}
    for k in changed[:8]:
        snap = (s.get("vars") or {}).get(k) or {}
        t = snap.get("type", "?")
        v = snap.get("value")
        if t == "int":
            vars_brief[k] = str(v)
        elif t == "list" and isinstance(v, list):
            vars_brief[k] = f"list[{len(v)}]"
        elif t == "node_ref" and isinstance(v, dict):
            vars_brief[k] = str(v.get("node"))
        else:
            vars_brief[k] = t
    return {
        "step_index": step_index,
        "line": s.get("line"),
        "changed": changed,
        "vars_brief": vars_brief,
    }


def _condense_steps_for_diagnosis(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    valid_steps: list[tuple[int, dict[str, Any]]] = []
    for i, s in enumerate(steps):
        changed = s.get("changed") or []
        if changed or i == 0:
            valid_steps.append((i, s))

    if len(valid_steps) <= MAX_STEPS_IN_PROMPT:
        return [_format_condensed_step(i, s) for i, s in valid_steps]

    head_count = 30
    tail_count = 50
    head = valid_steps[:head_count]
    tail = valid_steps[-tail_count:]
    omitted = len(valid_steps) - head_count - tail_count

    gap_marker = {
        "step_index": -1,
        "line": None,
        "changed": ["..."],
        "vars_brief": {"...": f"由于长度限制，中间 {omitted} 步已省略"},
    }

    out = [_format_condensed_step(i, s) for i, s in head]
    out.append(gap_marker)
    out.extend(_format_condensed_step(i, s) for i, s in tail)
    return out


def _normalize_edge_case(raw: dict[str, Any], judge_mode: str, sample: dict[str, Any]) -> dict[str, Any]:
    case: dict[str, Any] = {}
    if judge_mode == "stdio" or raw.get("stdin") is not None:
        case["stdin"] = str(raw.get("stdin") or sample.get("stdin") or "")
        case["stdout"] = str(raw.get("stdout") or sample.get("stdout") or "")
        return ensure_stdio_fields(case)
    if raw.get("args") is not None:
        case["args"] = raw["args"]
        case["expected"] = raw.get("expected", sample.get("expected"))
        return ensure_stdio_fields(case)
    return ensure_stdio_fields({**sample, **raw})


def _fallback_edge_cases(sample: dict[str, Any]) -> list[dict[str, Any]]:
    """无 LLM 时的规则边界测例候选。"""
    candidates: list[dict[str, Any]] = []
    base = ensure_stdio_fields(dict(sample))
    stdin = base.get("stdin") or ""
    lines = stdin.strip().split("\n") if stdin else []

    if lines:
        try:
            n = int(lines[0].strip())
            if n > 1:
                candidates.append(ensure_stdio_fields({"stdin": "0\n", "stdout": base.get("stdout") or ""}))
                candidates.append(
                    ensure_stdio_fields({"stdin": "1\n0\n", "stdout": base.get("stdout") or ""})
                )
            elif n == 0:
                candidates.append(ensure_stdio_fields({"stdin": "1\n0\n", "stdout": base.get("stdout") or ""}))
        except ValueError:
            pass

    args = sample.get("args") or []
    if args and isinstance(args[0], list) and len(args[0]) > 1:
        empty_case = {"args": [[]] + list(args[1:]), "expected": sample.get("expected")}
        candidates.append(ensure_stdio_fields(empty_case))
        single = {"args": [[args[0][0]] + list(args[1:])], "expected": sample.get("expected")}
        candidates.append(ensure_stdio_fields(single))

    if not candidates:
        candidates.append(base)
    return candidates


async def generate_edge_case(
    *,
    problem_title: str,
    description: str,
    judge_mode: str,
    sample: dict[str, Any],
    user_code: str,
    failed_cases: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """生成最小失败边界测例。"""
    failed_hint = ""
    if failed_cases:
        failed_hint = "\n\n已失败用例摘要：\n" + "\n".join(
            f"- 输入 {c.get('input_preview', '')[:120]} → {c.get('message', '')[:80]}"
            for c in failed_cases[:3]
        )

    if settings.siliconflow_api_key:
        user_body = json.dumps(
            {
                "title": problem_title,
                "description": description[:1200],
                "judge_mode": judge_mode,
                "sample": {
                    k: sample.get(k)
                    for k in ("stdin", "stdout", "args", "expected")
                    if sample.get(k) is not None
                },
                "user_code": user_code[:4000],
                "failed_cases_hint": failed_hint,
            },
            ensure_ascii=False,
        )
        try:
            raw = await chat_completion(
                [{"role": "system", "content": EDGE_CASE_SYSTEM}, {"role": "user", "content": user_body}],
                temperature=0.4,
                max_tokens=800,
            )
            parsed = _parse_json_object(raw)
            case = _normalize_edge_case(parsed, judge_mode, sample)
            return {
                "case": case,
                "reason": str(parsed.get("reason") or "AI 生成的边界测例"),
                "category": str(parsed.get("category") or "edge"),
                "source": "llm",
            }
        except Exception:
            pass

    for cand in _fallback_edge_cases(sample):
        return {
            "case": cand,
            "reason": "规则生成的边界测例（空输入/单元素等）",
            "category": "rule_based",
            "source": "fallback",
        }
    return {
        "case": ensure_stdio_fields(dict(sample)),
        "reason": "使用首个样例作为诊断输入",
        "category": "sample",
        "source": "fallback",
    }


async def generate_trace_diagnosis(
    *,
    user_code: str,
    steps: list[dict[str, Any]],
    problem_title: str = "",
    edge_reason: str = "",
) -> list[dict[str, Any]]:
    """生成破案式轨迹诊断旁白（含 critical 标记）。"""
    if not steps:
        return []

    condensed = _condense_steps_for_diagnosis(steps)

    if settings.siliconflow_api_key:
        user_body = json.dumps(
            {
                "problem": problem_title,
                "edge_reason": edge_reason,
                "code_excerpt": user_code[:2500],
                "steps": condensed,
            },
            ensure_ascii=False,
        )
        try:
            raw = await chat_completion(
                [
                    {"role": "system", "content": TRACE_DIAGNOSIS_SYSTEM},
                    {"role": "user", "content": user_body},
                ],
                temperature=0.35,
                max_tokens=1200,
            )
            items = _parse_json_array(raw)
            out: list[dict[str, Any]] = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                idx = int(item.get("step_index", -1))
                txt = str(item.get("text") or "").strip()
                if 0 <= idx < len(steps) and txt:
                    out.append(
                        {
                            "step_index": idx,
                            "text": txt[:240],
                            "critical": bool(item.get("critical", True)),
                        }
                    )
            if out:
                return out
        except Exception:
            pass

    return _fallback_trace_diagnosis(condensed, steps)


def _fallback_trace_diagnosis(
    condensed: list[dict[str, Any]], steps: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """规则兜底：找 changed 含指针/循环变量且长时间不变的步。"""
    out: list[dict[str, Any]] = []
    pointer_keys = ("left", "right", "l", "r", "i", "j", "curr", "prev", "slow", "fast")
    stagnant: dict[str, int] = {}

    for c in condensed:
        idx = int(c["step_index"])
        changed = c.get("changed") or []
        line = c.get("line")
        for k in changed:
            if k in pointer_keys:
                stagnant[k] = stagnant.get(k, 0) + 1
                if stagnant[k] >= 3:
                    out.append(
                        {
                            "step_index": idx,
                            "text": f"注意！第 {line} 步起 {k} 多次未按预期移动，可能导致死循环或漏解。",
                            "critical": True,
                        }
                    )
                    stagnant[k] = 0
            else:
                stagnant.pop(k, None)

    if not out and condensed:
        mid = condensed[min(len(condensed) // 2, len(condensed) - 1)]
        idx = int(mid["step_index"])
        ch = mid.get("changed") or []
        out.append(
            {
                "step_index": idx,
                "text": f"第 {mid.get('line')} 步：{('、'.join(ch[:4]) if ch else '变量')} 发生变化，请核对此处逻辑。",
                "critical": True,
            }
        )
    return out[:3]


async def analyze_complexity(
    *,
    steps: list[dict[str, Any]],
    case: dict[str, Any],
    user_code: str,
    problem_title: str = "",
) -> dict[str, Any]:
    """分析步数与输入规模关系，生成复杂度微型报告。"""
    n = _estimate_input_size(case, steps)
    meaningful = _meaningful_step_count(steps)
    total = len(steps)

    if settings.siliconflow_api_key:
        code_lower = user_code.lower()
        nested_hint = "双层循环" if code_lower.count("for") >= 2 else "单层或递归"
        user_body = json.dumps(
            {
                "problem": problem_title,
                "input_size_n": n,
                "total_steps": total,
                "meaningful_steps": meaningful,
                "code_pattern_hint": nested_hint,
            },
            ensure_ascii=False,
        )
        try:
            raw = await chat_completion(
                [
                    {"role": "system", "content": COMPLEXITY_SYSTEM},
                    {"role": "user", "content": user_body},
                ],
                temperature=0.3,
                max_tokens=600,
            )
            parsed = _parse_json_object(raw)
            return {
                "input_size_n": int(parsed.get("input_size_n") or n),
                "total_steps": total,
                "meaningful_steps": int(parsed.get("meaningful_steps") or meaningful),
                "estimated_complexity": str(parsed.get("estimated_complexity") or "O(?)"),
                "report": str(parsed.get("report") or "")[:400],
                "alternative_hint": str(parsed.get("alternative_hint") or "")[:200],
                "source": "llm",
            }
        except Exception:
            pass

    return _fallback_complexity(n, total, meaningful, user_code)


def _fallback_complexity(n: int, total: int, meaningful: int, user_code: str) -> dict[str, Any]:
    ratio = meaningful / max(1, n)
    nested = user_code.lower().count("for") >= 2

    if nested and meaningful > n * 1.5:
        est: Literal["O(N)", "O(N^2)", "O(N log N)", "O(?)"] = "O(N^2)"
        alt = "若改用哈希表或双指针，步数可降至 O(N) 量级。"
    elif meaningful <= n * 2:
        est = "O(N)"
        alt = "当前步数与输入规模近似线性，复杂度较优。"
    else:
        est = "O(N log N)" if meaningful > n * 2 else "O(N)"
        alt = "可对比不同数据结构的访问次数。"

    report = (
        f"本次输入规模 N≈{n}，共记录 {total} 步执行（其中 {meaningful} 步有变量变化）。"
        f"步数/规模比约为 {ratio:.1f}，结合代码结构推测为 {est}。"
    )
    if nested and est == "O(N^2)":
        report += f" 若换成哈希表，同类问题步数可降至 {max(8, n + 3)} 步左右。"

    return {
        "input_size_n": n,
        "total_steps": total,
        "meaningful_steps": meaningful,
        "estimated_complexity": est,
        "report": report,
        "alternative_hint": alt,
        "source": "fallback",
    }


def merge_diagnosis_narrations(
    step_narrations: list[dict[str, int | str]],
    diagnosis: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """合并普通旁白与 AI 诊断旁白，诊断步优先且标 critical。"""
    by_idx: dict[int, dict[str, Any]] = {}
    for n in step_narrations:
        idx = int(n["step_index"])
        by_idx[idx] = {"step_index": idx, "text": str(n["text"]), "critical": False}
    for d in diagnosis:
        idx = int(d["step_index"])
        by_idx[idx] = {
            "step_index": idx,
            "text": str(d["text"]),
            "critical": bool(d.get("critical", True)),
        }
    return sorted(by_idx.values(), key=lambda x: x["step_index"])
