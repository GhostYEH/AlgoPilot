"""AI 深度诊断：边界测例生成、轨迹破案式旁白、复杂度具象化报告。"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Literal

from core.config import settings
from services.agents.ast_analyzer import ASTAnalyzerAgent, AstAuditResult
from services.llm import chat_completion
from services.oj.stdio_io import ensure_stdio_fields

MAX_STEPS_IN_PROMPT = 80
MAX_TRACE_BUG_STEPS = 120
TRACE_DIAGNOSIS_LLM_TIMEOUT_SECONDS = 18
_logger = logging.getLogger(__name__)


def gate_code_before_dynamic_analysis(
    user_code: str,
    *,
    language: str = "python",
) -> AstAuditResult:
    """静动结合：动态 trace_runner / GDB 执行前的 AST 熔断门闸。"""
    return ASTAnalyzerAgent.audit(user_code, language=language)

TRACE_BUG_DIAGNOSIS_SYSTEM = """你是面向大一学生的算法调试教练。你的任务不是直接交付完整答案，而是用可验证证据帮助学生自己修正代码。
你将收到：题目描述、失败输入及期望/实际结果、学生代码、以及压缩后的执行轨迹。轨迹同时保留“变量未变化”的控制流步骤，因为遗漏更新本身可能就是根因。

任务：对比题目要求与学生轨迹，找出**逻辑开始偏离预期的最早一步**（bug 起源步）。

分析方法：
1. 先理解题目核心不变量（如：数组有序、指针单调递增、窗口内元素满足某条件）
2. 逐步检查关键变量是否违反不变量，找到**第一个**违反的步
3. 对照代码行号，指出是哪一行代码导致了该变量异常
4. 说明该步变量**应该是什么值**（根据题意推导），与**实际是什么值**（从轨迹读取）

教学要求：
- 禁止输出完整可提交代码或整段替换代码
- 先给一个观察问题，再给三层递进提示：L1 只指出观察位置；L2 解释不变量与状态差异；L3 给修改方向但仍不贴完整答案
- 重点说明：在哪一步（Step 索引）、代码第几行、哪些变量状态不符合题意
- 若涉及死循环，指出指针/循环变量为何未按预期推进，并说明循环不变量是什么
- bug_step_index 必须是轨迹中的 **0-based 步序号**（与输入 "Step N" 中的 N 一一致）
- diagnosis_title 必须是具体的错误描述（如"第5行 left 指针未收缩导致窗口过大"），不要写空泛标题
- detailed_analysis 必须包含：①该步变量应有值 vs 实际值 ②违反的不变量 ③对应代码行
- confidence 只有在失败测例确实复现且轨迹提供直接证据时才可为 high

严格只输出一个 JSON 对象，不要 markdown，不要额外字段：
{
  "bug_step_index": <int>,
  "diagnosis_title": "<15~40字中文标题，需包含变量名或行号>",
  "detailed_analysis": "<120~350字中文，必须包含：应有值vs实际值、违反的不变量、对应代码行>",
  "actual_state": "<轨迹直接观察到的状态，必须含变量名和值>",
  "expected_state": "<根据题意推导的应有状态>",
  "invariant": "<被破坏的循环/数据结构不变量，一句话>",
  "observation_question": "<让学生先观察该步的一个具体问题>",
  "hints": [
    {"level": 1, "title": "先观察", "content": "<不直接说答案>"},
    {"level": 2, "title": "再推理", "content": "<指出不变量和实际/应有差异>"},
    {"level": 3, "title": "修改方向", "content": "<指出应调整的语句或顺序，不给完整代码>"}
  ],
  "fix_suggestion": "<具体修改方向，不输出完整代码>",
  "verification": "<修改后用哪个最小输入、观察什么结果>",
  "confidence": "high|medium|low"
}"""

EDGE_CASE_SYSTEM = """你是算法竞赛助教。根据题目描述、已有样例与学生代码，生成一个**最小边界测例**（Minimal Failing Testcase），
使该学生代码在此测例上很可能出错（WA/RE/TLE），但测例本身规模尽量小。

分析步骤：
1. 仔细阅读题目约束条件（数据范围、特殊限制），找出学生代码可能遗漏的边界
2. 分析学生代码逻辑，识别以下常见漏洞：
   - 循环边界：off-by-one（< vs <=、0-indexed vs 1-indexed）
   - 空输入/零值：空数组、n=0、全零、空字符串
   - 极值：最大值、最小值、全负数、全相同元素
   - 特殊排列：已排序、逆序、含重复元素
   - 单元素：n=1 时循环是否正确处理
3. 优先选择能**直接暴露代码逻辑缺陷**的测例，而非随机边界

