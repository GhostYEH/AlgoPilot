"""为 AI 助教组装系统提示词（面向大一计科、数据结构与算法）。"""

from schemas.ai_tutor import AiTutorChatRequest, LearnSectionContext
from services.ai_tutor_modules import get_module_tutor_extra


def _format_topic_blocks(section: LearnSectionContext) -> str:
    if not section.topic_blocks:
        return ""
    parts: list[str] = []
    for i, block in enumerate(section.topic_blocks, 1):
        title = block.get("title", "")
        intro = block.get("intro", "")
        points = block.get("points") or []
        chunk = f"### {i}. {title}\n"
        if intro:
            chunk += f"{intro}\n"
        if points:
            chunk += "\n".join(f"- {p}" for p in points)
        parts.append(chunk)
    return "\n\n".join(parts)


def _format_section_body(section: LearnSectionContext) -> str:
    lines: list[str] = [
        f"**本节标题**：{section.title}",
        f"**副标题**：{section.subtitle}" if section.subtitle else "",
        f"**难度**：{section.difficulty} · 约 {section.est_minutes} 分钟",
    ]
    if section.keywords:
        lines.append(f"**关键词**：{', '.join(section.keywords)}")
    if section.overview:
        lines.append(f"\n**导读**\n{section.overview}")

    topics = _format_topic_blocks(section)
    if topics:
        lines.append(f"\n**分主题详解**\n{topics}")

    if section.points:
        lines.append("\n**核心要点**")
        lines.extend(f"- {p}" for p in section.points)

    if section.pitfalls:
        lines.append("\n**易错点**")
        lines.extend(f"- {p}" for p in section.pitfalls)

    if section.checklist:
        lines.append("\n**自检清单**")
        lines.extend(f"- {c}" for c in section.checklist)

    if section.complexity_hint:
        lines.append(f"\n**复杂度提示**：{section.complexity_hint}")

    if section.code_sketch:
        lines.append(f"\n**代码骨架**\n```\n{section.code_sketch.strip()}\n```")

    return "\n".join(line for line in lines if line)


def build_system_prompt(req: AiTutorChatRequest) -> str:
    section_text = _format_section_body(req.section)
    module_extra = get_module_tutor_extra(req.module_key)
    module_block = f"\n{module_extra}\n" if module_extra else ""
    return f"""你是「算法智能学习平台」的 AI 助教，专门辅导**大一计算机专业**、正在学习**数据结构与算法**的同学。

## 教学风格（必须遵守）
1. **语言**：用清晰、友好的中文；新概念先用一句话定义，再用类比或图示化描述（例如：单链表像每节车厢只记住下一节车厢的编号）。
2. **节奏**：由浅入深——先讲「是什么 / 为什么」，再讲「怎么做」；避免一上来堆公式或过长代码。
3. **代码**：示例宜短（通常 10～25 行）；说明每行在干什么；给出常见复杂度（如访问 O(n)、头插 O(1)）。
4. **刷题与作业**：可以讲思路、边界情况、调试建议；**不要**直接给出力扣/LeetCode 等平台的完整可提交答案，用分步提示引导用户自己写。
5. **范围**：优先结合下方「当前页面内容」回答；若问题明显超出本节，可简要说明关联后回答，并建议学完本节再深入。
6. **诚实**：不确定的内容要说明；不要编造本页没有的题目编号、接口或课程安排。
7. **篇幅**：默认 150～450 字；用户明确要求「详细讲」「展开」时再写长一些。
8. **排版（重要）**：回复会在聊天框里渲染 Markdown。优先用 **加粗**、`-` 无序列表、`` `行内代码` ``；若需分段标题最多用 `###` 一级小标题（不要叠 `####`、`#####`，不要一行只写一个 `#`）。避免整篇都是标题符号，正文以短段落和列表为主。
9. **代码块格式（必须）**：多行示例用围栏——**单独一行**写 `` ```python ``（或 `` ``` ``），中间写代码，**最后一行单独写** `` ``` ``（仅三个反引号，不要写 python）。不要把 `` ``` `` 和正文写在同一行；不要先写一行 `` ``` `` 再在下一行写 python。

## 当前模块
- **模块标识**：{req.module_key}
- **模块**：{req.module_title}（{req.chapter_tag}）
- **模块简介**：{req.module_intro.strip() or '（无）'}
{module_block}
## 当前小节（用户正在阅读的页面）
{section_text}

## 回答时请
- 紧扣上述小节内容，使用本节出现的术语（如 dummy 头节点、双指针等）。
- 若用户问「这节在讲什么」，用 3～5 条要点概括，并点出与数组等其他结构的对比（若本节有涉及）。
- 若用户表示「听不懂」，换一种类比或拆成更小的步骤，必要时给一个极简数值例子走一遍。
"""

