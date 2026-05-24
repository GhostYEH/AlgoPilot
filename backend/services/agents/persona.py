"""画像 Agent：对话构建六维学习画像 + 结构化抽取。"""

from __future__ import annotations

import json
import re

from schemas.persona import (
    PROFILE_DIMENSION_KEYS,
    ChatHistoryItem,
    PersonaDimensions,
    migrate_dimension_payload,
)
from services.agents.base import BaseAgent
from services.llm import chat_completion

PERSONA_SYSTEM = """你是「算法智能学习平台」的**学习画像 Agent（ProfilingAgent）**，通过自然语言对话了解大一计科学生的学习情况。

## 任务
- 用简短、友好的中文提问或回应，逐步了解**六维画像**：
  1. knowledge_base 知识基础（已学课程、数据结构掌握程度）
  2. cognitive_style 认知风格（视觉型/文本型/动手型等）
  3. coding_ability 代码实操能力（能否独立写题、调试、复杂度分析）
  4. learning_goals 学习目标（竞赛/考研/课内/就业等）
  5. error_preference 易错点偏好（如边界、指针、递归、DP 状态等）
  6. grit_level 抗挫折心理（遇 WA/TLE 时的坚持程度与求助习惯）
- 每次回复 80～220 字，**优先追问**系统提示的「待补全维度」。
- 不要编造用户未提供的信息；可结合对话做合理归纳。
- 回复使用 Markdown（列表、加粗即可），不要输出 JSON。"""

EXTRACT_SYSTEM = """你是学习画像结构化抽取 Agent。根据对话历史，输出**唯一**一段 JSON，不要 markdown 代码块：
{
  "summary": "一句话总结",
  "dimensions": {
    "knowledge_base": "…",
    "cognitive_style": "…",
    "coding_ability": "…",
    "learning_goals": "…",
    "error_preference": "…",
    "grit_level": "…"
  },
  "scores": {
    "knowledge_base": 1-10,
    "cognitive_style": 1-10,
    "coding_ability": 1-10,
    "learning_goals": 1-10,
    "error_preference": 1-10,
    "grit_level": 1-10
  },
  "confidence": {
    "knowledge_base": "explicit|inferred",
    …
  }
}
scores 为 1-10 整数：知识/代码能力越高分越高；error_preference 表示易错程度（越高越易错）；grit_level 抗挫折越高分越高。
explicit=用户原话明确提供；inferred=模型推断。信息不足维度写「待补充」，对应 score 用 3。"""

_DIMENSION_LABELS = {
    "knowledge_base": "知识基础",
    "cognitive_style": "认知风格",
    "coding_ability": "代码实操能力",
    "learning_goals": "学习目标",
    "error_preference": "易错点偏好",
    "grit_level": "抗挫折心理能力",
}


class PersonaAgent(BaseAgent):
    name = "ProfilingAgent"
    role = "六维动态学生画像构建"

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
    ) -> tuple[str, PersonaDimensions, dict[str, str], list[str], dict[str, int]]:
        convo = "\n".join(f"{h.role}: {h.content}" for h in history[-30:])
        messages = [
            {"role": "system", "content": EXTRACT_SYSTEM},
            {"role": "user", "content": f"对话记录：\n{convo}\n\n请输出 JSON。"},
        ]
        raw = await chat_completion(messages, temperature=0.2, max_tokens=1400)
        summary, dims, confidence, scores = _parse_profile_json(raw)
        dims, confidence = _merge_incremental(dims, confidence, existing, existing_confidence)
        missing = _missing_dimension_keys(dims)
        if missing:
            followup = await _followup_extract(history, missing)
            for k, v in followup.get("dimensions", {}).items():
                if k in PROFILE_DIMENSION_KEYS and v and not _is_empty(v):
                    setattr(dims, k, v)
                    confidence[k] = followup.get("confidence", {}).get(k, "inferred")
            for k, v in followup.get("scores", {}).items():
                if k in PROFILE_DIMENSION_KEYS and isinstance(v, (int, float)):
                    scores[k] = _clamp_score(int(v))
            summary = followup.get("summary") or summary
            missing = _missing_dimension_keys(dims)
        return summary, dims, confidence, missing, scores


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
        _, dims, conf, scores = _parse_profile_json(raw)
        return {
            "summary": "",
            "dimensions": dims.model_dump(),
            "confidence": conf,
            "scores": scores,
        }
    except Exception:
        return {"dimensions": {}, "confidence": {}, "scores": {}}


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


def _clamp_score(val: int) -> int:
    return max(1, min(10, int(val)))


def _parse_profile_json(raw: str) -> tuple[str, PersonaDimensions, dict[str, str], dict[str, int]]:
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
            return "画像待完善", PersonaDimensions(), {}, _default_scores()
    summary = str(data.get("summary", "")).strip() or "画像待完善"
    dims_raw = data.get("dimensions") or data
    merged_raw = migrate_dimension_payload(
        {k: str(dims_raw.get(k, "") or "") for k in PROFILE_DIMENSION_KEYS}
        | {k: dims_raw.get(k, "") for k in dims_raw if isinstance(dims_raw, dict)}
    )
    dims = PersonaDimensions.model_validate(merged_raw)
    conf_raw = data.get("confidence") or {}
    confidence = {
        k: str(conf_raw.get(k, "inferred") if conf_raw.get(k) else "inferred")
        for k in PROFILE_DIMENSION_KEYS
    }
    scores_raw = data.get("scores") or {}
    scores = _default_scores()
    for k in PROFILE_DIMENSION_KEYS:
        if k in scores_raw and scores_raw[k] is not None:
            try:
                scores[k] = _clamp_score(int(scores_raw[k]))
            except (TypeError, ValueError):
                pass
    scores = _infer_scores_from_text(dims, scores)
    return summary, dims, confidence, scores


def _default_scores() -> dict[str, int]:
    return {k: 5 for k in PROFILE_DIMENSION_KEYS}


def _infer_scores_from_text(dims: PersonaDimensions, scores: dict[str, int]) -> dict[str, int]:
    """对 LLM 未给出分数的维度，用文本长度与关键词做启发式补全。"""
    out = dict(scores)
    for k in PROFILE_DIMENSION_KEYS:
        val = getattr(dims, k, "")
        if _is_empty(val):
            out[k] = 3
            continue
        if out.get(k, 5) != 5:
            continue
        t = val.lower()
        if any(w in t for w in ("薄弱", "不会", "零基础", "刚开始", "不太会")):
            out[k] = 4
        elif any(w in t for w in ("熟练", "扎实", "较好", "ACM", "竞赛", "刷过很多")):
            out[k] = 8
        else:
            out[k] = max(4, min(8, 4 + len(val) // 25))
    return out
