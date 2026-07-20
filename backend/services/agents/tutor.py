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


def _zero_one_knapsack_reverse_reply(request: AiTutorChatRequest) -> str | None:
    """为 0/1 背包一维倒序这一高频易错点提供确定性事实护栏。"""
    message = request.message.lower()
    if request.module_key != "dp" or "背包" not in message or "0/1" not in message:
        return None
    if not any(keyword in message for keyword in ("倒序", "从大到小", "遍历顺序")):
        return None

    diagram = ""
    if "mermaid" in message or "图" in message or "流程" in message:
        diagram = """```mermaid
flowchart TD
    A[遍历当前物品] --> B[容量 j 从 W 递减到 w]
    B --> C[读取尚未被本轮改写的 dp[j-w]]
    C --> D[dp[j] = max(dp[j], dp[j-w] + v)]
    D --> E{还有下一件物品?}
    E -- 是 --> A
    E -- 否 --> F[得到 dp[W]]
```

"""

    return f"""{diagram}一维状态 `dp[j]` 表示：处理完当前及之前的物品后，容量上限为 `j` 时能取得的最大价值。处理重量为 `w`、价值为 `v` 的物品时，更新式是 `dp[j] = max(dp[j], dp[j-w] + v)`，并让 `j` 从 `W` 递减到 `w`。

必须倒序，是为了让本次读取的 `dp[j-w]` 仍来自“处理当前物品之前”的上一轮状态，这样当前物品最多只会被使用一次。若正序更新，较小容量的 `dp[j-w]` 可能已经在本轮加入过当前物品，再拿它更新 `dp[j]` 就会重复使用同一件物品，语义会变成完全背包。倒序不会降低 `O(nW)` 的时间复杂度；它保证的是状态转移正确性。"""


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
        if request.module_key == "dp" and "背包" in request.message:
            # 把高频易混淆事实放到用户问题之前的最近位置，避免长上下文中
            # 被模型误写成“为了提速”或“避免搜索”。
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "本轮回答的事实底线：0/1 背包一维 DP 更新为 "
                        "dp[j] = max(dp[j], dp[j-w] + v)，容量 j 必须从 W 倒序到 w。"
                        "倒序的唯一核心原因是让 dp[j-w] 保持为上一轮物品的状态，"
                        "防止同一件物品在本轮被重复使用；它不会降低 O(nW) 时间复杂度。"
                        "完全背包允许重复使用物品，容量才正序。不得把倒序解释为提速、"
                        "贪心选择、减少搜索或容量与价值比较。"
                    ),
                }
            )
        messages.append({"role": "user", "content": request.message})
        return messages

    async def run(self, *, request: AiTutorChatRequest, profile_block: str = "") -> str:
        guarded_reply = _zero_one_knapsack_reverse_reply(request)
        if guarded_reply is not None:
            return guarded_reply
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
        guarded_reply = _zero_one_knapsack_reverse_reply(request)
        if guarded_reply is not None:
            yield guarded_reply
            return
        messages = self.build_messages(request=request, profile_block=profile_block)
        async for chunk in chat_completion_stream(messages, temperature=0.65, max_tokens=2048):
            yield chunk

    def temperature(self) -> float:
        return 0.65

    def max_tokens(self) -> int:
        return 2048
