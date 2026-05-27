"""学习路径 Agent：启发式 DAG 规划为主，LLM 润色为辅。"""

from __future__ import annotations

import json
import re

from schemas.learning_path import LearningPathReplanRequest, ModuleProgressInput
from services.agents.base import BaseAgent
from services.knowledge.concept_clusters import concept_clusters
from services.agents.learning_path_catalog import (
    DEFAULT_ORDER,
    MODULE_CATALOG,
    MODULE_DEPENDENCIES,
    PHASE_RANK,
    VALID_MODULE_KEYS,
    lookup_remediation,
)
from services.llm import chat_completion

PATH_SYSTEM = """你是「学习路径 Agent（PlannerAgent）」，为大一计科「数据结构与算法」课程**润色**个性化学习路径说明。

## 规则
1. 不得改变用户消息中 ordered_keys 的顺序（已由系统按依赖与进度排好）。
2. 仅输出 summary、rationale、next_module_key 及各 step 的 reason（15字内）。
3. 输出**唯一** JSON，不要 markdown 代码块：
{
  "summary": "一句话路径策略",
  "rationale": "80～150字说明为何这样排序",
  "next_module_key": "建议下一步 module_key",
  "steps": [{"module_key": "array", "rank": 1, "reason": "…", "phase": "foundation"}]
}"""


class LearningPathAgent(BaseAgent):
    name = "LearningPathAgent"
    role = "学习路径规划"

    def build_messages(
        self,
        *,
        profile_block: str,
        request: LearningPathReplanRequest,
        ordered_keys: list[str],
    ) -> list[dict[str, str]]:
        progress_lines = []
        for m in request.modules:
            status = f"{m.percent}%"
            if m.total_count:
                status += f"，{m.done_count}/{m.total_count} 小节"
            progress_lines.append(
                f"- {m.key} ({m.label}): {status}，阶段={m.phase}，available={m.available}"
            )
        user = "\n".join(
            [
                f"学生画像：\n{profile_block}",
                f"整体进度：{request.overall_percent}%",
                "模块进度：\n" + ("\n".join(progress_lines) if progress_lines else "（无）"),
                f"已排好顺序（勿改动）：{ordered_keys}",
                "请仅润色 summary/rationale/next_module_key 与各 step.reason。",
            ]
        )
        return [{"role": "system", "content": PATH_SYSTEM}, {"role": "user", "content": user}]

    def temperature(self) -> float:
        return 0.35

    def max_tokens(self) -> int:
        return 1200

    async def plan(
        self,
        *,
        profile_block: str,
        request: LearningPathReplanRequest,
        dimension_scores: dict[str, int] | None = None,
        remediation_before: str | None = None,
    ) -> dict:
        base = _heuristic_plan(profile_block, request, dimension_scores or {})
        ordered = _topo_sort_keys(base["ordered_keys"])
        base["ordered_keys"] = ordered
        base["steps"] = _rebuild_steps(ordered, base["steps"], request, dimension_scores or {})
        base["next_module_key"] = _pick_next(ordered, {m.key: m for m in request.modules})
        base["remediation_inserted"] = False

        if remediation_before and remediation_before in VALID_MODULE_KEYS:
            base = _insert_remediation_step(base, remediation_before, request)

        try:
            messages = self.build_messages(
                profile_block=profile_block, request=request, ordered_keys=base["ordered_keys"]
            )
            raw = await chat_completion(
                messages, temperature=self.temperature(), max_tokens=self.max_tokens()
            )
            llm = _parse_plan_json(raw)
            base["summary"] = str(llm.get("summary") or base["summary"]).strip()
            base["rationale"] = str(llm.get("rationale") or base["rationale"]).strip()
            nk = llm.get("next_module_key")
            if nk in VALID_MODULE_KEYS:
                base["next_module_key"] = nk
            for step in base["steps"]:
                item = next(
                    (s for s in llm.get("steps") or [] if s.get("module_key") == step["module_key"]),
                    None,
                )
                if item and item.get("reason"):
                    step["reason"] = str(item["reason"]).strip()[:40]
        except Exception:
            pass
        return base

    def plan_remediation_for_struggle(
        self,
        *,
        knowledge_point: str,
        module_key: str,
        error_pattern: str,
    ) -> dict[str, str]:
        spec = lookup_remediation(knowledge_point, module_key)
        reason = spec["reason"]
        if error_pattern:
            reason = f"{reason}（{error_pattern}）"
        return {**spec, "reason": reason}


def _parse_plan_json(raw: str) -> dict:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no json")
    return json.loads(text[start : end + 1])


