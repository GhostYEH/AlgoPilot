"""五类个性化资源生成角色 Agent（赛题多智能体协同）。"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from schemas.agent_outputs import QuizQuestion, validate_quiz_payload
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

    def interest_theme(self) -> str:
        """从学习目标/兴趣侧写提取叙事世界观（供业务域 Prompt）。"""
        goals = (self.learning_goals or "").strip()
        if not goals:
            return "星际探险"
        themes = (
            "赛博朋克",
            "原神",
            "星际探险",
            "哈利波特",
            "三体",
            "黑客帝国",
            "minecraft",
            "我的世界",
            "武侠",
            "修仙",
        )
        lower = goals.lower()
        for t in themes:
            if t.lower() in lower or t in goals:
                return t
        return goals[:48]


# --- Domain / Structure 双域 JSON（understand-anything 式 Prompt 分离）---

DOMAIN_STRUCTURE_JSON_SCHEMA = """
{
  "domain_narrative": {
    "headline": "业务场景标题（纯故事语言）",
    "story": "代入感故事正文（Markdown 可用，禁止代码与数据结构名）",
    "illustration_hint": "给 UI 插画占位的一句话画面描述（如：霓虹雨夜的数据港）"
  },
  "structure_logic": {
    "learning_objectives": ["学术目标1", "学术目标2"],
    "abstract_model": "形式化问题抽象（输入/输出/不变量）",
    "data_structures": ["双端队列", "邻接矩阵"],
    "algorithm_outline": "步骤化算法描述（可用伪代码，禁止故事）",
    "time_complexity": "O(n) 及简要理由",
    "space_complexity": "O(1) 及简要理由",
    "correctness_proof": "正确性/复杂度论证要点（2~5句严谨表述）",
    "pitfalls": ["易错点1", "易错点2"]
  }
}
""".strip()

SCENARIO_DOMAIN_STRUCTURE_SCHEMA = """
{
  "domain_narrative": {
    "headline": "剧本标题",
    "story": "剧本背景（纯叙事，禁止代码与数据结构名）",
    "mission": "任务目标（故事语言描述要达成什么）",
    "illustration_hint": "场景插画提示"
  },
  "structure_logic": {
    "problem_formalization": "剥离故事后的形式化题意",
    "data_structures": ["需要的数据结构"],
    "code_framework": "Python3 代码框架，关键处 // TODO: …",
    "step_hints": ["分步提示1", "分步提示2", "分步提示3"],
    "time_complexity": "O(?) 及理由",
    "space_complexity": "O(?) 及理由",
    "correctness_proof": "复杂度或正确性论证要点"
  }
}
""".strip()

def _domain_structure_system_preamble(*, agent_label: str, hints: PersonaHints) -> str:
    theme = hints.interest_theme()
    return f"""你是 {agent_label}。你必须遵守 **业务域 (Domain) 与结构域 (Structure) 严格分离** 原则，杜绝把故事与底层实现混写。

## 学生兴趣世界观（仅用于 domain_narrative）
- 叙事主题：{theme}
- 画像侧写：
{hints.personalization_block()}

