from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from services.llm import chat_completion, chat_completion_stream


class BaseAgent(ABC):
    name: str = "BaseAgent"
    role: str = ""

    @abstractmethod
    def build_messages(self, **kwargs) -> list[dict[str, str]]:
        ...

    async def run(self, **kwargs) -> str:
        messages = self.build_messages(**kwargs)
        return await chat_completion(messages, temperature=self.temperature(), max_tokens=self.max_tokens())

    async def run_stream(self, **kwargs) -> AsyncIterator[str]:
        messages = self.build_messages(**kwargs)
        async for chunk in chat_completion_stream(
            messages, temperature=self.temperature(), max_tokens=self.max_tokens()
        ):
            yield chunk

    def temperature(self) -> float:
        return 0.65

    def max_tokens(self) -> int:
        return 2048
