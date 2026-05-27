"""阿里云百炼 CosyVoice 语音合成（dashscope tts_v2）。"""

from __future__ import annotations

import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer

from core.config import settings

MAX_TTS_CHARS = 2000


def synthesize_speech(text: str, *, voice: str | None = None) -> bytes:
    plain = " ".join(text.split()).strip()
    if not plain:
        raise ValueError("朗读文本为空")
    if len(plain) > MAX_TTS_CHARS:
        plain = f"{plain[:MAX_TTS_CHARS]}…"

    if not settings.dashscope_api_key:
        raise RuntimeError("未配置 DASHSCOPE_API_KEY")

    dashscope.api_key = settings.dashscope_api_key
    synthesizer = SpeechSynthesizer(
        model=settings.tts_model,
        voice=voice or settings.tts_voice,
    )
    audio = synthesizer.call(plain)
    if not audio:
        raise RuntimeError("语音合成返回空数据")
    if isinstance(audio, bytes):
        return audio
    if isinstance(audio, bytearray):
        return bytes(audio)
    raise RuntimeError(f"语音合成返回类型异常：{type(audio).__name__}")