## 绝对禁令
- domain_narrative 内：**禁止** 出现任何编程语言、代码片段、伪代码、变量名、API、复杂度符号、数据结构/算法专有名词（如数组、链表、栈、队列、哈希、堆、图、指针、动态规划等）。
- structure_logic 内：**禁止** 出现故事情节、角色对白、世界观设定；只用计算机科学学术语言。
- 输出必须是 **唯一 JSON 对象**，不要用 markdown 代码围栏包裹。"""


def _normalize_domain_structure_payload(
    data: dict[str, Any],
    *,
    fallback_topic: str,
    scenario: bool = False,
) -> dict[str, Any]:
    domain = data.get("domain_narrative")
    structure = data.get("structure_logic")
    if not isinstance(domain, dict):
        domain = {"headline": fallback_topic, "story": str(domain or fallback_topic), "illustration_hint": ""}
    if not isinstance(structure, dict):
        structure = {"abstract_model": str(structure or ""), "data_structures": []}

    story = str(domain.get("story") or "").strip()
    if not story:
        domain["story"] = f"围绕「{fallback_topic}」展开的沉浸式任务（待模型补全）。"

    if scenario:
        domain.setdefault("mission", str(domain.get("mission") or "在叙事中完成核心挑战"))
    else:
        structure.setdefault("learning_objectives", structure.get("learning_objectives") or [])
        structure.setdefault("pitfalls", structure.get("pitfalls") or [])

    structure.setdefault("data_structures", structure.get("data_structures") or [])
    if scenario and not str(structure.get("code_framework") or "").strip():
        structure["code_framework"] = (
            "# TODO: 在此补全核心逻辑\n"
            "def solve():\n"
            "    pass\n"
        )

    domain.setdefault("headline", str(domain.get("headline") or fallback_topic))
    domain.setdefault(
        "illustration_hint",
        str(domain.get("illustration_hint") or f"{fallback_topic} 主题场景概念图"),
    )
    structure.setdefault("time_complexity", str(structure.get("time_complexity") or "待分析"))
    structure.setdefault("space_complexity", str(structure.get("space_complexity") or "待分析"))
    structure.setdefault(
        "correctness_proof",
        str(structure.get("correctness_proof") or "请结合算法不变量完成论证。"),
    )

    return {"domain_narrative": domain, "structure_logic": structure}


def _serialize_domain_structure(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


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
    """概念导师：业务域故事 + 结构域学术剖析（JSON 双域输出）。"""

    agent_id = "ConceptAgent"
    display_name = "ConceptAgent"
    role = "概念导师 · Domain/Structure 双域教案"

    def system_prompt(self, hints: PersonaHints) -> str:
        style = (hints.cognitive_style or "").lower()
        if any(k in style for k in ("视觉", "visual", "图", "动画")):
            domain_style = "业务故事宜画面感强、节奏快，多用场景动作与对话感。"
        else:
            domain_style = "业务故事可稍详尽，注重动机与因果。"
        ability = hints.coding_ability or "待评估"
        preamble = _domain_structure_system_preamble(agent_label="ConceptAgent（概念导师）", hints=hints)
        return f"""{preamble}

## domain_narrative（业务域）写作指导
请结合学生兴趣世界观（如：赛博朋克、原神、星际探险等），用生动、代入感极强的故事讲解当前算法的**业务应用场景**（「现实中要解决什么问题」）。
{domain_style}
- 此部分**绝对不允许**出现任何代码、伪代码、变量名、复杂度符号或具体数据结构/算法名称。
- 用「货物」「通道」「情报网」等隐喻可，但不能出现「数组」「队列」等术语。

## structure_logic（结构域）写作指导
剥离所有业务故事，用最严谨的计算机科学学术语言，从抽象层级讲解底层实现：
- 明确指出需要哪些**数据结构**（如：优先队列、双端队列、邻接矩阵）
- 给出**时间/空间复杂度**及简要证明或论证草图
- 代码实操能力：{ability}，算法描述难度与之匹配
- 易错点侧重：{hints.error_preference or '边界与复杂度'}
- 术语须与知识库一致，不得编造库外四位题号、虚假 URL

## JSON Schema（严格遵守字段名）
{DOMAIN_STRUCTURE_JSON_SCHEMA}

## 篇幅
- domain_narrative.story：200～400 字
- structure_logic 各字段合计：400～900 字"""

    def temperature(self) -> float:
        return 0.45

    def max_tokens(self) -> int:
        return 2400

    def output_format(self) -> str:
        return "domain_structure_json"

    def normalize_output(self, raw: str, *, hints: PersonaHints) -> str:
        data = _parse_json_object(raw)
        if data.get("domain_narrative") and data.get("structure_logic"):
            normalized = _normalize_domain_structure_payload(
                data,
                fallback_topic=hints.learning_goals[:32] or "算法主题",
                scenario=False,
            )
            return _serialize_domain_structure(normalized)

        # 兼容旧版 Markdown：拆成双域
        legacy_story = raw.strip()
        normalized = _normalize_domain_structure_payload(
            {
                "domain_narrative": {
                    "headline": "学习场景",
                    "story": legacy_story[:1200],
                    "illustration_hint": hints.interest_theme(),
                },
                "structure_logic": {
                    "learning_objectives": ["理解核心算法思想", "掌握复杂度分析"],
                    "abstract_model": "（由旧版教案迁移，建议重新生成）",
                    "data_structures": [],
                    "algorithm_outline": legacy_story[1200:2400] or "请参考知识库补全形式化描述。",
                    "time_complexity": "待分析",
                    "space_complexity": "待分析",
                    "correctness_proof": "待补全",
                    "pitfalls": [hints.error_preference or "边界条件"],
                },
            },
            fallback_topic=hints.learning_goals[:32] or "算法主题",
            scenario=False,
        )
        return _serialize_domain_structure(normalized)


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
        validated, issues = validate_quiz_payload(data if isinstance(data, dict) else {})
        if validated is not None:
            trimmed: list[QuizQuestion] = list(validated.questions[:3])
            while len(trimmed) < 3:
                trimmed.append(
                    QuizQuestion(
                        type="fill",
                        stem="请用一句话总结本主题要点",
                        hint="参考讲解文档",
                        focus=hints.error_preference or "综合",
                        difficulty="medium",
                    )
                )
            return json.dumps(
                {"questions": [q.model_dump() for q in trimmed[:3]]},
                ensure_ascii=False,
                indent=2,
            )
        if issues:
            data = {**(data if isinstance(data, dict) else {}), "_validation_issues": issues[:5]}
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
    """互动编剧：业务域剧本 + 结构域 TODO 沙盒（JSON 双域输出）。"""

    agent_id = "ScenarioAgent"
    display_name = "ScenarioAgent"
    role = "互动编剧 · Domain/Structure 沙盒"

    def system_prompt(self, hints: PersonaHints) -> str:
        grit = hints.grit_level or "中等"
        preamble = _domain_structure_system_preamble(agent_label="ScenarioAgent（互动编剧）", hints=hints)
        return f"""{preamble}