严格只输出 JSON 对象，不要 markdown：
{
  "stdin": "<洛谷 stdin 字符串，含换行>",
  "stdout": "<期望 stdout，含换行>",
  "reason": "<为何此测例能暴露 bug，30~80字，需指明代码哪部分会出错>",
  "category": "<edge 类型，如 empty|single|all_negative|duplicate|overflow|off_by_one|zero_value>"
}

若题目为力扣式 args/expected（非 stdin），则改为：
{
  "args": [...],
  "expected": ...,
  "reason": "...",
  "category": "..."
}

不要输出完整修正代码。"""

TRACE_DIAGNOSIS_SYSTEM = """你是算法调试侦探。根据执行轨迹的 condensed steps（每步 line、changed、关键变量），找出**逻辑开始出错的关键步**（通常 1~3 步），并给出破案式旁白。

分析方法：
1. 识别关键变量（循环指针、累加器、dp 状态、窗口边界等）
2. 对比每步变量的**应有值**（根据题意不变量推导）与**实际值**（从轨迹读取）
3. 找到第一个不一致的步作为 bug 起源，后续受影响的步也标注

旁白要求：
- 不要逐步流水账；只在 bug 起源步或关键转折步输出
- 旁白像侦探指出证据，必须包含**具体变量名和值**：「注意！Step 5 中 left=3 但窗口和已超过 target，left 应该右移到 4」
- 每步 30~100 字中文，越关键的步越详细
- critical=true 表示这是 bug 关键步（前端会标红）

严格只输出 JSON 数组：
[{"step_index": <int>, "text": "<旁白，必须含变量名和具体值>", "critical": true|false}]"""

COMPLEXITY_SYSTEM = """你是算法复杂度分析助教。根据输入规模 N 与 trace 步数（含 changed 的步数），
以及学生代码的结构特征，生成一份微型复杂度报告，帮助学生具象理解 O(N) vs O(N^2)。

分析要点：
1. 根据 N 与 meaningful_steps 的比值判断复杂度量级：
   - 比值 ≈1 → O(N)；比值 ≈log(N) → O(N log N)；比值 ≈N → O(N^2)
2. 结合代码中的循环嵌套层数、递归调用模式验证判断
3. 若为 O(N^2) 或更高，给出**具体的优化方向**（如：用哈希表替代内层遍历、双指针替代暴力搜索）

