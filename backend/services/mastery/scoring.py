"""掌握度可解释评分：六维加权合成。"""

from __future__ import annotations

from services.mastery.models import (
    MasteryComponentScore,
    MasteryEvidenceItem,
    MasterySignals,
    mastery_level_from_score,
)

COMPONENT_WEIGHTS: dict[str, tuple[float, str]] = {
    "exercise_accuracy": (0.30, "练习测验正确率"),
    "oj_accept_rate": (0.25, "OJ 通过率"),
    "recent_error_reduction": (0.15, "近期错因改善"),
    "resource_completion": (0.15, "资源学习完成度"),
    "trace_debugging_improvement": (0.10, "Trace 调试改善"),
    "self_report_confidence": (0.05, "自陈学习信心"),
}

DEFAULT_SCORE = 50.0


def _comp(key: str, score: float, note: str, available: bool) -> MasteryComponentScore:
    weight, label = COMPONENT_WEIGHTS[key]
    return MasteryComponentScore(
        key=key,
        label=label,
        score=round(score, 1),
        weight=weight,
        weighted=round(score * weight, 2),
        data_available=available,
        note=note,
    )


def compute_component_scores(signals: MasterySignals) -> list[MasteryComponentScore]:
    components: list[MasteryComponentScore] = []

    # 练习测验正确率
    if signals.quiz_total > 0:
        acc = min(100.0, max(0.0, signals.quiz_correct / signals.quiz_total * 100))
        note = f"测验 {signals.quiz_correct}/{signals.quiz_total} 题正确"
        available = True
    elif signals.module_percents:
        vals = list(signals.module_percents.values())
        acc = sum(vals) / len(vals)
        note = f"以模块进度 {vals} 估算练习完成度"
        available = True
    else:
        acc = DEFAULT_SCORE
        note = "暂无测验记录，使用默认中间值 50"
        available = False
    components.append(_comp("exercise_accuracy", acc, note, available))

    # OJ 通过率
    if signals.oj_failures > 0:
        penalty = min(90, signals.oj_failures * 22)
        oj_rate = max(5.0, 100.0 - penalty)
        note = f"近期 OJ 未通过 {signals.oj_failures} 次，通过率估算 {oj_rate:.0f}"
        available = True
    elif signals.resource_completions > 0 and signals.memory_event_count > 0:
        oj_rate = 72.0
        note = "暂无 OJ 失败记录且有学习完成行为，给予偏上估算 72"
        available = True
    else:
        oj_rate = DEFAULT_SCORE
        note = "暂无 OJ 提交记录，使用默认中间值 50"
        available = False
    if signals.positive_deltas > signals.oj_failures and signals.oj_failures == 0:
        oj_rate = min(100.0, oj_rate + signals.positive_deltas * 5)
        note += "；正向学习事件提升 OJ 估算"
    components.append(_comp("oj_accept_rate", oj_rate, note, available))

    # 近期错因改善
    recent = len(set(signals.recent_fail_patterns))
    older = len(set(signals.older_fail_patterns))
    if recent == 0 and older == 0:
        err_red = DEFAULT_SCORE
        note = "暂无错因记忆对比，使用默认中间值 50"
        available = False
    elif older == 0:
        err_red = max(30.0, 70.0 - recent * 12)
        note = f"近期出现 {recent} 类错因模式"
        available = True
    else:
        improvement = max(0, older - recent)
        err_red = min(100.0, 50.0 + improvement * 15 - recent * 8)
        note = f"近期错因 {recent} 类 vs 较早 {older} 类"
        available = True
    if signals.struggle_events >= 2:
        err_red = max(10.0, err_red - signals.struggle_events * 10)
        note += f"；连续受挫 {signals.struggle_events} 次"
    components.append(_comp("recent_error_reduction", err_red, note, available))

    # 资源完成度
    done = signals.resource_completions + signals.section_completions
    if done > 0:
        res_comp = min(100.0, 40.0 + done * 18)
        note = f"资源/小节完成 {done} 次"
        available = True
    elif signals.module_percents:
        res_comp = sum(signals.module_percents.values()) / len(signals.module_percents)
        note = "以模块进度估算资源完成度"
        available = True
    else:
        res_comp = DEFAULT_SCORE
        note = "暂无资源完成记录，使用默认中间值 50"
        available = False
    components.append(_comp("resource_completion", res_comp, note, available))

    # Trace 调试改善
    if signals.oj_diagnoses > 0:
        trace = min(100.0, 35.0 + signals.oj_diagnoses * 15 + signals.trace_with_hints * 10)
        note = f"AI/Trace 诊断 {signals.oj_diagnoses} 次"
        if signals.trace_with_hints:
            note += f"，有效提示 {signals.trace_with_hints} 条"
        available = True
    else:
        trace = DEFAULT_SCORE
        note = "暂无 Trace 诊断记录，使用默认中间值 50"
        available = False
    components.append(_comp("trace_debugging_improvement", trace, note, available))

    # 自陈信心
    if signals.self_report_score is not None:
        conf = min(100.0, max(0.0, signals.self_report_score))
        note = f"画像维度均分换算 {conf:.0f}"
        available = True
    else:
        conf = DEFAULT_SCORE
        note = "暂无画像自陈分数，使用默认中间值 50"
        available = False
    components.append(_comp("self_report_confidence", conf, note, available))

    return components


def compute_mastery_score(components: list[MasteryComponentScore]) -> int:
    total = 0.0
    for c in components:
        w = COMPONENT_WEIGHTS.get(c.key, (0.0, ""))[0]
        c.weight = w
        c.weighted = round(c.score * w, 2)
        total += c.score * w
    return max(0, min(100, round(total)))


def build_evidence_from_components(
    components: list[MasteryComponentScore],
    *,
    extra: list[MasteryEvidenceItem] | None = None,
) -> list[MasteryEvidenceItem]:
    items = list(extra or [])
    for c in components:
        items.append(
            MasteryEvidenceItem(
                source=c.key,
                detail=f"{c.label}={c.score:.0f}（权重 {int(c.weight * 100)}%）：{c.note}",
            )
        )
    return items


def resolve_weak_strong_skills(
    signals: MasterySignals,
    *,
    skill_name_map: dict[str, str] | None = None,
) -> tuple[list[str], list[str]]:
    names = skill_name_map or {}
    weak: list[tuple[int, str]] = []
    strong: list[tuple[int, str]] = []
    for sid, cnt in signals.skill_fail_counts.items():
        if cnt > 0:
            weak.append((cnt, names.get(sid, sid)))
    for sid, cnt in signals.skill_success_counts.items():
        if cnt > 0:
            strong.append((cnt, names.get(sid, sid)))
    weak.sort(key=lambda x: -x[0])
    strong.sort(key=lambda x: -x[0])
    return [label for _, label in weak[:5]], [label for _, label in strong[:5]]


def score_to_level(score: int) -> str:
    return mastery_level_from_score(score)
