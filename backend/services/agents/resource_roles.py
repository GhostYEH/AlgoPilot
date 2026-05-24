"""五类个性化资源生成角色 Agent（赛题多智能体协同）。"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from schemas.resources import ResourceType
from services.knowledge.retriever import KnowledgeChunk, format_context_block
from services.llm import chat_completion


@dataclass
class PersonaHints:
    """从画像块解析出的生成侧写。"""

    knowledge_base: str = ""
    cognitive_style: str = ""
    coding_ability: str = ""
    learning_goals: str = ""
    error_preference: str = ""
    grit_level: str = ""

    @classmethod
    def from_profile_block(cls, profile_block: str) -> PersonaHints:
        hints = cls()
        label_map = {
            "知识基础": "knowledge_base",
            "认知风格": "cognitive_style",
            "代码实操能力": "coding_ability",
            "学习目标": "learning_goals",
            "易错点偏好": "error_preference",
            "抗挫折心理": "grit_level",
            "抗挫折心理能力": "grit_level",
            # 兼容旧标签
            "薄弱点": "error_preference",
            "学习节奏": "grit_level",
            "兴趣方向": "learning_goals",
            "偏好模态": "cognitive_style",
        }
        for line in profile_block.splitlines():
            line = line.strip().lstrip("-").strip()
            if "：" not in line:
                continue
            label, _, val = line.partition("：")
            key = label_map.get(label.strip())
            if key and val.strip():
                setattr(hints, key, val.strip())
        return hints

    def personalization_block(self) -> str:
        parts: list[str] = []
        if self.knowledge_base:
            parts.append(f"- 知识基础：{self.knowledge_base}")
        if self.cognitive_style:
            parts.append(f"- 认知风格：{self.cognitive_style}")
        if self.coding_ability:
            parts.append(f"- 代码实操能力：{self.coding_ability}")
        if self.learning_goals:
            parts.append(f"- 学习目标：{self.learning_goals}")
        if self.error_preference:
            parts.append(f"- 易错点偏好：{self.error_preference}")
        if self.grit_level:
            parts.append(f"- 抗挫折心理：{self.grit_level}")
        return "\n".join(parts) if parts else "（按通用大一计科算法初学者处理）"


class ResourceRoleAgent(ABC):
    agent_id: str = "BaseResourceAgent"
    display_name: str = "BaseResourceAgent"
    role: str = ""

    @abstractmethod
    def system_prompt(self, hints: PersonaHints) -> str:
        ...

    def temperature(self) -> float:
        return 0.5

    def max_tokens(self) -> int:
        return 1600

    def build_user_prompt(
        self,
        *,
        topic: str,
        module_key: str,
        hints: PersonaHints,
        focus_hint: str,
        knowledge_block: str,
    ) -> str:
        parts = [
            f"课程主题：{topic}",
            f"关联模块：{module_key or '通用'}",
            f"学生画像：\n{hints.personalization_block()}",
            knowledge_block,
        ]
        if focus_hint:
            parts.append(f"协作上下文：\n{focus_hint}")
        parts.append("请直接输出内容，不要解释你是 AI。")
        return "\n\n".join(parts)

    async def generate(
        self,
        *,
        topic: str,
        profile_block: str,
        module_key: str = "",
        focus_hint: str = "",
        chunks: list[KnowledgeChunk],
    ) -> tuple[str, str, dict]:
        hints = PersonaHints.from_profile_block(profile_block)
        knowledge_block = format_context_block(chunks)
        messages = [
            {"role": "system", "content": self.system_prompt(hints)},
            {
                "role": "user",
                "content": self.build_user_prompt(
                    topic=topic,
                    module_key=module_key,
                    hints=hints,
                    focus_hint=focus_hint,
                    knowledge_block=knowledge_block,
                ),
            },
        ]
        content = await chat_completion(
            messages,
            temperature=self.temperature(),
            max_tokens=self.max_tokens(),
        )
        content = self.normalize_output(content.strip(), hints=hints)
        title = self.build_title(topic, module_key)
        meta = {
            "format": self.output_format(),
            "agent_id": self.agent_id,
            "agent_role": self.role,
            "temperature": self.temperature(),
            "persona_applied": hints.personalization_block()[:300],
        }
        return title, content, meta

    def build_title(self, topic: str, module_key: str) -> str:
        label = self.display_name.replace("Agent", "")
        if module_key:
            return f"{label} · {module_key} · {topic[:24]}"
        return f"{label} · {topic}"

    @abstractmethod
    def output_format(self) -> str:
        ...

    @abstractmethod
    def normalize_output(self, raw: str, *, hints: PersonaHints) -> str:
        ...


class ConceptAgent(ResourceRoleAgent):
    """概念导师：定制化 Markdown 课程讲解。"""

    agent_id = "ConceptAgent"
    display_name = "ConceptAgent"
    role = "概念导师 · 课程讲解文档"

    def system_prompt(self, hints: PersonaHints) -> str:
        style = (hints.cognitive_style or "").lower()
        if any(k in style for k in ("视觉", "visual", "图", "动画")):
            detail = "认知风格偏视觉：段落精简，多用列表、对比表、步骤编号，少用大段文字。"
        else:
            detail = "认知风格偏文本：讲解详尽，含定义、原理、例题 walkthrough 与小结。"
        ability = hints.coding_ability or "待评估"
        return f"""你是 ConceptAgent（概念导师）。根据学生画像与知识库撰写 Markdown 讲解文档。

