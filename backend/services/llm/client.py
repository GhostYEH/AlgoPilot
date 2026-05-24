"""硅基流动 Chat Completions（流式 / 非流式）。"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx
from fastapi import HTTPException, status

from core.config import settings

SILICONFLOW_CHAT_URL = "https://api.siliconflow.cn/v1/chat/completions"


def _ensure_configured() -> None:
    if not settings.siliconflow_api_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "AI 未配置：请在服务端 .env 中设置 SILICONFLOW_API_KEY",
        )


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.siliconflow_api_key}",
        "Content-Type": "application/json",
    }


async def chat_completion(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.65,
    max_tokens: int = 2048,
) -> str:
    _ensure_configured()
    payload = {
        "model": settings.siliconflow_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": 0.9,
        "stream": False,
    }
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(SILICONFLOW_CHAT_URL, json=payload, headers=_headers())
    except httpx.TimeoutException:
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, "AI 响应超时，请稍后重试") from None
    except httpx.HTTPError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"无法连接 AI 服务：{exc}") from exc

    if resp.status_code != 200:
        detail = resp.text[:500] if resp.text else resp.reason_phrase
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            f"AI 服务返回错误（{resp.status_code}）：{detail}",
        )

    data = resp.json()
    try:
        reply = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "AI 返回格式异常") from exc

    if not reply or not str(reply).strip():
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "AI 返回内容为空")
    return str(reply).strip()


async def chat_completion_stream(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.65,
    max_tokens: int = 2048,
) -> AsyncIterator[str]:
    """逐段产出文本 delta。"""
    _ensure_configured()
    payload = {
        "model": settings.siliconflow_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": 0.9,
        "stream": True,
    }
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST", SILICONFLOW_CHAT_URL, json=payload, headers=_headers()
            ) as resp:
                if resp.status_code != 200:
                    body = (await resp.aread()).decode("utf-8", errors="replace")[:500]
                    raise HTTPException(
                        status.HTTP_502_BAD_GATEWAY,
                        f"AI 服务返回错误（{resp.status_code}）：{body}",
                    )
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    chunk = line[5:].strip()
                    if chunk == "[DONE]":
                        break
                    try:
                        data = json.loads(chunk)
                        delta = data["choices"][0]["delta"].get("content") or ""
                    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                        continue
                    if delta:
                        yield delta
    except httpx.TimeoutException:
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, "AI 响应超时，请稍后重试") from None
    except httpx.HTTPError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"无法连接 AI 服务：{exc}") from exc
