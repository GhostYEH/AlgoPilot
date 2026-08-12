"""健康检查与联调接口"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    """前后端联调探活，并检查 LLM、TTS 与 Trace 子系统。"""
    from core.config import settings

    trace_cpp = False
    cpp_compiler = False
    try:
        from services.oj.cpp_runner import _find_gpp
        from services.oj.cpp_trace_runner import gdb_available

        cpp_compiler = _find_gpp() is not None
        trace_cpp = cpp_compiler and gdb_available()
    except Exception:
        pass

    llm_ok = bool(settings.llm_configured)
    tts_ok = bool(settings.tts_configured)

    hints: list[str] = []
    if not llm_ok:
        hints.append(
            "未配置 SPARK_API_PASSWORD：画像对话与 generate-all 可走模板降级；"
            "Python OJ/Trace 诊断仍可用规则兜底"
        )
    if not tts_ok:
        hints.append("未配置 TTS：视频脚本分镜与试听文案仍可展示，语音合成不可用")
    if not trace_cpp:
        hints.append("C++ Trace 不可用：可使用 Python Trace，或安装 g++/gdb")

    return {
        "status": "ok",
        "llm_configured": llm_ok,
        "tts_configured": tts_ok,
        "trace_python": True,
        "trace_cpp": trace_cpp,
        "cpp_compiler": cpp_compiler,
        "hints": hints,
    }