def _topo_sort_keys(keys: list[str]) -> list[str]:
    """拓扑排序，保证依赖模块在前。"""
    keys_set = set(keys)
    indeg = {k: 0 for k in keys}
    adj: dict[str, list[str]] = {k: [] for k in keys}
    for k in keys:
        for dep in MODULE_DEPENDENCIES.get(k, []):
            if dep in keys_set:
                indeg[k] += 1
                adj[dep].append(k)
    queue = [k for k in keys if indeg[k] == 0]
    queue.sort(key=lambda x: DEFAULT_ORDER.index(x) if x in DEFAULT_ORDER else 99)
    out: list[str] = []
    while queue:
        n = queue.pop(0)
        out.append(n)
        for nxt in adj.get(n, []):
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                queue.append(nxt)
        queue.sort(key=lambda x: DEFAULT_ORDER.index(x) if x in DEFAULT_ORDER else 99)
    for k in keys:
        if k not in out:
            out.append(k)
    return out


def _insert_remediation_step(
    plan: dict,
    remediation_key: str,
    request: LearningPathReplanRequest,
) -> dict:
    """在 next_module 之前插入降级巩固节点。"""
    ordered = list(plan["ordered_keys"])
    if remediation_key not in ordered:
        ordered.insert(0, remediation_key)
    else:
        ordered = [remediation_key] + [k for k in ordered if k != remediation_key]

    spec = lookup_remediation("", remediation_key)
    steps = _rebuild_steps(ordered, plan["steps"], request, {}, remediation_key=remediation_key)
    for step in steps:
        if step["module_key"] == remediation_key:
            step["is_remediation"] = True
            step["reason"] = spec.get("reason", step["reason"])
            step["difficulty"] = "入门"

    plan["ordered_keys"] = ordered
    plan["steps"] = steps
    plan["next_module_key"] = remediation_key
    plan["remediation_inserted"] = True
    plan["summary"] = f"学情自适应：已插入「{spec.get('label', remediation_key)}」巩固关卡"
    return plan


def _rebuild_steps(
    ordered: list[str],
    old_steps: list[dict],
    request: LearningPathReplanRequest,
    scores: dict[str, int],
    *,
    remediation_key: str | None = None,
) -> list[dict]:
    progress_map = {m.key: m for m in request.modules}
    old_map = {s["module_key"]: s for s in old_steps}
    steps = []
    for i, key in enumerate(ordered, start=1):
        prev = old_map.get(key, {})
        m = progress_map.get(key)
        phase = prev.get("phase") or (m.phase if m else "")
        for c in MODULE_CATALOG:
            if c["key"] == key:
                phase = phase or c["phase"]
                break
        prereqs = [d for d in MODULE_DEPENDENCIES.get(key, []) if d in ordered[: i - 1]]
        steps.append(
            {
                "module_key": key,
                "rank": i,
                "reason": prev.get("reason") or _default_reason(key, m),
                "phase": phase,
                "prerequisites": prereqs,
                "difficulty": _difficulty_label(key, scores, remediation_key == key),
                "is_remediation": remediation_key == key,
            }
        )
    return steps


def _difficulty_label(module_key: str, scores: dict[str, int], is_remediation: bool) -> str:
    if is_remediation:
        return "入门"
    kb = scores.get("knowledge_base", 5)
    coding = scores.get("coding_ability", 5)
    phase = next((c["phase"] for c in MODULE_CATALOG if c["key"] == module_key), "foundation")
    avg = (kb + coding) / 2
    if phase == "foundation" and avg < 5:
        return "入门"
    if phase == "advanced" and avg >= 7:
        return "进阶"
    if avg >= 8 and phase != "foundation":
        return "进阶"
    if avg <= 4:
        return "入门"
    return "标准"


def _extract_weak_keys(profile_block: str) -> set[str]:
    keys: set[str] = set()
    for c in MODULE_CATALOG:
        if c["key"] in profile_block or c["label"] in profile_block:
            keys.add(c["key"])
    return keys


def _module_cluster_map() -> dict[str, str]:
    """module_key -> 知识簇 id（概念图社区发现）。"""
    clusters = concept_clusters()
    try:
        import json
        from pathlib import Path

        path = Path(__file__).resolve().parents[2] / "knowledge_base" / "concept_graph.json"
        graph = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    except Exception:
        return {}
    out: dict[str, str] = {}
    for c in graph.get("concepts") or []:
        mk, cid = c.get("module_key"), c.get("id")
        if mk and cid and mk not in out:
            out[str(mk)] = clusters.get(str(cid), "")
    return out