严格只输出 JSON：
{
  "input_size_n": <int>,
  "meaningful_steps": <int>,
  "estimated_complexity": "<如 O(N^2)>",
  "report": "<100~220字中文报告，必须包含：①本次 N 与步数 ②比值与量级 ③与代码结构的对应>",
  "alternative_hint": "<更优解法复杂度提示，需具体说明用什么数据结构/算法替代>"
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


def _mentions_code_line(text: str, line: object) -> bool:
    line_text = str(line or "").strip()
    if not line_text:
        return False
    return bool(
        re.search(
            rf"(?:第\s*{re.escape(line_text)}\s*行|code\s+line\s+{re.escape(line_text)}\b|"
            rf"line\s+{re.escape(line_text)}\b|L{re.escape(line_text)}\b)",
            text,
            re.IGNORECASE,
        )
    )


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
    压缩为 LLM 可读文本行。不能丢弃 changed 为空的步骤：遗漏更新恰恰表现为
    “执行到这里但状态没有变化”。
    返回 (lines, meaningful_count)。
    """
    lines: list[str] = []
    for i, s in enumerate(steps):
        if i >= MAX_TRACE_BUG_STEPS:
            lines.append(f"... (truncated, total {len(steps)} steps)")
            break
        changed = s.get("changed") or []
        vars_dict = s.get("vars") or {}
        parts: list[str] = []
        keys = list(changed)
        if not keys and isinstance(vars_dict, dict):
            keys = list(vars_dict.keys())[:8]
        for k in keys[:10]:
            snap = vars_dict.get(k) if isinstance(vars_dict, dict) else None
            parts.append(f"{k}={_format_snap_brief(snap)}")
        if len(changed) > 10:
            parts.append(f"+{len(changed) - 10} more")
        line_no = s.get("line", "?")
        change_note = ", ".join(str(k) for k in changed) if changed else "none"
        lines.append(
            f"Step {i} (code line {line_no}, changed={change_note}): "
            f"{', '.join(parts) if parts else '(no captured vars)'}"
        )
    return lines, sum(1 for s in steps[:MAX_TRACE_BUG_STEPS] if s.get("changed"))


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
    idx = max(0, min(idx, len(steps) - 1))
    step = steps[idx]
    line = step.get("line")
    changed = [str(name) for name in (step.get("changed") or []) if str(name)]
    evidence_text = " ".join(
        [
            title,
            analysis,
            str(parsed.get("actual_state") or ""),
            str(parsed.get("expected_state") or ""),
            str(parsed.get("invariant") or ""),
        ]
    )
    evidence_complete = (not line or _mentions_code_line(evidence_text, line)) and (
        not changed or any(name in evidence_text for name in changed)
    )
    hints: list[dict[str, Any]] = []
    for level, item in enumerate(parsed.get("hints") or [], start=1):
        if not isinstance(item, dict):
            continue
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        hints.append(
            {
                "level": max(1, min(3, int(item.get("level") or level))),
                "title": str(item.get("title") or f"提示 {level}")[:24],
                "content": content[:360],
            }
        )
    confidence = str(parsed.get("confidence") or "medium").lower()
    if confidence not in ("high", "medium", "low"):
        confidence = "medium"
    if not evidence_complete and confidence == "high":
        confidence = "medium"
    return {
        "bug_step_index": idx,
        "diagnosis_title": title[:80],
        "detailed_analysis": analysis[:800],
        "actual_state": str(parsed.get("actual_state") or "")[:300],
        "expected_state": str(parsed.get("expected_state") or "")[:300],
        "invariant": str(parsed.get("invariant") or "")[:300],
        "observation_question": str(parsed.get("observation_question") or "")[:300],
        "hints": hints[:3],
        "fix_suggestion": str(parsed.get("fix_suggestion") or "")[:500],
        "verification": str(parsed.get("verification") or "")[:300],
        "confidence": confidence,
    }


def _fallback_trace_bug_diagnosis(
    steps: list[dict[str, Any]],
    compressed_lines: list[str],
    *,
    user_code: str = "",
    judge_verdict: str = "",
) -> dict[str, Any]:
    """无 LLM 时仅返回可由轨迹直接支持的诊断线索。"""
    pointer_keys = ("left", "right", "l", "r", "i", "j", "slow", "fast", "curr", "prev", "head", "tail")
    last_value: dict[str, str] = {}
    stagnant_count: dict[str, int] = {}
    first_changed_idx = -1

    for i, s in enumerate(steps):
        changed = s.get("changed") or []
        if not changed:
            continue
        if first_changed_idx < 0:
            first_changed_idx = i
        vars_map = s.get("vars") or {}
        for k in changed:
            if k not in pointer_keys:
                continue
            current = _format_snap_brief(vars_map.get(k))
            if current == last_value.get(k):
                stagnant_count[k] = stagnant_count.get(k, 0) + 1
            else:
                stagnant_count[k] = 0
            last_value[k] = current
            if stagnant_count[k] >= 2:
                return {
                    "bug_step_index": i,
                    "diagnosis_title": f"变量 {k} 连续保持 {current}，存在停滞证据",
                    "detailed_analysis": (
                        f"Step {i + 1}（代码第 {s.get('line')} 行）中 {k}={current}，"
                        f"且连续至少 3 次相关快照保持同值。该事实支持“{k} 未推进”的判断；"
                        f"若判题结果为 {judge_verdict or '未通过'}，应核对循环条件和更新分支，"
                        "但仍需结合题目不变量确认它是否为最终根因。"
                    ),
                    "source": "fallback",
                    "actual_state": f"{k}={current}，连续至少 3 次相关快照未变化",
                    "expected_state": f"{k} 应在每轮满足更新条件时继续推进",
                    "invariant": f"循环继续时，关键推进变量 {k} 不能长期停滞",
                    "observation_question": f"观察 Step {i + 1}：{k} 为什么仍是 {current}？",
                    "hints": [
                        {"level": 1, "title": "先观察", "content": f"对比前后三步的 {k}。"},
                        {"level": 2, "title": "再推理", "content": f"检查哪些分支负责推进 {k}，是否存在未执行的路径。"},
                        {"level": 3, "title": "修改方向", "content": f"确保循环继续前 {k} 在正确分支完成更新。"},
                    ],
                    "fix_suggestion": f"检查并补全 {k} 的推进逻辑。",
                    "verification": "用最小失败输入重跑，确认该变量不再连续停滞。",
                    "confidence": "medium",
                }

    bug_idx = first_changed_idx if first_changed_idx >= 0 else 0
    s = steps[bug_idx] if bug_idx < len(steps) else steps[0]
    ch = s.get("changed") or []
    line = s.get("line", "?")
    return {
        "bug_step_index": bug_idx,
        "diagnosis_title": "现有规则无法唯一确定根因",
        "detailed_analysis": (
            f"Step {bug_idx + 1}（代码第 {line} 行）记录到"
            f"{('、'.join(ch[:5]) if ch else '程序状态')}变化，但轨迹只给出实际状态，"
            "没有足够证据自动推导该题此处的唯一期望值。请先用失败输入手算关键不变量，"
            "再对照后续 Trace 找到首次偏离；当前结论仅是定位起点，不是已证实根因。"
            + (f" 压缩轨迹共有 {len(compressed_lines)} 个有效步。" if compressed_lines else "")
        ),
        "source": "fallback",
        "actual_state": f"Step {bug_idx + 1} 仅确认 {('、'.join(ch[:5]) if ch else '程序状态')}发生变化",
        "expected_state": "现有轨迹不足以从规则推导唯一应有值",
        "invariant": "需要结合题目要求手算该步应保持的不变量",
        "observation_question": f"从代码第 {line} 行开始，哪一个状态第一次与手算结果不同？",
        "hints": [
            {"level": 1, "title": "先观察", "content": f"从 Step {bug_idx + 1} 开始逐步对照变量。"},
            {"level": 2, "title": "再推理", "content": "先写出每轮循环结束时必须成立的一句话。"},
            {"level": 3, "title": "修改方向", "content": "找到首次破坏该不变量的分支后再调整对应语句。"},
        ],
        "fix_suggestion": "证据不足，暂不建议直接修改代码。",
        "verification": "使用真实失败输入手算关键状态，再与 Trace 对照。",
        "confidence": "low",
    }


async def diagnose_trace_bug(
    problem_description: str,
    user_code: str,
    trace_steps: list[dict[str, Any]],
    *,
    slug: str = "",
    judge_verdict: str = "",
    failed_cases: list[dict[str, Any]] | None = None,
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

    from services.oj.rule_diagnosis import diagnose_known_error_pattern

    known = diagnose_known_error_pattern(
        slug=slug,
        user_code=user_code,
        trace_steps=trace_steps,
    )
    if known:
        return known

    if settings.llm_configured:
        failed_hint = ""
        if failed_cases:
            failed_hint = "\n\n## 失败用例\n" + "\n".join(
                f"- 用例 {c.get('index', '?')}: 输入 {str(c.get('input_preview', ''))[:100]}；"
                f"期望 {str(c.get('expected_preview', ''))[:80]}；"
                f"实际 {str(c.get('actual_preview', ''))[:80]}；"
                f"判题信息 {str(c.get('message', ''))[:80]}"
                for c in failed_cases[:3]
            )
        verdict_hint = f"\n\n## 判题结果：{judge_verdict}" if judge_verdict else ""

        user_body = (
            f"## 题目描述\n{(problem_description or '（无描述）')[:2000]}\n\n"
            f"## 学生代码\n```\n{user_code[:3500]}\n```"
            f"{verdict_hint}{failed_hint}\n\n"
            f"## 压缩轨迹（共 {len(trace_steps)} 步；changed=none 表示该步执行但状态未变化）\n"
            + "\n".join(compressed_lines[:MAX_STEPS_IN_PROMPT])
        )
        if len(compressed_lines) > MAX_STEPS_IN_PROMPT:
            user_body += f"\n...（已截断，仅展示前 {MAX_STEPS_IN_PROMPT} 行）"

        try:
            raw = await asyncio.wait_for(
                chat_completion(
                    [
                        {"role": "system", "content": TRACE_BUG_DIAGNOSIS_SYSTEM},
                        {"role": "user", "content": user_body},
                    ],
                    temperature=0.2,
                    max_tokens=1200,
                    json_mode=True,
                ),
                timeout=TRACE_DIAGNOSIS_LLM_TIMEOUT_SECONDS,
            )
            out = _parse_trace_bug_diagnosis(raw, max_step=max_idx, steps=trace_steps)
            out["source"] = "llm"
            return out
        except Exception as exc:
            _logger.warning("Spark trace diagnosis failed; using fallback: %s", exc, exc_info=True)

    out = _fallback_trace_bug_diagnosis(
        trace_steps, compressed_lines,
        user_code=user_code,
        judge_verdict=judge_verdict,
    )
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

    if settings.llm_configured:
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
                json_mode=True,
            )
            parsed = _parse_json_object(raw)
            case = _normalize_edge_case(parsed, judge_mode, sample)
            return {
                "case": case,
                "reason": str(parsed.get("reason") or "AI 生成的边界测例"),
                "category": str(parsed.get("category") or "edge"),
                "source": "llm",
            }
        except Exception as exc:
            _logger.warning("Spark edge-case generation failed; using fallback: %s", exc, exc_info=True)

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

    if settings.llm_configured:
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
                temperature=0.3,
                max_tokens=1500,
                json_mode=True,
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
        except Exception as exc:
            _logger.warning("Spark trace narration diagnosis failed; using fallback: %s", exc, exc_info=True)

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

    if settings.llm_configured:
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
                json_mode=True,
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
        except Exception as exc:
            _logger.warning("Spark complexity analysis failed; using fallback: %s", exc, exc_info=True)

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
