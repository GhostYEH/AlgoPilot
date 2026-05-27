"""Quick check: AI tutor API + 讯飞星火 Spark。"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from core.config import settings


async def main() -> int:
    print("LLM configured:", settings.llm_configured)
    print("LLM provider:", settings.llm_provider)
    print("LLM model:", settings.spark_model)
    print("LLM URL:", settings.spark_chat_url)

    payload = {
        "message": "用一句话解释什么是单链表",
        "history": [],
        "module_key": "linked-list",
        "module_title": "链表学习模块",
        "chapter_tag": "链表篇",
        "module_intro": "链表是一种线性结构",
        "section": {
            "id": "theory",
            "title": "理论基础",
            "points": ["每个节点包含数据和指向下一个节点的指针"],
        },
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        r = await client.post("http://127.0.0.1:9000/api/ai/tutor/chat", json=payload)

    print("HTTP status:", r.status_code)
    if r.status_code != 200:
        print("Error body:", r.text[:500])
        return 1

    reply = r.json().get("reply", "")
    print("Reply length:", len(reply))
    print("Reply preview:", reply[:300])
    out = Path(__file__).resolve().parent.parent.parent / "ai-test-result.txt"
    out.write_text(f"status={r.status_code}\n{reply}\n", encoding="utf-8")
    print("Full reply saved to:", out)
    return 0 if reply.strip() else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
