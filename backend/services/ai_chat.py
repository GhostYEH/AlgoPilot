"""兼容层：请使用 services.llm.client，新代码仅经 Orchestrator 调用。"""

from services.llm.client import chat_completion, chat_completion_stream

__all__ = ["chat_completion", "chat_completion_stream"]
