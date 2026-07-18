"""QA 临时脚本：直接调用讯飞星火 LLM 验证 API Key 与返回质量（用 validator 校验）。"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from services.llm.client import chat_completion, chat_completion_stream
from services.llm.validator import (
    json_object_validator,
    non_empty_validator,
)


async def test_non_stream():
    """非流式：验证返回内容非空、是有效中文。"""
    print("=" * 60)
    print("[1] 非流式调用测试")
    msg = [{"role": "user", "content": "请用一句话介绍链表数据结构，不超过30字。"}]
    try:
        r = await chat_completion(msg, temperature=0.3, max_tokens=100)
        print(f"  返回长度: {len(r)}")
        print(f"  返回内容: {r[:200]}")
        v = non_empty_validator(5)(r)
        if v.passed:
            print("  [OK] validator 通过")
            return True
        else:
            print(f"  [FAIL] validator 失败: {v.issues}")
            return False
    except Exception as e:
        print(f"  [ERROR] {type(e).__name__}: {e}")
        return False


async def test_json_mode():
    """JSON 模式：验证 validator 能处理 LLM 返回的 markdown 围栏。"""
    print("=" * 60)
    print("[2] JSON 模式调用 + validator 校验")
    msg = [
        {"role": "system", "content": "仅输出 JSON 对象，不要 markdown。"},
        {"role": "user", "content": '输出 {"topic":"链表","summary":"一句话总结"}'},
    ]
    try:
        r = await chat_completion(msg, temperature=0.2, max_tokens=100, json_mode=True)
        print(f"  原始返回: {repr(r[:200])}")
        v = json_object_validator()(r)
        if v.passed:
            print("  [OK] json_object_validator 通过（能处理 markdown 围栏）")
            return True
        else:
            print(f"  [FAIL] validator 失败: {v.issues}")
            return False
    except Exception as e:
        print(f"  [ERROR] {type(e).__name__}: {e}")
        return False


async def test_stream():
    """流式：验证能收到多个 chunk。"""
    print("=" * 60)
    print("[3] 流式调用测试")
    msg = [{"role": "user", "content": "用三句话介绍动态规划的核心思想。"}]
    try:
        chunks = []
        async for delta in chat_completion_stream(msg, temperature=0.3, max_tokens=200):
            chunks.append(delta)
        full = "".join(chunks)
        print(f"  收到 chunk 数: {len(chunks)}")
        print(f"  拼接后长度: {len(full)}")
        print(f"  内容预览: {full[:200]}")
        v = non_empty_validator(10)(full)
        if v.passed:
            print("  [OK] 流式正常 + validator 通过")
            return True
        else:
            print(f"  [FAIL] validator 失败: {v.issues}")
            return False
    except Exception as e:
        print(f"  [ERROR] {type(e).__name__}: {e}")
        return False


async def main():
    from core.config import settings
    print("讯飞星火 LLM 实际调用验证")
    print(f"API Key 长度: {len(settings.spark_api_password)}")
    print(f"LLM 已配置: {settings.llm_configured}")
    print(f"模型: {settings.spark_model}")
    print()
    r1 = await test_non_stream()
    print()
    r2 = await test_json_mode()
    print()
    r3 = await test_stream()
    print()
    print("=" * 60)
    print(f"汇总: 非流式={'PASS' if r1 else 'FAIL'} JSON+validator={'PASS' if r2 else 'FAIL'} 流式={'PASS' if r3 else 'FAIL'}")
    return 0 if (r1 and r2 and r3) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
