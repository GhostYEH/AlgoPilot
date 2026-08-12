"""无 LLM Key 或 LLM 不可用时的画像对话模板降级（TemplatePersonaFallbackAgent）。"""

from __future__ import annotations

import asyncio
import re
from collections.abc import AsyncIterator
from typing import Any

from schemas.persona import (
    PROFILE_DIMENSION_KEYS,
    ChatHistoryItem,
    LearningEvidenceBrief,
    PersonaDimensions,
)
from services.agents.persona import (
    _DIMENSION_LABELS,
    _infer_score_from_text,
    _is_empty,
    _merge_incremental,
    _missing_dimension_keys,
)

GENERATED_BY = "TemplatePersonaFallbackAgent"
FALLBACK_REASON_DEFAULT = "LLM key missing or provider unavailable"

_DISCLAIMER = (
    "> ⚠️ **离线画像引导模式**（TemplatePersonaFallbackAgent）\n"
    "> 当前未连接大模型或模型暂不可用；以下为**规则模板追问**，非 AI 深度分析。\n"
    "> 配置 `SPARK_API_PASSWORD` 后可启用 ProfilingAgent 流式对话。\n\n"
)

_QUESTIONS: dict[str, str] = {
    "knowledge_base": (
        "你目前学过哪些数据结构或编程课？对**数组、链表、栈队列、树**等熟悉到什么程度？"
    ),
    "cognitive_style": "你更喜欢**看图示/动画**学习，还是**读文字讲义**、自己动手写代码？",
    "coding_ability": "你能**独立写完一道 OJ 题**并调试通过吗？大概什么难度（入门/中等）？",
    "learning_goals": "你的**学习目标**是什么？课内及格、蓝桥杯、考研还是就业面试？",
    "error_preference": "做题时最怕哪类错误？**边界、指针、递归**还是 **DP 状态设计**？",
    "grit_level": "遇到连续 **WA 或 TLE** 时，你一般会坚持多久？会不会主动求助或看题解？",
}

_KEYWORD_RULES: dict[str, list[tuple[str, str]]] = {
    "knowledge_base": [
        (r"大一|大二|大三|大四|计科|计算机", "年级/专业：计算机相关专业"),
        (r"零基础|没学过|初学|入门|刚开始", "知识基础偏弱，处于入门阶段"),
        (r"数据结构|链表|数组|栈|队列|树|图|哈希", "已接触基础数据结构相关内容"),
        (r"C语言|Python|Java|编程课", "有编程语言或课内编程基础"),
        (r"扎实|熟练|学过|掌握", "具备一定课内知识基础"),
    ],
    "cognitive_style": [
        (r"视觉|看图|动画|图示|思维导图", "偏好视觉型学习材料"),
        (r"文字|阅读|讲义|文档", "偏好文本阅读型学习"),
        (r"动手|写代码|实操|练习", "偏好动手实践型学习"),
    ],
    "coding_ability": [
        (r"不会写|写不出|零基础|刚开始刷题", "代码实操能力仍在建立中"),
        (r"能写|独立|AC|通过|调试", "具备一定独立编码与调试能力"),
        (r"OJ|刷题|LeetCode|力扣|蓝桥|洛谷", "有在线评测或刷题实践"),
        (r"WA|TLE|RE|编译错误", "有 OJ 实战与排错经验"),
    ],
    "learning_goals": [
        (r"考研|保研|升学", "学习目标含升学导向"),
        (r"就业|面试|实习|找工作", "学习目标含就业面试导向"),
        (r"蓝桥|ACM|竞赛|比赛", "学习目标含算法竞赛"),
        (r"课内|及格|考试|期末", "学习目标以课内通过为主"),
    ],
    "error_preference": [
        (r"边界|越界|下标|空指针|空结点", "易错点偏边界与指针"),
        (r"递归|栈溢出|基线|终止", "易错点偏递归与基线条件"),
        (r"动态规划|DP|状态转移|初始化", "易错点偏 DP 状态设计"),
        (r"指针|next|null|链表", "易错点偏指针移动"),
        (r"死循环|复杂度|TLE|超时", "易错点偏复杂度与循环收敛"),
    ],
    "grit_level": [
        (r"坚持|不放弃|再试|韧性|抗挫", "受挫后倾向坚持尝试"),
        (r"放弃|求助|问老师|看题解|很快", "受挫后倾向及时求助"),
        (r"连续.*WA|多次.*失败|受挫", "对连续失败有明确体验"),
    ],
}


def persona_fallback_meta(reason: str | None = None) -> dict[str, Any]:
    return {
        "fallback": True,
        "fallback_reason": reason or FALLBACK_REASON_DEFAULT,
        "generated_by": GENERATED_BY,
    }


def should_use_persona_fallback() -> bool:
    from core.config import settings

    return not settings.llm_configured


def _collect_user_text(history: list[ChatHistoryItem], message: str = "") -> str:
    parts = [h.content for h in history if h.role == "user"]
    if message:
        parts.append(message)
    return "\n".join(parts)


