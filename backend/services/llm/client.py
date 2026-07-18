"""讯飞星火 Spark Chat Completions（OpenAI 兼容，流式 / 非流式）。"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx
from fastapi import HTTPException, status

from core.config import settings


def _ensure_configured() -> None:
    if not settings.llm_configured:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "AI 未配置：请在 backend/.env 中设置 SPARK_API_PASSWORD（讯飞星火）",
        )


def _raise_spark_error(data: dict[str, Any], http_status: int = 502) -> None:
    err = data.get("error")
    if isinstance(err, dict):
        msg = err.get("message") or err.get("type") or "AI 服务错误"
        raise HTTPException(http_status, f"星火 API：{msg}")
    code = data.get("code")
    if code is not None and code != 0:
        msg = data.get("message") or f"错误码 {code}"
        raise HTTPException(http_status, f"星火 API：{msg}")


def _extract_reply(data: dict[str, Any]) -> str:
    _raise_spark_error(data)
    try:
        reply = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "星火返回格式异常"
        ) from exc
    if not reply or not str(reply).strip():
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "星火返回内容为空"
        )
    return str(reply).strip()


def _extract_stream_delta(data: dict[str, Any]) -> str:
    _raise_spark_error(data)
    try:
        return str(data["choices"][0]["delta"].get("content") or "")
    except (KeyError, IndexError, TypeError):
        return ""


def _prepare_messages(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    """Spark Lite 不稳定支持 system role，将系统约束合并进首条 user 消息。"""
    if settings.spark_model.lower() != "lite":
        return messages
    system_parts = [m.get("content", "").strip() for m in messages if m.get("role") == "system"]
    if not system_parts:
        return messages
    instruction = "\n\n".join(part for part in system_parts if part)
    prepared: list[dict[str, str]] = []
    injected = False
    for message in messages:
        if message.get("role") == "system":
            continue
        item = dict(message)
        if not injected and item.get("role") == "user":
            item["content"] = f"【必须遵守的任务规则】\n{instruction}\n\n【待分析内容】\n{item.get('content', '')}"
            injected = True
        prepared.append(item)
    if not injected:
        prepared.insert(0, {"role": "user", "content": instruction})
    return prepared


async def chat_completion(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.65,
    max_tokens: int = 2048,
    json_mode: bool = False,
) -> str:
    _ensure_configured()
    payload = {
        "model": settings.spark_model,
        "messages": _prepare_messages(messages),
        "temperature": temperature,
        "max_tokens": min(max_tokens, settings.spark_max_tokens_limit),
        "stream": False,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    try:
        async with httpx.AsyncClient(timeout=settings.spark_timeout) as client:
            resp = await client.post(settings.spark_chat_url, json=payload, headers=_headers())
    except httpx.TimeoutException:
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, "AI 响应超时，请稍后重试") from None
    except httpx.HTTPError as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, f"无法连接星火服务：{exc}"
        ) from exc

    if resp.status_code != 200:
        detail = resp.text[:500] if resp.text else resp.reason_phrase
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            f"星火服务返回错误（{resp.status_code}）：{detail}",
        )

    try:
        data = resp.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "星火返回非 JSON 响应"
        ) from exc

    return _extract_reply(data)


async def chat_completion_stream(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.65,
    max_tokens: int = 2048,
) -> AsyncIterator[str]:
    """逐段产出文本 delta。"""
    _ensure_configured()
    payload = {
        "model": settings.spark_model,
        "messages": _prepare_messages(messages),
        "temperature": temperature,
        "max_tokens": min(max_tokens, settings.spark_max_tokens_limit),
        "stream": True,
    }
    has_content = False
    try:
        async with httpx.AsyncClient(timeout=settings.spark_stream_timeout) as client:
            async with client.stream(
                "POST",
                settings.spark_chat_url,
                json=payload,
                headers=_headers(),
            ) as resp:
                if resp.status_code != 200:
                    body = (await resp.aread()).decode("utf-8", errors="replace")[:500]
                    raise HTTPException(
                        status.HTTP_502_BAD_GATEWAY,
                        f"星火服务返回错误（{resp.status_code}）：{body}",
                    )
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    chunk = line[5:].strip()
                    if not chunk or chunk == "[DONE]":
                        break
                    try:
                        data = json.loads(chunk)
                    except json.JSONDecodeError:
                        continue
                    delta = _extract_stream_delta(data)
                    if delta:
                        has_content = True
                        yield delta
    except httpx.TimeoutException:
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, "AI 响应超时，请稍后重试") from None
    except httpx.HTTPError as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, f"无法连接星火服务：{exc}"
        ) from exc

    if not has_content:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "星火返回内容为空")


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.spark_api_password}",
        "Content-Type": "application/json",
    }