## 个性化要求
{detail}
- 代码实操能力：{ability}，示例代码难度与之匹配
- 学习目标：{hints.learning_goals or '夯实算法基础'}
- 易错点：重点标注 {hints.error_preference or '常见边界与复杂度误区'}

## 输出规范
- 结构：学习目标（3条）、核心概念、分节讲解（≥2节）、易错提醒、小结、自测思考题（不给答案）
- 600～1200 字，中文，术语与知识库一致
- 不得编造库外四位题号、虚假 URL"""

    def temperature(self) -> float:
        return 0.5

    def output_format(self) -> str:
        return "markdown"

    def normalize_output(self, raw: str, *, hints: PersonaHints) -> str:
        return raw


class GraphAgent(ResourceRoleAgent):
    """拓扑专家：生成 Mermaid 知识点思维导图。"""

    agent_id = "GraphAgent"
    display_name = "GraphAgent"
    role = "拓扑专家 · Mermaid 知识图谱"

    def system_prompt(self, hints: PersonaHints) -> str:
        return f"""你是 GraphAgent（拓扑专家）。根据核心知识点输出 **Mermaid.js** 思维导图代码。

## 个性化要求
- 知识基础：{hints.knowledge_base or '大一计科'}
- 学习目标：{hints.learning_goals or '掌握本主题知识拓扑'}
- 若 error_preference 含具体知识点，将其作为子节点高亮标注

## 输出规范
- 只输出 Mermaid 源码，不要 markdown 代码块围栏
- 使用 flowchart TD 或 mindmap 语法
- 8～15 个节点，中文标签，与知识库一致
- 示例：
flowchart TD
  root["哈希表"] --> collision["冲突处理"]
  collision --> chaining["链地址法"]"""

    def temperature(self) -> float:
        return 0.45

    def max_tokens(self) -> int:
        return 1200

    def output_format(self) -> str:
        return "mermaid"

    def normalize_output(self, raw: str, *, hints: PersonaHints) -> str:
        text = raw.strip()
        fence = re.search(r"```(?:mermaid)?\s*([\s\S]*?)```", text)
        if fence:
            text = fence.group(1).strip()
        if not text.startswith(("flowchart", "graph", "mindmap", "sequenceDiagram")):
            topic = hints.learning_goals[:20] or "学习主题"
            return (
                f'flowchart TD\n  root["{topic}"]\n'
                f'  root --> n1["{text[:40].replace(chr(10), " ") or "核心概念"}"]'
            )
        return text


class QuizAgent(ResourceRoleAgent):
    """考题官：3 道个性化练习题（选择 + 填空）。"""

    agent_id = "QuizAgent"
    display_name = "QuizAgent"
    role = "考题官 · 个性化题单"

    def system_prompt(self, hints: PersonaHints) -> str:
        return f"""你是 QuizAgent（考题官）。根据学生知识短板与易错点生成 **3 道**个性化练习题。

## 个性化要求
- 知识基础：{hints.knowledge_base or '待评估'}
- 易错点偏好：{hints.error_preference or '边界条件与复杂度'}
- 代码能力：{hints.coding_ability or '入门'}，题目难度与之匹配