def _match_dimension(text: str, dim: str) -> tuple[str, list[str]]:
    hits: list[str] = []
    summary_parts: list[str] = []
    for pattern, phrase in _KEYWORD_RULES.get(dim, []):
        if re.search(pattern, text, re.IGNORECASE):
            hits.append(phrase)
            if phrase not in summary_parts:
                summary_parts.append(phrase)
    if not summary_parts:
        return "", []
    value = "；".join(summary_parts[:3])
    return value, hits


def _extract_dims_from_text(
    text: str,
    *,
    existing: PersonaDimensions | None,
    existing_confidence: dict[str, str] | None,
) -> tuple[PersonaDimensions, dict[str, str], dict[str, list[str]]]:
    extracted = PersonaDimensions()
    confidence: dict[str, str] = {}
    evidence: dict[str, list[str]] = {k: [] for k in PROFILE_DIMENSION_KEYS}

    for dim in PROFILE_DIMENSION_KEYS:
        value, hits = _match_dimension(text, dim)
        if value:
            setattr(extracted, dim, value)
            confidence[dim] = "explicit"
            evidence[dim] = hits[:3]

    merged, conf = _merge_incremental(extracted, confidence, existing, existing_confidence)
    return merged, conf, evidence


def _build_reply(
    *,
    message: str,
    history: list[ChatHistoryItem],
    existing_dims: PersonaDimensions | None,
) -> str:
    dims = existing_dims or PersonaDimensions()
    text = _collect_user_text(history, message)
    interim, _, _ = _extract_dims_from_text(text, existing=dims, existing_confidence=None)
    missing = _missing_dimension_keys(interim if any(not _is_empty(getattr(interim, k)) for k in PROFILE_DIMENSION_KEYS) else dims)
    if not missing and existing_dims:
        missing = _missing_dimension_keys(existing_dims)
    if not missing:
        missing = _missing_dimension_keys(interim)

    target = missing[0] if missing else "learning_goals"
    question = _QUESTIONS.get(target, _QUESTIONS["learning_goals"])
    ack = ""
    if message.strip():
        ack = f"收到：「{message.strip()[:60]}{'…' if len(message.strip()) > 60 else ''}」。\n\n"

    filled_labels = [
        _DIMENSION_LABELS[k]
        for k in PROFILE_DIMENSION_KEYS
        if not _is_empty(getattr(interim, k, ""))
    ]
    progress = ""
    if filled_labels:
        progress = f"已记录维度：{'、'.join(filled_labels[:4])}。\n\n"

    return (
        _DISCLAIMER
        + ack
        + progress
        + f"**{_DIMENSION_LABELS.get(target, '学习画像')}**\n\n"
        + question
        + "\n\n💡 请尽量用具体例子描述（学过章节、刷题平台、常错题型），便于离线规则抽取六维画像。"
    )


async def stream_persona_fallback_reply(
    *,
    message: str,
    history: list[ChatHistoryItem],
    existing_dims: PersonaDimensions | None = None,
    chunk_size: int = 28,
) -> AsyncIterator[str]:
    reply = _build_reply(message=message, history=history, existing_dims=existing_dims)
    for i in range(0, len(reply), chunk_size):
        yield reply[i : i + chunk_size]
        await asyncio.sleep(0)


def extract_persona_fallback(
    history: list[ChatHistoryItem],
    *,
    existing: PersonaDimensions | None = None,
    existing_confidence: dict[str, str] | None = None,
) -> tuple[str, PersonaDimensions, dict[str, str], list[str], dict[str, int], dict[str, list[str]], str, list[LearningEvidenceBrief]]:
    text = _collect_user_text(history)
    dims, confidence, dim_evidence = _extract_dims_from_text(
        text, existing=existing, existing_confidence=existing_confidence
    )
    missing = _missing_dimension_keys(dims)
    scores = {k: _infer_score_from_text(getattr(dims, k, "")) for k in PROFILE_DIMENSION_KEYS}

    filled = [_DIMENSION_LABELS[k] for k in PROFILE_DIMENSION_KEYS if not _is_empty(getattr(dims, k))]
    if filled:
        summary = f"离线画像：已根据对话关键词归纳 { '、'.join(filled[:4]) }"
    else:
        summary = "离线画像：待补充，请继续对话描述学习背景与目标"

    update_reason = (
        f"离线规则抽取（{GENERATED_BY}）：根据对话关键词更新六维画像"
        + (f"，待补全 { '、'.join(_DIMENSION_LABELS[k] for k in missing) }" if missing else "")
    )

    recent: list[LearningEvidenceBrief] = []
    for i, item in enumerate([h for h in history if h.role == "user"][-3:]):
        snippet = item.content.strip()[:160]
        if not snippet:
            continue
        recent.append(
            LearningEvidenceBrief(
                id=-(i + 1),
                event_type="persona_chat",
                event_label="对话摘录",
                summary=snippet,
            )
        )

    return summary, dims, confidence, missing, scores, dim_evidence, update_reason, recent
