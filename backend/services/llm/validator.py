"""LLM 输出验证与重试工具。

提供「检测到输出有问题就重新调用 AI 生成」的通用机制：
- 非流式场景：检测到问题重试（最多 max_retries 次），全部失败后保留最后一次结果并附带 warning。
- 流式场景：检测到问题后，先通过 on_retry 回调通知调用方发送 regenerate_clear 信号
  （让前端清空已生成的 delta），再重新发起流式生成。

设计原则：
- 不破坏现有 chat_completion / chat_completion_stream 接口（保持向后兼容）。
- 验证器是纯函数，由调用方根据业务场景提供。
- 流式重试时，前一轮已 yield 的 delta 无法「撤回」，由调用方通过 on_retry 钩子
  自行向前端发送清空信号；本工具只在重试前回调一次。
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field

from services.llm.client import chat_completion, chat_completion_stream

_logger = logging.getLogger(__name__)

# 默认最大重试次数（用户要求 2 次重试，即最多调用 3 次 LLM）
DEFAULT_MAX_RETRIES: int = 2


@dataclass
class ValidationResult:
    """LLM 输出验证结果。"""

    passed: bool
    issues: list[str] = field(default_factory=list)

    @classmethod
    def ok(cls) -> "ValidationResult":
        return cls(passed=True)

    @classmethod
    def fail(cls, *issues: str) -> "ValidationResult":
        return cls(passed=False, issues=list(issues))


# 验证器签名：接收 LLM 完整输出文本，返回 ValidationResult
ValidatorFn = Callable[[str], ValidationResult]


# ---------- 通用验证器 ----------

def non_empty_validator(min_chars: int = 1) -> ValidatorFn:
    """校验输出非空且达到最小长度。"""

    def _validate(text: str) -> ValidationResult:
        if not text or not text.strip():
            return ValidationResult.fail("LLM 返回内容为空")
        if len(text.strip()) < min_chars:
            return ValidationResult.fail(
                f"LLM 返回内容过短（{len(text.strip())} 字符 < 最小 {min_chars}）"
            )
        return ValidationResult.ok()

    return _validate


def json_object_validator() -> ValidatorFn:
    """校验输出是合法的 JSON 对象。"""

    def _validate(text: str) -> ValidationResult:
        import json

        if not text or not text.strip():
            return ValidationResult.fail("LLM 返回内容为空")
        raw = text.strip()
        # 剥离 markdown 代码围栏
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            return ValidationResult.fail(f"LLM 返回不是合法 JSON：{exc}")
        if not isinstance(data, dict):
            return ValidationResult.fail("LLM 返回 JSON 不是对象")
        return ValidationResult.ok()

    return _validate


# ---------- 非流式：带重试的 chat_completion ----------

async def chat_completion_validated(
    messages: list[dict[str, str]],
    *,
    validator: ValidatorFn,
    max_retries: int = DEFAULT_MAX_RETRIES,
    temperature: float = 0.65,
    max_tokens: int = 2048,
    json_mode: bool = False,
    retry_temperature: float | None = None,
    context_label: str = "",
) -> tuple[str, ValidationResult]:
    """带验证与重试的 chat_completion。

    返回 (最终输出, 最终验证结果)。若所有重试均失败，返回最后一次输出与失败结果，
    调用方可根据 final_result.passed 决定是否附加 warning 或降级处理。

    Args:
        validator: 验证函数，返回 ValidationResult
        max_retries: 最大重试次数（不含首次调用，共 max_retries+1 次调用）
        retry_temperature: 重试时使用的温度（略高于首次以增加多样性），默认沿用 temperature
        context_label: 用于日志的上下文标签，便于排查
    """
    last_text: str = ""
    last_result: ValidationResult = ValidationResult.fail("未调用 LLM")
    retry_temp = retry_temperature if retry_temperature is not None else temperature

    for attempt in range(max_retries + 1):
        current_temp = temperature if attempt == 0 else retry_temp
        try:
            text = await chat_completion(
                messages,
                temperature=current_temp,
                max_tokens=max_tokens,
                json_mode=json_mode,
            )
        except Exception:
            # LLM 调用本身的异常（超时、502 等）向上抛，由调用方处理
            raise

        last_text = text
        last_result = validator(text)
        if last_result.passed:
            if attempt > 0:
                _logger.info(
                    "LLM 输出验证通过（重试 %d 次后成功）%s",
                    attempt,
                    f" context={context_label}" if context_label else "",
                )
            return text, last_result

        _logger.warning(
            "LLM 输出验证失败 attempt=%d/%d%s issues=%s",
            attempt + 1,
            max_retries + 1,
            f" context={context_label}" if context_label else "",
            last_result.issues,
        )

    _logger.warning(
        "LLM 输出验证最终失败（已重试 %d 次）%s",
        max_retries,
        f" context={context_label}" if context_label else "",
    )
    return last_text, last_result


# ---------- 流式：带重试与 regenerate_clear 信号的 chat_completion_stream ----------

async def chat_completion_stream_validated(
    messages: list[dict[str, str]],
    *,
    validator: ValidatorFn,
    on_retry: Callable[[int, ValidationResult], None] | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    temperature: float = 0.65,
    max_tokens: int = 2048,
    retry_temperature: float | None = None,
    context_label: str = "",
) -> AsyncIterator[tuple[str, str]]:
    """带验证与重试的 chat_completion_stream。

    流式生成完整内容，生成结束后由 validator 校验。若校验失败：
    1. 调用 on_retry(attempt, result) 通知调用方（调用方应发送 regenerate_clear 信号让前端清空）
    2. 重新发起流式生成
    最多重试 max_retries 次。

    yield 形式为 (event_type, payload)：
    - ("delta", "文本片段")：正常的流式增量，调用方应转发给前端
    - ("regenerate_clear", reason)：清空信号，调用方应转发给前端让其清空已显示内容
    - ("done", final_text)：生成结束（最终内容已通过验证或重试次数耗尽）
    - ("warning", issue)：最终验证失败时附带的 warning 信息（前端可选择展示）
    """
    retry_temp = retry_temperature if retry_temperature is not None else temperature
    last_text: str = ""
    last_result: ValidationResult = ValidationResult.fail("未调用 LLM")

    for attempt in range(max_retries + 1):
        current_temp = temperature if attempt == 0 else retry_temp
        chunks: list[str] = []

        if attempt > 0:
            # 重试前通知调用方发送清空信号
            if on_retry is not None:
                try:
                    on_retry(attempt, last_result)
                except Exception:
                    _logger.exception(
                        "on_retry 回调异常%s",
                        f" context={context_label}" if context_label else "",
                    )
            yield ("regenerate_clear", "; ".join(last_result.issues) or "LLM 输出有问题，重新生成")

        try:
            async for delta in chat_completion_stream(
                messages,
                temperature=current_temp,
                max_tokens=max_tokens,
            ):
                chunks.append(delta)
                yield ("delta", delta)
        except Exception:
            # LLM 流式调用本身异常，向上抛
            raise

        last_text = "".join(chunks)
        last_result = validator(last_text)
        if last_result.passed:
            if attempt > 0:
                _logger.info(
                    "LLM 流式输出验证通过（重试 %d 次后成功）%s",
                    attempt,
                    f" context={context_label}" if context_label else "",
                )
            yield ("done", last_text)
            return

        _logger.warning(
            "LLM 流式输出验证失败 attempt=%d/%d%s issues=%s",
            attempt + 1,
            max_retries + 1,
            f" context={context_label}" if context_label else "",
            last_result.issues,
        )

    _logger.warning(
        "LLM 流式输出验证最终失败（已重试 %d 次）%s",
        max_retries,
        f" context={context_label}" if context_label else "",
    )
    # 最终仍失败：yield warning 让前端展示，再以 done 结束（保留最后一次内容）
    yield ("warning", "; ".join(last_result.issues))
    yield ("done", last_text)
