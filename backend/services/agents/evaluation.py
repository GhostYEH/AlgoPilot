"""学习效果评估 Agent：掌握度加权 + 历史快照对比。"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from schemas.evaluation import EvaluationDimensionScore, LearningEvaluationResponse
from schemas.learning_path import LearningPathReplanRequest, ModuleProgressInput
from services.llm import chat_completion

_EVAL_SYSTEM = """你是「学习效果评估 Agent」。根据学生学习进度与画像，输出简短诊断。
输出唯一 JSON（不要 markdown 代码块）：
{
  "narrative": "80～150字总体评价与建议",
  "push_strategy": "一句话说明资源推送策略调整建议",
  "suggestions": ["建议1", "建议2"]
}"""


class EvaluationAgent:
    name = "EvaluationAgent"
    role = "学习效果评估"

    async def evaluate(
        self,
        *,
        profile_summary: str,
        profile_block: str,
        request: LearningPathReplanRequest,
        resources_count: int,
        recent_resource_types: list[str],
        prior_snapshot: dict | None = None,
    ) -> LearningEvaluationResponse:
        modules = request.modules
        tracked = [m for m in modules if m.total_count > 0 or m.percent > 0]
        completed = [m for m in modules if m.percent >= 100]
        weak = sorted(
            [m for m in modules if m.available and 0 < m.percent < 60],
            key=lambda x: x.percent,
        )[:5]
        stagnant = [m for m in modules if m.available and m.percent == 0 and m.total_count > 0]

        overall = request.overall_percent
        mastery = _mastery_score(modules, completed, weak)
        consistency = _consistency_score(tracked, modules)
        practice = _practice_score(modules, resources_count)
        resource_usage = min(100, resources_count * 10 + len(set(recent_resource_types)) * 12)

        dimensions = [
            EvaluationDimensionScore(key="mastery", label="知识掌握", score=mastery),
            EvaluationDimensionScore(key="consistency", label="学习持续性", score=consistency),
            EvaluationDimensionScore(key="practice", label="练习完成度", score=practice),
            EvaluationDimensionScore(
                key="resource_usage", label="资源利用", score=resource_usage
            ),
        ]
        overall_score = round(sum(d.score for d in dimensions) / len(dimensions))

        narrative, push_strategy, llm_suggestions = await self._llm_insight(
            profile_summary=profile_summary,
            profile_block=profile_block,
            overall_percent=overall,
            weak_labels=[m.label for m in weak],
            completed_count=len(completed),
            resources_count=resources_count,
            mastery=mastery,
            prior=prior_snapshot,
        )

        suggestions = list(llm_suggestions) if llm_suggestions else []
        if not suggestions:
            suggestions = _rule_suggestions(weak, stagnant, resources_count, overall)

        trend = _compute_trend(overall_score, prior_snapshot)
        if trend:
            suggestions.insert(0, trend)

        return LearningEvaluationResponse(
            agent_name=self.name,
            overall_score=overall_score,
            dimensions=dimensions,
            weak_module_keys=[m.key for m in weak],
            suggestions=suggestions,
            narrative=narrative,
            push_strategy=push_strategy,
        )

    def build_snapshot(self, response: LearningEvaluationResponse) -> dict:
        return {
            "at": datetime.now(timezone.utc).isoformat(),
            "overall_score": response.overall_score,
            "dimensions": {d.key: d.score for d in response.dimensions},
            "weak_module_keys": list(response.weak_module_keys),
        }

    async def _llm_insight(
        self,
        *,
        profile_summary: str,
        profile_block: str,
        overall_percent: int,
        weak_labels: list[str],
        completed_count: int,
        resources_count: int,
        mastery: int,
        prior: dict | None,
    ) -> tuple[str, str, list[str]]:
        user = json.dumps(
            {
                "画像摘要": profile_summary or "无",
                "画像": profile_block[:800],
                "总进度%": overall_percent,
                "薄弱模块": weak_labels,
                "已完成模块数": completed_count,
                "已生成资源数": resources_count,
                "掌握度分": mastery,
                "上次评估": prior,
            },
            ensure_ascii=False,
        )
        try:
            raw = await chat_completion(
                [{"role": "system", "content": _EVAL_SYSTEM}, {"role": "user", "content": user}],
                temperature=0.35,
                max_tokens=600,
            )
            data = _parse_json(raw)
            narrative = str(data.get("narrative", "")).strip() or _fallback_narrative(
                overall_percent, weak_labels
            )
            push = str(data.get("push_strategy", "")).strip() or "按薄弱模块优先推送题单与讲解文档"
            sugg = data.get("suggestions") or []
            llm_sugg = [str(s).strip() for s in sugg if str(s).strip()][:5]
            return narrative, push, llm_sugg
        except Exception:
            return (
                _fallback_narrative(overall_percent, weak_labels),
                "按薄弱模块优先推送题单与讲解文档",
                [],
            )

    async def evaluate_oj_struggle(
        self,
        *,
        knowledge_point: str,
        module_key: str,
        verdict: str,
        consecutive_failures: int,
        error_pattern: str,
    ) -> tuple[bool, str, str, list[dict]]:
        """
        检测 OJ 连续受挫并生成 Planner 联动信号。
        返回：(是否触发降级, 巩固模块 key, 巩固标签, agent_logs)
        """
        struggle = consecutive_failures >= 3 and verdict in ("WA", "RE", "TLE", "CE")
        logs: list[dict] = []

        if not struggle:
            logs.append(
                {
                    "agent": self.name,
                    "action": "学情监测",
                    "detail": f"连续失败 {consecutive_failures} 次（{verdict}），未达降级阈值",
                    "status": "done",
                }
            )
            return False, "", "", logs

        from services.agents.learning_path import LearningPathAgent

        path_agent = LearningPathAgent()
        spec = path_agent.plan_remediation_for_struggle(
            knowledge_point=knowledge_point,
            module_key=module_key,
            error_pattern=error_pattern,
        )
        rem_key = spec["module_key"]
        rem_label = spec["label"]
        pattern = error_pattern or verdict

        logs.append(
            {
                "agent": self.name,
                "action": "捕捉到连续受挫",
                "detail": (
                    f"连续 {consecutive_failures} 次 {verdict}"
                    f"（{knowledge_point or module_key or '当前知识点'}）"
                    f"，已通知 Planner 下调下一关难度；错误特征：{pattern}"
                ),
                "status": "warn",
            }
        )
        logs.append(
            {
                "agent": "PlannerAgent",
                "action": "接收 Evaluator 降级信号",
                "detail": f"请求在「{knowledge_point or module_key}」前插入「{rem_label}」巩固关卡",
                "status": "running",
            }
        )
        logs.append(
            {
                "agent": "PlannerAgent",
                "action": "路径已插入降级节点",
                "detail": f"下一关推荐：{rem_label}（{rem_key}）",
                "status": "done",
            }
        )
        return True, rem_key, rem_label, logs


def _mastery_score(
    modules: list[ModuleProgressInput],
    completed: list[ModuleProgressInput],
    weak: list[ModuleProgressInput],
) -> int:
    if not modules:
        return 0
    weighted = 0.0
    total_w = 0.0
    for m in modules:
        if not m.available:
            continue
        w = max(m.total_count, 1)
        pct = m.percent / 100.0
        weighted += pct * w
        total_w += w
    base = (weighted / total_w * 85) if total_w else 0
    bonus = min(15, len(completed) * 2)
    penalty = min(20, len(weak) * 4)
    return int(max(0, min(100, round(base + bonus - penalty))))


def _consistency_score(
    tracked: list[ModuleProgressInput], modules: list[ModuleProgressInput]
) -> int:
    if not tracked:
        return 30
    active = len([m for m in tracked if m.percent > 0])
    spread = len(set(m.phase for m in tracked if m.phase))
    base = min(70, 25 + active * 10)
    balance = min(20, spread * 5)
    stagnant = len([m for m in modules if m.percent == 0 and m.total_count > 0])
    return int(max(0, min(100, base + balance - stagnant * 5)))


def _practice_score(modules: list[ModuleProgressInput], resources_count: int) -> int:
    done = sum(m.done_count for m in modules)
    pct_avg = sum(m.percent for m in modules if m.available) / max(
        len([m for m in modules if m.available]), 1
    )
    return int(min(100, done * 1.5 + pct_avg * 0.4 + min(15, resources_count * 2)))


def _rule_suggestions(
    weak: list[ModuleProgressInput],
    stagnant: list[ModuleProgressInput],
    resources_count: int,
    overall: int,
) -> list[str]:
    suggestions: list[str] = []
    if weak:
        suggestions.append(f"优先巩固：{'、'.join(m.label for m in weak[:3])}")
    if stagnant:
        suggestions.append(f"长期未推进：{'、'.join(m.label for m in stagnant[:2])}")
    if resources_count < 3:
        suggestions.append("建议在资源库生成针对性题单与讲解文档")
    if overall < 20:
        suggestions.append("建议先完成基础模块并建立学习画像")
    if not suggestions:
        suggestions.append("保持当前节奏，可挑战进阶模块与 OJ 综合题")
    return suggestions


def _compute_trend(current: int, prior: dict | None) -> str:
    if not prior:
        return ""
    prev = int(prior.get("overall_score", 0))
    delta = current - prev
    if delta >= 8:
        return f"相较上次评估（{prev} 分），综合分提升 {delta} 分，进步明显。"
    if delta <= -8:
        return f"相较上次评估（{prev} 分），综合分下降 {abs(delta)} 分，建议回顾薄弱模块。"
    if delta != 0:
        return f"相较上次评估（{prev} 分），综合分变化 {delta:+d} 分。"
    return ""


def _fallback_narrative(overall_percent: int, weak_labels: list[str]) -> str:
    if overall_percent < 20:
        return "学习尚在起步阶段，建议先完成基础模块的小节与配套练习，并建立学习画像。"
    if weak_labels:
        return f"整体进度 {overall_percent}%，建议在 { '、'.join(weak_labels[:3]) } 等模块加强练习与 AI 生成资源。"
    return f"整体进度 {overall_percent}%，各模块推进较均衡，可继续按学习路径拓展进阶内容。"


def _parse_json(raw: str) -> dict:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])
    return json.loads(text)


evaluation_agent = EvaluationAgent()