## 输出规范
- 输出**唯一** JSON，不要 markdown 代码块
- 固定 3 题：choice×2 + fill×1（禁止 code 编程题）
- 每题含 stem、hint、focus、difficulty(easy|medium|hard)

{{"questions":[{{"type":"choice","stem":"…","options":["A","B","C","D"],"hint":"…","focus":"…","difficulty":"easy"}}]}}"""

    def temperature(self) -> float:
        return 0.3

    def max_tokens(self) -> int:
        return 1400

    def output_format(self) -> str:
        return "quiz_json"

    def normalize_output(self, raw: str, *, hints: PersonaHints) -> str:
        data = _parse_json_object(raw)
        questions = data.get("questions") if isinstance(data, dict) else None
        if not isinstance(questions, list) or not questions:
            focus = hints.error_preference or "综合"
            return json.dumps(
                {
                    "questions": [
                        {
                            "type": "choice",
                            "stem": f"关于本主题，下列哪项最容易出错？（侧重：{focus}）",
                            "options": ["忽略边界", "正确理解", "跳过证明", "不分析复杂度"],
                            "hint": "结合易错点思考",
                            "focus": focus,
                            "difficulty": "easy",
                        },
                        {
                            "type": "fill",
                            "stem": "请填写本主题的核心时间复杂度符号（如 O(n)）",
                            "hint": "参考知识库",
                            "focus": "复杂度",
                            "difficulty": "medium",
                        },
                        {
                            "type": "choice",
                            "stem": "下列哪种表述与知识库一致？",
                            "options": ["A. 与知识库一致", "B. 编造题号", "C. 忽略边界", "D. 跳过定义"],
                            "hint": "选与知识库一致项",
                            "focus": "概念",
                            "difficulty": "easy",
                        },
                    ]
                },
                ensure_ascii=False,
                indent=2,
            )
        trimmed = [q for q in questions if isinstance(q, dict)][:3]
        while len(trimmed) < 3:
            trimmed.append(
                {
                    "type": "fill",
                    "stem": "请用一句话总结本主题要点",
                    "hint": "参考讲解文档",
                    "focus": hints.error_preference or "综合",
                    "difficulty": "medium",
                }
            )
        return json.dumps({"questions": trimmed}, ensure_ascii=False, indent=2)


class ScenarioAgent(ResourceRoleAgent):
    """互动编剧：实操案例剧本 + 待补全 TODO 代码框架。"""

    agent_id = "ScenarioAgent"
    display_name = "ScenarioAgent"
    role = "互动编剧 · 剧本沙盒"

    def system_prompt(self, hints: PersonaHints) -> str:
        grit = hints.grit_level or "中等"
        return f"""你是 ScenarioAgent（互动编剧）。生成**代入感实操剧本**与带 // TODO 的代码框架（动态沙盒模式，非小游戏）。

## 个性化要求
- 剧本背景贴合学习目标：{hints.learning_goals or '算法实践'}
- 代码框架难度匹配 coding_ability：{hints.coding_ability or '入门'}
- 抗挫折心理 {grit}：hint 分步给出，避免一次暴露完整答案
- 在 TODO 处设计易错点：{hints.error_preference or '边界处理'}

## 输出规范（Markdown）
1. ## 剧本背景（80～150字，有场景代入感）
2. ## 任务目标
3. ## 代码框架（Python3，15～35 行，关键逻辑处写 // TODO: …）
4. ## 分步提示（3 条，不给完整答案）
5. ## 复杂度说明"""

    def temperature(self) -> float:
        return 0.55

    def output_format(self) -> str:
        return "scenario_markdown"

    def normalize_output(self, raw: str, *, hints: PersonaHints) -> str:
        if "// TODO" not in raw and "TODO" not in raw:
            raw += "\n\n```python\n# TODO: 在此补全核心逻辑\ndef solve():\n    pass\n```"
        return raw


