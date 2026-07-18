"""Run the five core resource agents through the real verification pipeline.

Usage:
    python -m scripts.audit_agent_quality
    python -m scripts.audit_agent_quality --topic "二叉树层序遍历" --module binary-tree
"""

from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any

from services.orchestrator.pipeline_context import PipelineContext
from services.orchestrator.workflow import resource_workflow
from schemas.resources import CORE_RESOURCE_PIPELINE
from services.agents.verifier import _structured_quality_issues


RESOURCE_TYPES = tuple(CORE_RESOURCE_PIPELINE)


def _summarize(kind: str, title: str, content: str, meta: dict[str, Any]) -> dict[str, Any]:
    row: dict[str, Any] = {
        "type": kind,
        "status": meta.get("status"),
        "verified": bool(meta.get("verified")),
        "attempts": meta.get("verify_attempts"),
        "chars": len(content),
        "title": title[:80],
    }
    if kind != "trace_animation":
        row["deterministic_quality_issues"] = _structured_quality_issues(
            content,
            resource_type=kind,
            topic=str(meta.get("topic") or ""),
        )
    if meta.get("status") != "published":
        verification = meta.get("content_verification") or {}
        row["draft_reason"] = meta.get("draft_reason")
        row["unsupported_claims"] = list(verification.get("unsupported_claims") or [])[:4]
        row["content_preview"] = content[:500]
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        data = {}
    if kind in {"document", "code_case"}:
        row.update(
            domain=bool(data.get("domain_narrative")),
            structure=bool(data.get("structure_logic")),
        )
    elif kind == "trace_animation":
        row.update(
            steps=len(data.get("steps") or []),
            trace_verdict=meta.get("trace_verdict"),
        )
    elif kind == "reading":
        levels = data.get("levels") or []
        row.update(
            levels=len(levels),
            items=sum(len(level.get("items") or []) for level in levels),
        )
    elif kind == "mindmap":
        row["nodes"] = sum(
            1
            for line in content.splitlines()
            if line.strip() and not line.strip().startswith("mindmap")
        )
    return row


async def _run(topic: str, module_key: str) -> int:
    profile = "\n".join(
        (
            f"知识基础：理解{topic}的基本术语",
            "认知风格：图示与步骤",
            "代码实操能力：入门",
            f"学习目标：掌握{topic}",
            "易错点偏好：操作顺序与边界条件",
        )
    )
    context = PipelineContext()
    results: list[dict[str, Any]] = []
    for kind in RESOURCE_TYPES:
        title, content, meta = await resource_workflow.run(
            kind,
            topic=topic,
            profile_block=profile,
            module_key=module_key,
            focus_hint="优先解释核心操作的先后顺序、成立前提和常见错误",
            pipeline_ctx=context,
        )
        row = _summarize(kind, title, content, meta)
        results.append(row)
        print(json.dumps(row, ensure_ascii=False))
    published = sum(row.get("status") == "published" for row in results)
    print(json.dumps({"published": published, "total": len(results)}, ensure_ascii=False))
    return 0 if published == len(results) else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default="链表反转")
    parser.add_argument("--module", default="linked-list", dest="module_key")
    args = parser.parse_args()
    return asyncio.run(_run(args.topic, args.module_key))


if __name__ == "__main__":
    raise SystemExit(main())
