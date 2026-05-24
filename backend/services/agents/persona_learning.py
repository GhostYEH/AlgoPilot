"""随学随新：根据学习行为轻量更新六维画像。"""

from __future__ import annotations

from schemas.evaluation import PersonaLearningPatchRequest
from schemas.persona import PersonaDimensions
from services.agents.learning_path_catalog import MODULE_CATALOG

_MODULE_LABELS = {m["key"]: m["label"] for m in MODULE_CATALOG}


def apply_learning_patch(
    summary: str,
    dimensions: PersonaDimensions,
    body: PersonaLearningPatchRequest,
) -> tuple[str, PersonaDimensions]:
    dims = dimensions.model_dump()
    weak_keys = list(dict.fromkeys(body.weak_module_keys))[:8]
    weak_labels = [_MODULE_LABELS.get(k, k) for k in weak_keys if k]

    if weak_labels:
        dims["error_preference"] = f"近期易错/待加强：{'、'.join(weak_labels)}"
    elif body.signals:
        visited = list(dict.fromkeys(s.module_key for s in body.signals if s.module_key))[:5]
        if visited:
            prev = dims.get("error_preference") or "待补充"
            suffix = f"近期学习模块：{'、'.join(_MODULE_LABELS.get(k, k) for k in visited)}"
            dims["error_preference"] = suffix if _is_pending(prev) else f"{prev}；{suffix}"

    done_modules = [s for s in body.signals if s.event_type == "section_done" and s.module_key]
    if done_modules:
        labels = [_MODULE_LABELS.get(s.module_key, s.module_key) for s in done_modules[-5:]]
        prev = dims.get("knowledge_base") or "待补充"
        if _is_pending(prev):
            dims["knowledge_base"] = f"已完成小节：{'、'.join(labels)}"
        elif not any(l in prev for l in labels):
            dims["knowledge_base"] = f"{prev}；近期完成：{'、'.join(labels[-3:])}"

    oj_events = [s for s in body.signals if s.event_type == "oj_submit"]
    if oj_events:
        prev = dims.get("coding_ability") or "待补充"
        patch = "含 OJ 刷题实践，代码实操能力随练习提升"
        dims["coding_ability"] = patch if _is_pending(prev) else f"{prev}；{patch}"
        wa_count = sum(1 for e in oj_events if getattr(e, "verdict", "") in ("WA", "RE", "TLE"))
        if wa_count >= 2:
            grit_prev = dims.get("grit_level") or "待补充"
            grit_patch = "多次提交未过仍继续尝试，抗挫折能力中等偏上"
            dims["grit_level"] = grit_patch if _is_pending(grit_prev) else f"{grit_prev}；{grit_patch}"

    new_summary = summary
    if weak_labels:
        new_summary = f"计科算法学习者，当前需加强 {'、'.join(weak_labels[:3])}。"
    elif done_modules and (not summary or summary == "画像待完善"):
        new_summary = "已通过平台学习数据结构与算法相关模块，画像随学更新中。"

    return new_summary.strip() or summary, PersonaDimensions.model_validate(dims)


def _is_pending(val: str) -> bool:
    v = (val or "").strip()
    return not v or v in ("待补充", "暂无", "未知")
