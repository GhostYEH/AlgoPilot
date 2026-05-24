"""资源生成多智能体：Doc / MindMap / Quiz / Reading / Code / Video。"""

from __future__ import annotations

import json
import re

from schemas.resources import RESOURCE_AGENT_META, ResourceType
from services.agents.registry import agent_for_resource
from services.knowledge.retriever import KnowledgeChunk, format_context_block
from services.llm import chat_completion

_RESOURCE_TEMPERATURE: dict[str, float] = {
    "document": 0.5,
    "mindmap": 0.45,
    "exercises": 0.3,
    "reading": 0.5,
    "code_case": 0.4,
    "video_script": 0.7,
}

_RESOURCE_PROMPTS: dict[str, str] = {
    "document": """你是 DocAgent（课程讲解智能体）。根据学生画像与知识库片段撰写 Markdown 讲解文档。

## 输出规范
- 结构：学习目标（3条）、核心概念、分节讲解（≥2节）、小结、自测思考题（不给答案）
- 600～1200 字，中文，术语与知识库一致
- 不得编造库外四位题号、虚假 URL、未出现的教材章节号

## Few-shot 结构示例
### 学习目标
- 理解…定义
### 核心概念
…
### 小结
…""",
    "mindmap": """你是 MindMapAgent。输出**唯一**一段 JSON（不要 markdown 代码块）。

## JSON Schema
{
  "root": "string 根主题",
  "nodes": [
    {
      "id": "string 唯一",
      "label": "string 中文标签",
      "parent": "string 父 id，根子节点 parent=root",
      "children": ["string 子 id 列表，叶子为 []"]
    }
  ]
}
- 节点 8～15 个；children 必须为 string 数组；与知识库知识点一致

## Few-shot
{"root":"哈希表","nodes":[{"id":"n1","label":"冲突处理","parent":"root","children":[]}]}""",
    "exercises": """你是 QuizAgent。输出**唯一**一段 JSON（不要 markdown 代码块）。

## 输出规范
- 共 5 题，题型分布固定：choice×2 + fill×1 + code×2
- 难度：第1-2题入门，第3题中等，第4-5题进阶
- 编程题只给思路与函数签名，不给完整可提交答案

## JSON 格式
{"questions":[{"type":"choice|fill|code","stem":"题干","options":["A","B","C","D"],"hint":"提示","focus":"考查点","difficulty":"easy|medium|hard"}]}

## Few-shot（节选）
{"questions":[{"type":"choice","stem":"哈希查找平均复杂度？","options":["O(1)","O(n)","O(log n)","O(n^2)"],"hint":"考虑均摊","focus":"复杂度","difficulty":"easy"}]}""",
    "reading": """你是 ReadingAgent。生成拓展阅读 Markdown。

## 输出规范
- 3～5 条主题，每条 2～3 句
- 可提教材章节名（勿编造章节号），勿编造 URL

## Few-shot
1. **延伸阅读**：建议阅读…""",
    "code_case": """你是 CodeAgent。生成 Markdown 实操案例。

## 输出规范
- 含：问题描述、思路、Python3 示例（15～35 行含注释）、时间与空间复杂度
- 复杂度须与知识库一致并注明前提

## Few-shot
## 问题\n…\n## 代码\n```python\n# O(n)\ndef solve(nums):\n    pass\n```""",
    "video_script": """你是 VideoAgent。生成 Markdown 分镜脚本。

## 输出规范
- 4～6 镜，每镜：场景 | 旁白 | 画面 | 配图建议
- 注明可对接 TTS/动画

## Few-shot
| 镜号 | 旁白 | 画面 |\n| 1 | … | 动画演示… |""",
}


