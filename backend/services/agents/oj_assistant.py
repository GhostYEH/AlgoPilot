"""OJ 刷题助手 Agent。"""

from schemas.oj_assistant import OjAssistantRequest
from services.agents.base import BaseAgent
from services.llm import chat_completion
from services.oj_assistant_prompt import build_oj_assistant_messages


class OjAssistantAgent(BaseAgent):
    name = "OjAssistantAgent"
    role = "刷题辅导"

    def build_messages(self, *, request: OjAssistantRequest) -> list[dict[str, str]]:
        return build_oj_assistant_messages(request)

    async def run(self, **kwargs) -> str:
        """BaseAgent interface compatibility: kwargs must contain request: OjAssistantRequest."""
        body = kwargs["request"]
        return await self.run_for_request(body)

    async def run_for_request(self, body: OjAssistantRequest) -> str:
        messages = self.build_messages(request=body)
        temp = 0.55 if body.mode == "ds_hint" else 0.6
        max_t = 1200 if body.mode == "ds_hint" else 900
        return await chat_completion(messages, temperature=temp, max_tokens=max_t)
