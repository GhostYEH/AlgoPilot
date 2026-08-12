"""科大讯飞在线语音合成（流式 WebAPI v2，wss://tts-api.xfyun.cn/v2/tts）。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import ssl
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time

import websocket

from core.config import settings

MAX_TTS_CHARS = 2000
_TTS_HOST = "tts-api.xfyun.cn"
_TTS_PATH = "/v2/tts"
_TTS_WSS = f"wss://{_TTS_HOST}{_TTS_PATH}"


def _build_auth_url() -> str:
    date = format_date_time(mktime(datetime.now().timetuple()))
    signature_origin = (
        f"host: {_TTS_HOST}\n"
        f"date: {date}\n"
        f"GET {_TTS_PATH} HTTP/1.1"
    )
    signature_sha = hmac.new(
        settings.iflytek_tts_api_secret.encode("utf-8"),
        signature_origin.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    signature = base64.b64encode(signature_sha).decode("utf-8")
    authorization_origin = (
        f'api_key="{settings.iflytek_tts_api_key}", algorithm="hmac-sha256", '
        f'headers="host date request-line", signature="{signature}"'
    )
    authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode("utf-8")
    query = urlencode({"authorization": authorization, "date": date, "host": _TTS_HOST})
    return f"{_TTS_WSS}?{query}"


def synthesize_speech(text: str, *, voice: str | None = None) -> bytes:
    plain = " ".join(text.split()).strip()
    if not plain:
        raise ValueError("朗读文本为空")
    if len(plain) > MAX_TTS_CHARS:
        plain = f"{plain[:MAX_TTS_CHARS]}…"

    if not settings.tts_configured:
        raise RuntimeError(
            "未配置科大讯飞 TTS：请在 backend/.env 设置 "
            "IFLYTEK_TTS_APP_ID、IFLYTEK_TTS_API_KEY、IFLYTEK_TTS_API_SECRET"
        )

    vcn = voice or settings.tts_voice
    audio_chunks: list[bytes] = []
    errors: list[str] = []

    def on_message(_ws: websocket.WebSocketApp, message: str) -> None:
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            errors.append("科大讯飞 TTS 响应解析失败")
            _ws.close()
            return

        code = payload.get("code")
        if code != 0:
            errors.append(payload.get("message") or f"科大讯飞 TTS 错误码 {code}")
            _ws.close()
            return

        data = payload.get("data") or {}
        audio_b64 = data.get("audio")
        if audio_b64:
            audio_chunks.append(base64.b64decode(audio_b64))
        if data.get("status") == 2:
            _ws.close()

    def on_error(_ws: websocket.WebSocketApp, error: Exception | str) -> None:
        errors.append(str(error))

    def on_open(ws: websocket.WebSocketApp) -> None:
        body = {
            "common": {"app_id": settings.iflytek_tts_app_id},
            "business": {
                "aue": "lame",
                "sfl": 1,
                "auf": "audio/L16;rate=16000",
                "vcn": vcn,
                "tte": "UTF8",
                "speed": 50,
                "volume": 50,
                "pitch": 50,
            },
            "data": {
                "status": 2,
                "text": base64.b64encode(plain.encode("utf-8")).decode("utf-8"),
            },
        }
        ws.send(json.dumps(body, ensure_ascii=False))

    ws_app = websocket.WebSocketApp(
        _build_auth_url(),
        on_message=on_message,
        on_error=on_error,
        on_open=on_open,
    )
    ssl_opt: dict = {}
    if settings.tts_ssl_verify:
        ssl_opt["cert_reqs"] = ssl.CERT_REQUIRED
    else:
        ssl_opt["cert_reqs"] = ssl.CERT_NONE
    ws_app.run_forever(
        sslopt=ssl_opt,
        ping_interval=10,
        ping_timeout=settings.tts_timeout,
        timeout=settings.tts_timeout,
    )

    if errors:
        raise RuntimeError(errors[0])
    if not audio_chunks:
        raise RuntimeError("语音合成返回空数据")
    return b"".join(audio_chunks)