class ResourceAgents:
    @staticmethod
    def agent_name(resource_type: ResourceType) -> str:
        return agent_for_resource(resource_type)

    @staticmethod
    def build_messages(
        resource_type: ResourceType,
        *,
        topic: str,
        profile_block: str,
        module_key: str,
        focus_hint: str,
        knowledge_block: str,
    ) -> list[dict[str, str]]:
        system = _RESOURCE_PROMPTS[resource_type] + "\n\n" + knowledge_block
        user_parts = [
            f"课程主题：{topic}",
            f"关联模块：{module_key or '通用'}",
            f"学生画像：\n{profile_block}",
        ]
        if focus_hint:
            user_parts.append(f"生成侧重与协作上下文：\n{focus_hint}")
        user_parts.append("请直接输出内容，不要解释你是 AI。")
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": "\n".join(user_parts)},
        ]

    @staticmethod
    async def generate_with_context(
        resource_type: ResourceType,
        *,
        topic: str,
        profile_block: str,
        module_key: str = "",
        focus_hint: str = "",
        chunks: list[KnowledgeChunk],
    ) -> tuple[str, str, dict]:
        knowledge_block = format_context_block(chunks)
        messages = ResourceAgents.build_messages(
            resource_type,
            topic=topic,
            profile_block=profile_block,
            module_key=module_key,
            focus_hint=focus_hint,
            knowledge_block=knowledge_block,
        )
        max_tokens = 2000 if resource_type in ("exercises", "mindmap") else 1600
        temp = _RESOURCE_TEMPERATURE.get(resource_type, 0.5)
        content = await chat_completion(messages, temperature=temp, max_tokens=max_tokens)
        content = _normalize_output(resource_type, content.strip())
        label = RESOURCE_AGENT_META[resource_type]["label"]
        title = f"{label} · {topic}"
        if module_key:
            title = f"{label} · {module_key} · {topic[:24]}"
        meta = {
            "format": _output_format(resource_type),
            "agent_id": agent_for_resource(resource_type),
            "temperature": temp,
        }
        return title, content, meta

    @staticmethod
    async def generate(
        resource_type: ResourceType,
        *,
        topic: str,
        profile_block: str,
        module_key: str = "",
        focus_hint: str = "",
        knowledge_block: str = "",
        chunks: list[KnowledgeChunk] | None = None,
    ) -> tuple[str, str, dict]:
        from services.knowledge.retriever import retriever

        if chunks is None:
            query = f"{topic} {focus_hint} {module_key}".strip()
            chunks = retriever.search(query, module_key=module_key, top_k=5)
        return await ResourceAgents.generate_with_context(
            resource_type,
            topic=topic,
            profile_block=profile_block,
            module_key=module_key,
            focus_hint=focus_hint,
            chunks=chunks,
        )


def _output_format(resource_type: ResourceType) -> str:
    if resource_type == "mindmap":
        return "mindmap_json"
    if resource_type == "exercises":
        return "quiz_json"
    return "markdown"


def _normalize_output(resource_type: ResourceType, raw: str) -> str:
    if resource_type == "mindmap":
        return _ensure_json(raw, fallback_type="mindmap")
    if resource_type == "exercises":
        return _ensure_json(raw, fallback_type="quiz")
    return raw


def _ensure_json(raw: str, fallback_type: str) -> str:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        data = json.loads(text)
        return json.dumps(data, ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(text[start : end + 1])
                return json.dumps(data, ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                pass
    if fallback_type == "mindmap":
        label = _first_heading_or_line(text, 120)
        return json.dumps(
            {
                "root": "学习主题",
                "nodes": [
                    {
                        "id": "n1",
                        "label": label or "待整理",
                        "parent": "root",
                        "children": [],
                    },
                    {
                        "id": "n2",
                        "label": text[80:160].strip() or "知识点",
                        "parent": "n1",
                        "children": [],
                    },
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    stem = text[:400].strip() or "请根据知识库复习"
    return json.dumps(
        {
            "questions": [
                {
                    "type": "fill",
                    "stem": stem,
                    "hint": "请参考知识库与讲解文档",
                    "focus": "综合",
                    "difficulty": "medium",
                },
                {
                    "type": "choice",
                    "stem": "下列哪项最符合本主题？",
                    "options": ["A. 与知识库一致", "B. 编造题号", "C. 忽略复杂度", "D. 跳过边界"],
                    "hint": "选与知识库一致项",
                    "focus": "概念",
                    "difficulty": "easy",
                },
            ]
        },
        ensure_ascii=False,
        indent=2,
    )


def _first_heading_or_line(text: str, limit: int) -> str:
    for ln in text.splitlines():
        ln = ln.strip().lstrip("#").strip()
        if ln:
            return ln[:limit]
    return text[:limit].strip()