class TraceAgent(ResourceRoleAgent):
    """动画总导演：录制题解执行轨迹为 trace_viz JSON。"""

    agent_id = "TraceAgent"
    display_name = "TraceAgent"
    role = "动画总导演 · 执行轨迹动画"

    def system_prompt(self, hints: PersonaHints) -> str:
        return f"""你是 TraceAgent（动画总导演）。为教学动画准备**可执行的 Python 题解**与 stdin 测例。

## 个性化要求
- 题解应展示 {hints.error_preference or '核心算法'} 相关变量变化
- 难度匹配 coding_ability：{hints.coding_ability or '入门'}
- 代码须含 main 或可从 stdin 读入，便于 trace_runner 单步追踪

## 输出规范
输出**唯一** JSON，不要 markdown：
{{"code":"完整 Python3 源码","stdin":"输入","stdout":"期望输出","title":"动画标题","narration_hint":"30字动画旁白提示"}}"""

    def temperature(self) -> float:
        return 0.35

    def max_tokens(self) -> int:
        return 1800

    def output_format(self) -> str:
        return "trace_json"

    async def generate(
        self,
        *,
        topic: str,
        profile_block: str,
        module_key: str = "",
        focus_hint: str = "",
        chunks: list[KnowledgeChunk],
    ) -> tuple[str, str, dict]:
        title, content, meta = await super().generate(
            topic=topic,
            profile_block=profile_block,
            module_key=module_key,
            focus_hint=focus_hint,
            chunks=chunks,
        )
        payload = _parse_json_object(content)
        code = str(payload.get("code") or "").strip()
        stdin = str(payload.get("stdin") or "")
        trace_meta: dict[str, Any] = {"trace_source": "llm_only"}

        if code:
            trace_meta = await _record_trace(code, stdin, topic=topic)
            payload.update(trace_meta)
            content = json.dumps(payload, ensure_ascii=False, indent=2)

        meta["trace_verdict"] = trace_meta.get("verdict", "SKIPPED")
        meta["trace_steps"] = trace_meta.get("step_count", 0)
        return title, content, meta

    def normalize_output(self, raw: str, *, hints: PersonaHints) -> str:
        data = _parse_json_object(raw)
        if not isinstance(data, dict):
            data = {}
        if not data.get("code"):
            data = _fallback_trace_payload(topic=hints.learning_goals or "算法演示")
        return json.dumps(data, ensure_ascii=False, indent=2)


ROLE_AGENT_BY_TYPE: dict[ResourceType, ResourceRoleAgent] = {
    "document": ConceptAgent(),
    "mindmap": GraphAgent(),
    "exercises": QuizAgent(),
    "code_case": ScenarioAgent(),
    "trace_animation": TraceAgent(),
    # 兼容旧类型别名
    "reading": ConceptAgent(),
    "video_script": TraceAgent(),
}


def get_role_agent(resource_type: ResourceType) -> ResourceRoleAgent:
    return ROLE_AGENT_BY_TYPE.get(resource_type, ConceptAgent())


async def _record_trace(code: str, stdin: str, *, topic: str) -> dict[str, Any]:
    from services.oj.trace_runner import run_trace_stdio

    case = {"stdin": stdin, "stdout": ""}
    try:
        summary = run_trace_stdio(code, case=case, time_limit_ms=8000)
    except Exception as exc:
        return {
            "verdict": "RE",
            "message": str(exc)[:200],
            "step_count": 0,
            "steps": [],
            "trace_source": "trace_runner_error",
        }

    steps_out: list[dict[str, Any]] = []
    for step in summary.steps:
        steps_out.append(
            {
                "line": step.line,
                "changed": step.changed,
                "vars": step.vars,
            }
        )

    return {
        "verdict": summary.verdict,
        "message": summary.message,
        "step_count": len(steps_out),
        "user_line_count": summary.user_line_count,
        "steps": steps_out,
        "result_preview": summary.result_preview,
        "trace_source": "trace_runner",
        "topic": topic,
    }


def _fallback_trace_payload(*, topic: str) -> dict[str, Any]:
    code = (
        "n = int(input())\n"
        "nums = list(map(int, input().split()))\n"
        "total = 0\n"
        "for x in nums:\n"
        "    total += x\n"
        "print(total)\n"
    )
    return {
        "title": f"{topic} · 求和演示",
        "code": code,
        "stdin": "3\n1 2 3\n",
        "stdout": "6\n",
        "narration_hint": "观察循环变量与累加器的变化",
        "steps": [],
        "verdict": "PENDING",
        "trace_source": "fallback_template",
    }


def _parse_json_object(raw: str) -> dict[str, Any]:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(text[start : end + 1])
                return data if isinstance(data, dict) else {}
            except json.JSONDecodeError:
                pass
    return {}
