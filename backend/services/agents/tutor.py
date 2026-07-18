"""TutorAgent：学习页多模态智能辅导（结合画像）。"""

from collections.abc import AsyncIterator

from schemas.ai_tutor import AiTutorChatRequest
from services.agents.base import BaseAgent
from services.ai_tutor_prompt import build_system_prompt
from services.llm import chat_completion_stream
from services.llm.validator import (
    DEFAULT_MAX_RETRIES,
    chat_completion_validated,
    non_empty_validator,
)


class TutorAgent(BaseAgent):
    name = "TutorAgent"
    role = "智能辅导"

    def build_messages(
        self, *, request: AiTutorChatRequest, profile_block: str = ""
    ) -> list[dict[str, str]]:
        system_prompt = build_system_prompt(request)
        if profile_block:
            system_prompt += f"""

## 学生个性化画像（答疑须结合易错点，勿复述整段）
{profile_block}

## 多模态输出建议
- 复杂流程可用 ```mermaid` 流程图（节点中文简短）
- 对比类问题用列表；代码仅给思路级短示例（10 行内），勿给完整 OJ 可提交答案
"""
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        for item in request.history[-16:]:
            messages.append({"role": item.role, "content": item.content})
        messages.append({"role": "user", "content": request.message})
        return messages

    async def run(self, *, request: AiTutorChatRequest, profile_block: str = "") -> str:
        messages = self.build_messages(request=request, profile_block=profile_block)
        text, _ = await chat_completion_validated(
            messages,
            validator=non_empty_validator(5),
            max_retries=DEFAULT_MAX_RETRIES,
            temperature=0.65,
            max_tokens=2048,
            retry_temperature=0.8,
            context_label="tutor_chat",
        )
        return text

    async def run_stream(
        self, *, request: AiTutorChatRequest, profile_block: str = ""
    ) -> AsyncIterator[str]:
        messages = self.build_messages(request=request, profile_block=profile_block)
        async for chunk in chat_completion_stream(messages, temperature=0.65, max_tokens=2048):
            yield chunk

    def temperature(self) -> float:
        return 0.65

    def max_tokens(self) -> int:
        return 2048