## domain_narrative（业务域）写作指导
结合学生兴趣世界观，用**剧本/任务**形式描述业务场景与使命；要有角色、冲突、目标。
- **绝对禁止** 代码、TODO、变量名、数据结构/算法专有名词。
- story + mission 合计 120～220 字。

## structure_logic（结构域）写作指导
剥离全部故事后，给出严谨 CS 描述与可运行代码骨架：
- problem_formalization：形式化输入输出
- data_structures：明确列出所需结构（如单调栈、优先队列）
- code_framework：Python3，15～35 行，关键逻辑处 `// TODO: …`（抗挫折 {grit}，分步 hint 不泄露完整答案）
- 易错点嵌入 TODO：{hints.error_preference or '边界处理'}
- coding_ability：{hints.coding_ability or '入门'}
- 必须含 time/space 复杂度及 correctness_proof 论证要点

## JSON Schema（严格遵守字段名）
{SCENARIO_DOMAIN_STRUCTURE_SCHEMA}"""

    def temperature(self) -> float:
        return 0.5

    def max_tokens(self) -> int:
        return 2200

    def output_format(self) -> str:
        return "domain_structure_json"

    def normalize_output(self, raw: str, *, hints: PersonaHints) -> str:
        data = _parse_json_object(raw)
        if data.get("domain_narrative") and data.get("structure_logic"):
            normalized = _normalize_domain_structure_payload(
                data,
                fallback_topic=hints.learning_goals[:32] or "实操任务",
                scenario=True,
            )
            code = str(normalized["structure_logic"].get("code_framework") or "")
            if "TODO" not in code:
                normalized["structure_logic"]["code_framework"] = (
                    code.rstrip() + "\n\n# TODO: 在此补全核心逻辑\n"
                )
            return _serialize_domain_structure(normalized)

        # 兼容旧版 Markdown 章节
        bg = ""
        mission = ""
        code = ""
        m_bg = re.search(r"##\s*剧本背景[\s\S]*?(?=##|$)", raw, re.I)
        if m_bg:
            bg = re.sub(r"^##[^\n]*\n?", "", m_bg.group(0)).strip()
        m_goal = re.search(r"##\s*任务目标[\s\S]*?(?=##|$)", raw, re.I)
        if m_goal:
            mission = re.sub(r"^##[^\n]*\n?", "", m_goal.group(0)).strip()
        m_code = re.search(r"```(?:python|py)?\s*([\s\S]*?)```", raw, re.I)
        if m_code:
            code = m_code.group(1).strip()
        if not code:
            code = "# TODO: 在此补全核心逻辑\ndef solve():\n    pass\n"

        normalized = _normalize_domain_structure_payload(
            {
                "domain_narrative": {
                    "headline": "实操剧本",
                    "story": bg or raw[:400],
                    "mission": mission or "完成叙事中的核心挑战",
                    "illustration_hint": hints.interest_theme(),
                },
                "structure_logic": {
                    "problem_formalization": "（由旧版剧本迁移）",
                    "data_structures": [],
                    "code_framework": code,
                    "step_hints": ["先明确输入输出", "再补全核心循环", "最后处理边界"],
                    "time_complexity": "待分析",
                    "space_complexity": "待分析",
                    "correctness_proof": "待补全",
                },
            },
            fallback_topic=hints.learning_goals[:32] or "实操任务",
            scenario=True,
        )
        return _serialize_domain_structure(normalized)


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