def _heuristic_plan(
    profile_block: str,
    request: LearningPathReplanRequest,
    scores: dict[str, int],
) -> dict:
    progress_map = {m.key: m for m in request.modules}
    weak_keys = _extract_weak_keys(profile_block)
    kb = scores.get("knowledge_base", 5)
    coding = scores.get("coding_ability", 5)
    beginner_mode = kb <= 4 or coding <= 4
    advanced_mode = kb >= 8 and coding >= 7
    module_clusters = _module_cluster_map()
    weak_clusters = {module_clusters.get(wk, "") for wk in weak_keys} - {""}

    def score(key: str) -> tuple[int, int, int, int, int]:
        m = progress_map.get(key)
        pct = m.percent if m else 0
        phase_rank = PHASE_RANK.get(
            next((c["phase"] for c in MODULE_CATALOG if c["key"] == key), ""), 9
        )
        weak_bonus = 0 if key in weak_keys else 1
        cluster_bonus = 0 if module_clusters.get(key, "") in weak_clusters else 1
        if pct >= 100:
            return (3, 100, phase_rank, DEFAULT_ORDER.index(key), cluster_bonus)
        if pct > 0:
            return (0, pct, phase_rank * 10 + weak_bonus, DEFAULT_ORDER.index(key), cluster_bonus)
        if beginner_mode and phase_rank > 1:
            return (2, 80, phase_rank + 5, DEFAULT_ORDER.index(key), cluster_bonus)
        if advanced_mode and phase_rank == 0 and key in ("array", "linked-list"):
            return (2, 30, phase_rank, DEFAULT_ORDER.index(key), cluster_bonus)
        return (1, 50 + (0 if key in weak_keys else 20), phase_rank, DEFAULT_ORDER.index(key), cluster_bonus)

    ordered = sorted(
        [k for k in DEFAULT_ORDER if k in VALID_MODULE_KEYS],
        key=score,
    )
    ordered = _topo_sort_keys(ordered)
    steps = []
    for i, key in enumerate(ordered, start=1):
        m = progress_map.get(key)
        steps.append(
            {
                "module_key": key,
                "rank": i,
                "reason": _default_reason(key, m, beginner_mode, advanced_mode),
                "phase": next((c["phase"] for c in MODULE_CATALOG if c["key"] == key), ""),
                "prerequisites": MODULE_DEPENDENCIES.get(key, []),
                "difficulty": _difficulty_label(key, scores, False),
                "is_remediation": False,
            }
        )

    rationale = "已用拓扑排序保证先修关系；"
    if beginner_mode:
        rationale += "检测到知识基础/代码能力偏弱，优先夯实基础模块。"
    elif advanced_mode:
        rationale += "检测到基础扎实，基础模块后置，优先进阶与薄弱点。"
    else:
        rationale += "优先未完成且与薄弱点匹配的模块。"

    return {
        "summary": "基于六维画像分数与模块依赖 DAG 的千人千面路径",
        "rationale": rationale,
        "next_module_key": _pick_next(ordered, progress_map),
        "ordered_keys": ordered,
        "steps": steps,
        "remediation_inserted": False,
    }


def _default_reason(
    key: str,
    m: ModuleProgressInput | None,
    beginner: bool = False,
    advanced: bool = False,
) -> str:
    if m and m.percent >= 100:
        return "已完成，可复习巩固"
    if m and m.percent > 0:
        return "进行中，建议优先推进"
    if key == "graph":
        return "课程规划中"
    if beginner and key in ("array", "linked-list", "stack-queue"):
        return "基础薄弱，优先夯实"
    if advanced and key in ("array", "linked-list"):
        return "基础已扎实，可快速回顾"
    return "匹配学习目标与薄弱点"


def _pick_next(ordered: list[str], progress_map: dict[str, ModuleProgressInput]) -> str | None:
    """难度平滑：同阶段优先，避免跨阶段跃迁。"""
    last_phase: str | None = None
    for key in ordered:
        m = progress_map.get(key)
        if not m or not m.available:
            continue
        if m.percent >= 100:
            last_phase = m.phase or last_phase
            continue
        phase = m.phase or next((c["phase"] for c in MODULE_CATALOG if c["key"] == key), "")
        if last_phase and PHASE_RANK.get(phase, 0) - PHASE_RANK.get(last_phase, 0) > 1:
            continue
        return key
    for key in ordered:
        m = progress_map.get(key)
        if m and m.available and m.percent < 100:
            return key
    for key in ordered:
        m = progress_map.get(key)
        if m and m.available:
            return key
    return ordered[0] if ordered else None
