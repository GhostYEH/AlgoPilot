"""大模型调用层：讯飞星火 Spark（仅 Orchestrator / Agent 使用，禁止 API 层直连）。"""

from services.llm.client import chat_completion, chat_completion_stream

__all__ = ["chat_completion", "chat_completion_stream"]
