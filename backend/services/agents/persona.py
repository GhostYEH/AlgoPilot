"""画像 Agent：对话构建学习画像 + 结构化抽取（渐进确认）。"""

from __future__ import annotations

import json
import re

from schemas.persona import (
    PROFILE_DIMENSION_KEYS,
    ChatHistoryItem,
    PersonaDimensions,
)
from services.agents.base import BaseAgent
from services.llm import chat_completion

PERSONA_SYSTEM = """你是「算法智能学习平台」的**学习画像 Agent**，通过自然语言对话了解大一计科学生的学习情况。

## 任务
- 用简短、友好的中文提问或回应，逐步了解七维画像（专业背景、学习目标、认知风格、薄弱点、节奏、兴趣、偏好模态）。
- 每次回复 80～220 字，**优先追问**系统提示的「待补全维度」。
- 不要编造用户未提供的信息；可结合对话做合理归纳。
- 回复使用 Markdown（列表、加粗即可），不要输出 JSON。"""

EXTRACT_SYSTEM = """你是学习画像结构化抽取 Agent。根据对话历史，输出**唯一**一段 JSON，不要 markdown 代码块：
{
  "summary": "一句话总结",
  "dimensions": {
    "knowledge_base": "…",
    "learning_goal": "…",
    "cognitive_style": "…",
    "weak_points": "…",
    "pace_preference": "…",
    "interest_focus": "…",
    "preferred_modalities": "…"
  },
  "confidence": {
    "knowledge_base": "explicit|inferred",
    …
  }
}
explicit=用户原话明确提供；inferred=模型推断。信息不足写「待补充」。"""

_DIMENSION_LABELS = {
    "knowledge_base": "知识基础",
    "learning_goal": "学习目标",
    "cognitive_style": "认知风格",
    "weak_points": "薄弱点",
    "pace_preference": "学习节奏",
    "interest_focus": "兴趣方向",
    "preferred_modalities": "偏好模态",
}


class PersonaAgent(BaseAgent):
    name = "ProfilingAgent"
    role = "学习画像构建"

    def build_messages(
        self,
        *,
        message: str,
        history: list[ChatHistoryItem],
        profile_summary: str = "",
        existing_dims: PersonaDimensions | None = None,
    ) -> list[dict[str, str]]:
        msgs: list[dict[str, str]] = [{"role": "system", "content": PERSONA_SYSTEM}]
        if profile_summary:
            msgs.append(
                {"role": "system", "content": f"当前已保存的画像摘要：{profile_summary}"}
            )
        if existing_dims:
            missing = _missing_dimension_keys(existing_dims)
            if missing:
                labels = "、".join(_DIMENSION_LABELS[k] for k in missing)
                msgs.append(
                    {
                        "role": "system",
                        "content": f"待补全维度（请优先追问）：{labels}",
                    }
                )
            filled = [k for k in PROFILE_DIMENSION_KEYS if not _is_empty(getattr(existing_dims, k))]
            if filled:
                msgs.append(
                    {
                        "role": "system",
                        "content": "已有维度：" + "、".join(_DIMENSION_LABELS[k] for k in filled),
                    }
                )
        for item in history[-30:]:
            msgs.append({"role": item.role, "content": item.content})
        msgs.append({"role": "user", "content": message})
        return msgs

    def temperature(self) -> float:
        return 0.7

    def max_tokens(self) -> int:
        return 1024

    async def extract_dimensions(
        self,
        history: list[ChatHistoryItem],
        *,
        existing: PersonaDimensions | None = None,
        existing_confidence: dict[str, str] | None = None,
    ) -> tuple[str, PersonaDimensions, dict[str, str], list[str]]:
        convo = "\n".join(f"{h.role}: {h.content}" for h in history[-30:])
        messages = [
            {"role": "system", "content": EXTRACT_SYSTEM},
            {"role": "user", "content": f"对话记录：\n{convo}\n\n请输出 JSON。"},
        ]
        raw = await chat_completion(messages, temperature=0.2, max_tokens=1400)
        summary, dims, confidence = _parse_profile_json(raw)
        dims, confidence = _merge_incremental(dims, confidence, existing, existing_confidence)
        missing = _missing_dimension_keys(dims)
        if missing:
            followup = await _followup_extract(history, missing)
            for k, v in followup.get("dimensions", {}).items():
                if k in PROFILE_DIMENSION_KEYS and v and not _is_empty(v):
                    setattr(dims, k, v)
                    confidence[k] = followup.get("confidence", {}).get(k, "inferred")
            summary = followup.get("summary") or summary
            missing = _missing_dimension_keys(dims)
        return summary, dims, confidence, missing


async def _followup_extract(history: list[ChatHistoryItem], missing: list[str]) -> dict:
    labels = "、".join(_DIMENSION_LABELS[k] for k in missing)
    convo = "\n".join(f"{h.role}: {h.content}" for h in history[-30:])
    user = f"对话：\n{convo}\n\n请仅补全维度：{labels}。输出 JSON：{{\"dimensions\":{{...}},\"confidence\":{{...}}}}"
    raw = await chat_completion(
        [{"role": "system", "content": EXTRACT_SYSTEM}, {"role": "user", "content": user}],
        temperature=0.15,
        max_tokens=800,
    )
    try:
        _, dims, conf = _parse_profile_json(raw)
        return {
            "summary": "",
            "dimensions": dims.model_dump(),
            "confidence": conf,
        }
    except Exception:
        return {"dimensions": {}, "confidence": {}}


def _missing_dimension_keys(dims: PersonaDimensions) -> list[str]:
    return [k for k in PROFILE_DIMENSION_KEYS if _is_empty(getattr(dims, k, ""))]


def _is_empty(val: str) -> bool:
    v = (val or "").strip()
    return not v or v in ("待补充", "暂无", "未知")


def _merge_incremental(
    new: PersonaDimensions,
    confidence: dict[str, str],
    existing: PersonaDimensions | None,
    existing_confidence: dict[str, str] | None,
) -> tuple[PersonaDimensions, dict[str, str]]:
    if not existing:
        return new, confidence
    merged = existing.model_dump()
    conf = dict(existing_confidence or {})
    for k in PROFILE_DIMENSION_KEYS:
        nv = getattr(new, k, "")
        if not _is_empty(nv):
            merged[k] = nv
            conf[k] = confidence.get(k, "inferred")
    return PersonaDimensions.model_validate(merged), conf


def _parse_profile_json(raw: str) -> tuple[str, PersonaDimensions, dict[str, str]]:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            data = json.loads(text[start : end + 1])
        else:
            return "画像待完善", PersonaDimensions(), {}
    summary = str(data.get("summary", "")).strip() or "画像待完善"
    dims_raw = data.get("dimensions") or data
    dims = PersonaDimensions.model_validate(
        {k: str(dims_raw.get(k, "") or "待补充") for k in PROFILE_DIMENSION_KEYS}
    )
    conf_raw = data.get("confidence") or {}
    confidence = {
        k: str(conf_raw.get(k, "inferred") if conf_raw.get(k) else "inferred")
        for k in PROFILE_DIMENSION_KEYS
    }
    return summary, dims, confidence
