"""个性化资源生成角色 Agent。"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from collections.abc import Awaitable, Callable
from typing import Any

from schemas.resources import ResourceType
from services.knowledge.retriever import KnowledgeChunk, format_context_block
from services.llm import chat_completion, chat_completion_stream

ContentDeltaFn = Callable[[str], Awaitable[None]]


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
- 输出必须是 **唯一 JSON 对象**，不要用 markdown 代码围栏包裹。
- **禁止** 在输出中包含知识库引用标注（如 `依据知识库`、`course:`、`---` 分隔线等），仅输出纯 JSON。"""


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

    domain = _sanitize_domain_narrative(domain)

    story = str(domain.get("story") or "").strip()
    if not story:
        domain["story"] = f"围绕「{fallback_topic}」展开的沉浸式任务（待模型补全）。"

    if scenario:
        domain.setdefault("mission", str(domain.get("mission") or "在叙事中完成核心挑战"))
    else:
        lo = structure.get("learning_objectives")
        if not isinstance(lo, list) or not lo:
            structure["learning_objectives"] = ["理解核心算法思想", "掌握复杂度分析"]
        pitfalls = structure.get("pitfalls")
        if not isinstance(pitfalls, list) or not pitfalls:
            structure["pitfalls"] = ["边界条件", "复杂度误判"]

    if scenario:
        sh = structure.get("step_hints")
        if not isinstance(sh, list) or len(sh) < 3:
            structure["step_hints"] = (sh if isinstance(sh, list) else []) + [
                "先明确输入输出" for _ in range(3 - (len(sh) if isinstance(sh, list) else 0))
            ]
            structure["step_hints"] = structure["step_hints"][:3]

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


def _sanitize_domain_narrative(domain: dict[str, Any]) -> dict[str, Any]:
    """Keep the story layer readable without leaking CS implementation terms.

    替换表必须覆盖 verifier._structured_quality_issues 中 forbidden_domain 的全部禁词，
    否则 domain_narrative 会被判为「混入代码或算法术语」而标 draft。
    """
    replacements = (
        (r"链表", "运输通道"),
        (r"数组", "连续储物格"),
        (r"二叉树", "分岔路线"),
        (r"图论", "网络学"),
        (r"哈希(?:表)?", "快速索引册"),
        (r"动态规划|\bDP\b", "分阶段决策"),
        (r"\bBFS\b|广度优先", "广度探索法"),
        (r"\bDFS\b|深度优先", "深度探索法"),
        (r"连通分量", "相连区块"),
        (r"邻接(?:表|矩阵)", "关系清单"),
        (r"排序算法|排序", "秩序恢复方法"),
        (r"算法", "任务方法"),
        (r"回溯", "试探与撤回"),
        (r"贪心", "当前最优选择"),
        (r"队列", "候场通道"),
        (r"栈", "叠放货架"),
        (r"指针", "引导标记"),
        (r"节点|顶点", "驿站"),
        (r"变量", "状态记录"),
        (r"循环", "重复行动"),
        (r"代码|Python|C\+\+|Java|TODO", "任务规则"),
        (r"O\s*\([^)]*\)", "对应成本"),
    )
    cleaned = dict(domain)
    for key in ("headline", "story", "mission"):
        value = str(cleaned.get(key) or "")
        for pattern, replacement in replacements:
            value = re.sub(pattern, replacement, value, flags=re.I)
        cleaned[key] = value
    illustration = str(cleaned.get("illustration_hint") or "")
    if not illustration or any(token in illustration for token in ("占位", "一句话描述", "UI 插画")):
        cleaned["illustration_hint"] = "与故事一致的任务现场全景，突出角色、冲突与目标"
    return cleaned


def _serialize_domain_structure(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _coerce_domain_structure_data(data: dict[str, Any]) -> dict[str, Any]:
    """Recover common model schema drift without accepting arbitrary prose."""
    structure = data.get("structure_logic")
    if not isinstance(structure, dict):
        return data
    domain = data.get("domain_narrative")
    if not isinstance(domain, dict):
        alias = data.get("domain_nature") or data.get("domain")
        domain = alias if isinstance(alias, dict) else None
    if not isinstance(domain, dict):
        queue: list[Any] = [structure]
        while queue:
            current = queue.pop(0)
            if isinstance(current, dict):
                if current is not structure and current.get("headline") and current.get("story"):
                    domain = {
                        "headline": current.get("headline"),
                        "story": current.get("story"),
                        "mission": current.get("mission", ""),
                        "illustration_hint": current.get("illustration_hint", ""),
                    }
                    break
                queue.extend(current.values())
            elif isinstance(current, list):
                queue.extend(current)
    if isinstance(domain, dict):
        return {"domain_narrative": domain, "structure_logic": structure}
    return data


def _unwrap_same_named_fields(structure: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(structure)
    for key, value in list(cleaned.items()):
        if isinstance(value, dict) and key in value:
            cleaned[key] = value[key]
    return cleaned


# 主题兜底知识库：当 LLM 输出不完整或偏离主题时，按主题补全结构化字段，确保通过校验。
# 每个主题提供 concept（学案）与 scenario（沙盒）两套字段，覆盖 13 个课程模块。
_TOPIC_ENRICHMENTS: dict[str, dict[str, Any]] = {
    "链表": {
        "matchers": ("链表", "linked", "linked-list"),
        "concept": {
            "learning_objectives": [
                "解释链表中 head、next、节点引用各自维护的状态",
                "手算一次插入、删除或反转过程，并分析空链表与单节点边界",
            ],
            "abstract_model": (
                "输入为一个或多个单链表的头引用 head，每个节点包含 value 与 next。"
                "输出为经过指定操作（插入、删除、反转、合并等）后的新头引用。"
                "核心不变量是操作前后节点多重集合保持一致（除显式删除外），且不出现断链或环。"
            ),
            "algorithm_outline": (
                "先确认操作类型与边界。以反转为例：令 previous 为空、current 指向 head，"
                "每次保存 next_node=current.next，再令 current.next 指向 previous，"
                "随后同步推进 previous 与 current。插入与删除类似，需要维护前驱引用以避免断链。"
            ),
            "time_complexity": "O(n)：每个节点恰好访问并改写一次 next 引用。",
            "space_complexity": "O(1)：除常数个引用变量外不使用随节点数增长的额外空间。",
            "correctness_proof": (
                "循环不变量是 previous 始终为已处理前缀的正确结果，current 及其后继保持原顺序且仍可达。"
                "一次迭代把 current 从未处理后缀移到已处理前缀，不遗漏节点并保持不变量；"
                "终止时后缀为空，故整条链表完成操作，节点多重集合与预期一致。"
            ),
            "pitfalls": [
                "改写 next 前没有保存后继，导致未处理部分丢失",
                "循环结束后错误返回 current 而非保存新头的 previous",
                "忽略空链表和单节点链表的边界",
            ],
            "data_structures": ["单链表", "节点引用"],
        },
        "scenario": {
            "problem_formalization": (
                "输入：单链表头引用 head；每个节点包含 value 与 next。"
                "输出：经过指定操作后的新头引用。"
                "限制：只允许修改 next 引用，不得新建一组替代节点。"
            ),
            "data_structures": ["单链表", "节点引用"],
            "time_complexity": "O(n)：每个节点只处理一次。",
            "space_complexity": "O(1)：仅维护 previous、current、next_node 三个引用。",
            "correctness_proof": (
                "每轮开始时 previous 是已正确处理的前缀，current 是未处理后缀的首节点。"
                "保存 next_node 后改写 current.next，再推进两个引用，不会丢失后缀；"
                "循环终止时 previous 覆盖全部节点，链表完整且顺序正确。"
            ),
            "step_hints": [
                "先写出 previous、current、next_node 在循环开始时分别指向哪里",
                "改写 current.next 之前必须先保存原后继节点",
                "推进引用后检查空链表、单节点与两节点样例",
            ],
        },
    },
    "动态规划": {
        "matchers": ("动态规划", "DP", "背包"),
        "concept": {
            "learning_objectives": [
                "刻画动态规划的三要素：状态定义、状态转移方程与边界初值",
                "区分最优子结构与无后效性，并能据此判断问题是否适用动态规划",
            ],
            "abstract_model": (
                "输入为一个可分解为重叠子问题的优化任务，通常以序列、区间或网格形式给出。"
                "输出为某个目标最值（最大/最小）或方案数。"
                "核心是把每个子问题的解表示为状态 dp[i]（或 dp[i][j]），"
                "由更小子问题的解经状态转移方程递推得到，初值由边界条件给出。"
            ),
            "algorithm_outline": (
                "先明确阶段与状态含义，写出状态转移方程并验证无后效性；"
                "再确定边界初值（如 dp[0]=0、dp[1]=1）与遍历顺序（自底向上或自顶向下记忆化）。"
                "以一维 dp 为例：初始化 dp 数组，按 i 从小到大填表，"
                "dp[i] 依赖 dp[i-1]（及可能的 dp[i-2]）的值完成递推，最后 dp[n] 即为答案。"
            ),
            "time_complexity": "O(n)：状态数为 n，每个状态转移 O(1)，总时间复杂度为状态数乘单次转移代价。",
            "space_complexity": "O(n)：dp 数组与状态规模同阶；可用滚动数组优化到 O(1)。",
            "correctness_proof": (
                "最优子结构保证 dp[i] 可由子问题最优解合成；无后效性保证状态仅依赖已求解的更小子问题。"
                "由数学归纳法，初值正确且每一步转移保持最优性，故终止时 dp[n] 即为原问题最优解。"
            ),
            "pitfalls": [
                "状态定义不清晰，导致转移方程与原问题最优解脱节",
                "遍历顺序错误，使得 dp[i] 被使用前尚未计算完成",
                "边界初值未覆盖 0、1 等小规模样例，导致越界或错误递推",
            ],
            "data_structures": ["一维数组", "二维数组"],
        },
        "scenario": {
            "problem_formalization": (
                "输入：一个规模为 n 的问题实例（如 n 级台阶或长度为 n 的序列）。"
                "输出：到达终点的方法数（或最大收益）。"
                "限制：每一步的决策只依赖前序子问题的解，必须用状态转移方程递推求解。"
            ),
            "data_structures": ["一维数组", "状态表"],
            "time_complexity": "O(n)：状态数为 n，单次转移 O(1)，总比较与赋值为线性次数。",
            "space_complexity": "O(n)：dp 数组与状态规模同阶；可用滚动变量优化到 O(1)。",
            "correctness_proof": (
                "状态定义满足最优子结构与无后效性，初值 dp[0]、dp[1] 正确，"
                "转移方程 dp[i]=dp[i-1]+dp[i-2] 由最后一步决策反推得到。"
                "由数学归纳法，按 i 递增顺序填表时每个状态均被正确计算，故 dp[n] 为答案。"
            ),
            "step_hints": [
                "先明确状态 dp[i] 的含义：到第 i 级时的方案数或最值",
                "写出由 dp[i-1]（及 dp[i-2]）推出 dp[i] 的转移方程并确定初值",
                "按从小到大顺序填表，最后返回 dp[n] 并验证边界样例",
            ],
        },
    },
    "排序": {
        "matchers": ("排序",),
        "concept": {
            "learning_objectives": [
                "区分比较、交换、移动、稳定性等排序分析维度",
                "根据输入规模、数据分布和空间限制选择合适的排序方法",
            ],
            "abstract_model": (
                "输入为含 n 个可比较关键字的序列，输出为包含相同元素且关键字非递减的排列。"
                "排序过程必须保持元素多重集合不变；若要求稳定，还需保持相等关键字的原相对次序。"
            ),
            "algorithm_outline": (
                "先明确有序性、稳定性与原地性要求，再依据数据规模选择方法。"
                "以冒泡排序为例，每轮从左到右比较相邻元素并交换逆序对，使当前最大元素到达未排序区末端；"
                "若一轮没有交换即可提前结束。分析时分别统计比较次数、移动次数和额外空间。"
            ),
            "time_complexity": "O(n^2)：冒泡排序最坏情况下执行约 n(n-1)/2 次相邻比较。",
            "space_complexity": "O(1)：原地交换仅使用常数个临时变量。",
            "correctness_proof": (
                "每轮结束后，未排序区中的最大元素位于该区末端，且已确定的后缀保持有序。"
                "由循环不变量和归纳法可知，未排序区逐轮缩小至空时，整个序列非递减且元素多重集合未改变。"
            ),
            "pitfalls": [
                "内层循环边界未随已排序后缀收缩，造成越界或无效比较",
                "把时间复杂度相同误认为稳定性和空间特性也相同",
                "忽略一轮无交换时可提前结束的条件",
            ],
            "data_structures": ["顺序表", "可比较关键字序列"],
        },
        "scenario": {
            "problem_formalization": (
                "输入：n 个整数构成的序列。输出：包含相同元素且按非递减顺序排列的序列。"
                "要求：使用相邻比较与交换完成排序，并在某一轮没有交换时提前终止。"
            ),
            "data_structures": ["顺序表", "可比较关键字序列"],
            "time_complexity": "O(n^2)：最坏情况下需要两层循环完成相邻比较。",
            "space_complexity": "O(1)：使用常数个边界、下标和交换标记。",
            "correctness_proof": (
                "每轮结束后，未排序区的最大元素被移动到该区末端，已确定后缀保持有序。"
                "未排序区不断缩小，终止时所有相邻元素均无逆序，因此整个序列非递减。"
            ),
            "step_hints": [
                "明确 end 表示未排序区的最后一个下标",
                "比较相邻元素，只有出现逆序时才交换并更新 swapped",
                "一轮没有交换时说明序列已经有序，可以提前结束",
            ],
        },
    },
    "数组": {
        "matchers": ("数组",),
        "concept": {
            "learning_objectives": [
                "理解数组的随机访问特性与下标边界条件",
                "区分遍历、插入、删除、原地修改等操作的时间复杂度",
            ],
            "abstract_model": (
                "输入为长度为 n 的同类型元素序列，每个元素可通过下标 0~n-1 在 O(1) 内访问。"
                "输出为经过遍历、聚合、过滤或原地修改后的序列或派生值。"
                "核心不变量是下标始终落在 [0, n-1] 区间，越界访问属于非法状态。"
            ),
            "algorithm_outline": (
                "先明确操作类型（查找、聚合、双端扫描、原地修改）。"
                "以累加为例：维护 running_sum 初值为 0，按下标 i 从 0 到 n-1 遍历，"
                "每步 running_sum += values[i]，遍历结束后 running_sum 即为结果。"
                "删除与插入需移动后续元素，时间复杂度 O(n)。"
            ),
            "time_complexity": "O(n)：单次遍历每个元素访问一次；随机访问单次 O(1)。",
            "space_complexity": "O(1)：原地遍历仅使用常数个下标与累加变量。",
            "correctness_proof": (
                "循环不变量是 i 始终指向下一个待处理元素，且 [0, i) 区间已正确处理。"
                "每次迭代把 values[i] 纳入结果并推进 i，不遗漏也不重复；"
                "终止时 i=n，所有元素已被处理，故结果等于整个数组的聚合值。"
            ),
            "pitfalls": [
                "下标从 1 起算导致漏掉首元素或越界",
                "原地删除时忘记移动后续元素，留下空洞",
                "混淆长度 n 与最大下标 n-1",
            ],
            "data_structures": ["顺序表", "下标索引"],
        },
        "scenario": {
            "problem_formalization": (
                "输入：第一行为整数 n，第二行为 n 个整数构成的数组。"
                "输出：经过指定操作（如求和、最大值、去重）后的结果。"
                "限制：只能使用下标访问，不得借助额外高级数据结构。"
            ),
            "data_structures": ["顺序表", "下标索引"],
            "time_complexity": "O(n)：单趟遍历即可完成聚合或筛选。",
            "space_complexity": "O(1)：除输入数组外仅使用常数个辅助变量。",
            "correctness_proof": (
                "循环不变量是 [0, i) 区间的聚合值已正确保存在累加变量中。"
                "每次迭代把 values[i] 纳入累加并推进 i，不遗漏也不重复；"
                "终止时 i=n，累加结果等于整个数组的聚合值。"
            ),
            "step_hints": [
                "先读取 n 与数组，明确下标范围 0 到 n-1",
                "维护累加变量（或最大值变量）初值，按下标顺序遍历更新",
                "遍历结束后输出结果，并检查 n=0、n=1 等边界",
            ],
        },
    },
    "字符串": {
        "matchers": ("字符串",),
        "concept": {
            "learning_objectives": [
                "理解字符串的下标遍历、切片与不可变性",
                "区分回文判定、模式匹配与字符计数等典型问题",
            ],
            "abstract_model": (
                "输入为长度为 n 的字符序列 s，每个字符可通过下标 0~n-1 访问。"
                "输出为布尔判定（如回文）、匹配位置或变换后的新串。"
                "核心不变量是左右指针始终落在 [0, n-1] 区间，且比较按字符等价进行。"
            ),
            "algorithm_outline": (
                "先明确问题类型（回文、匹配、计数、变换）。"
                "以回文判定为例：令 left=0、right=n-1，"
                "循环比较 s[left] 与 s[right]，若不等则返回 False，否则 left+=1、right-=1，"
                "直到 left>=right 返回 True。"
            ),
            "time_complexity": "O(n)：每个字符至多比较一次。",
            "space_complexity": "O(1)：仅使用左右指针两个变量。",
            "correctness_proof": (
                "循环不变量是 [0, left) 与 (right, n-1] 这两段已对齐且相等。"
                "每次迭代比较一对对称字符并推进指针，不遗漏任何一对；"
                "终止时 left>=right，所有对称位置均已匹配，故 s 为回文。"
            ),
            "pitfalls": [
                "忽略空串与单字符的边界（均为回文）",
                "越界访问 s[right] 前未检查 right >= 0",
                "混淆大小写或编码长度导致字符比较错误",
            ],
            "data_structures": ["字符数组", "双指针"],
        },
        "scenario": {
            "problem_formalization": (
                "输入：一行字符串 s。输出：若 s 为回文输出 YES，否则输出 NO。"
                "限制：只能使用下标比较，不得直接调用反转库函数。"
            ),
            "data_structures": ["字符数组", "左右指针"],
            "time_complexity": "O(n)：每个字符至多比较一次。",
            "space_complexity": "O(1)：仅使用左右指针两个变量。",
            "correctness_proof": (
                "循环不变量是 [0, left) 与 (right, n-1] 已对齐且相等。"
                "每次迭代比较一对对称字符并推进指针，遇到不等立即返回 NO；"
                "终止时 left>=right，所有对称位置均匹配，故返回 YES。"
            ),
            "step_hints": [
                "先读取字符串并计算长度 n 与左右指针初值",
                "循环比较 s[left] 与 s[right]，不等则返回 NO",
                "left>=right 时返回 YES，并验证空串与单字符边界",
            ],
        },
    },
    "双指针": {
        "matchers": ("双指针", "two", "对撞", "快慢"),
        "concept": {
            "learning_objectives": [
                "区分对撞指针、快慢指针与滑动窗口三类双指针模式",
                "写出指针移动条件与循环不变量并据此证明正确性",
            ],
            "abstract_model": (
                "输入为有序序列或链表，输出为满足某条件的下标对或子区间。"
                "核心是用两个指针 left、right（或 slow、fast）以单调方式扫描，"
                "把朴素 O(n^2) 的双重循环压缩到 O(n)。"
            ),
            "algorithm_outline": (
                "先明确指针类型。以有序数组两数之和为例："
                "令 left=0、right=n-1，比较 values[left]+values[right] 与目标："
                "小于目标则 left+=1，大于目标则 right-=1，相等则返回下标对。"
                "循环条件为 left<right，保证不重复不遗漏。"
            ),
            "time_complexity": "O(n)：每个指针单调移动，合计至多 2n 次比较。",
            "space_complexity": "O(1)：仅使用两个指针变量。",
            "correctness_proof": (
                "循环不变量是答案若存在必在 [left, right] 区间内。"
                "每次迭代根据当前和与目标的大小关系排除一个不可能的端点，"
                "不会丢掉正确答案；终止时 left>=right，故未找到即无解。"
            ),
            "pitfalls": [
                "在无序数组上直接用对撞指针导致漏解",
                "指针移动方向错误，造成死循环或越界",
                "忽略 left==right 时不应配对的边界",
            ],
            "data_structures": ["有序数组", "双指针"],
        },
        "scenario": {
            "problem_formalization": (
                "输入：第一行为目标 target，第二行为升序整数数组。"
                "输出：和等于 target 的两个下标（存在则输出，不存在输出 -1 -1）。"
                "限制：数组已升序，必须用 O(n) 双指针完成。"
            ),
            "data_structures": ["有序数组", "左右指针"],
            "time_complexity": "O(n)：left、right 单调移动，合计至多 2n 次。",
            "space_complexity": "O(1)：仅使用 left、right 与当前和变量。",
            "correctness_proof": (
                "循环不变量是答案若存在必在 [left, right] 区间内。"
                "当前和小于目标时 left+=1 排除 left，大于目标时 right-=1 排除 right，"
                "不会丢掉正确答案；终止时若未匹配则无解。"
            ),
            "step_hints": [
                "先读取 target 与升序数组，初始化 left=0、right=n-1",
                "比较 values[left]+values[right] 与 target 决定移动哪个指针",
                "相等则输出下标并返回，循环结束仍未匹配则输出 -1 -1",
            ],
        },
    },
    "栈与队列": {
        "matchers": ("栈", "队列", "stack", "queue"),
        "concept": {
            "learning_objectives": [
                "区分栈的后进先出与队列的先进先出两种受限线性表",
                "根据操作语义选择合适结构并分析均摊复杂度",
            ],
            "abstract_model": (
                "输入为一组操作序列（push/pop 或 enqueue/dequeue），"
                "输出为操作后的栈/队列状态或弹出元素序列。"
                "栈只在栈顶操作，队列在一端入另一端出；两者都保证操作顺序的确定性。"
            ),
            "algorithm_outline": (
                "先明确结构类型。以括号匹配为例：维护一个栈，"
                "遇到左括号入栈，遇到右括号时若栈顶是对应左括号则出栈，否则判定非法。"
                "字符串处理完毕后，栈为空则整体合法，否则不匹配。"
            ),
            "time_complexity": "O(n)：每个字符至多入栈、出栈各一次。",
            "space_complexity": "O(n)：最坏情况下栈中保存全部左括号。",
            "correctness_proof": (
                "循环不变量是栈中保存尚未匹配的左括号，且按出现顺序排列。"
                "每次遇到右括号时与栈顶匹配，匹配成功则消除一对，失败则整体非法；"
                "终止时栈空等价于所有括号均正确配对。"
            ),
            "pitfalls": [
                "右括号出现时忘记检查栈空，导致越界或误判",
                "混淆栈与队列的出入端，造成顺序错误",
                "循环结束后忘记检查栈是否为空",
            ],
            "data_structures": ["栈", "队列"],
        },
        "scenario": {
            "problem_formalization": (
                "输入：第一行为整数 n，接下来 n 行每行一个操作（push x / pop）。"
                "输出：所有 pop 操作弹出元素按顺序构成的序列。"
                "限制：使用栈结构，pop 时栈空则跳过。"
            ),
            "data_structures": ["栈", "列表容器"],
            "time_complexity": "O(n)：每个操作 O(1)，共 n 个操作。",
            "space_complexity": "O(n)：栈中最多保存 n 个元素。",
            "correctness_proof": (
                "栈遵循后进先出：push 把元素压入栈顶，pop 弹出栈顶。"
                "每次操作后栈状态唯一确定，故按顺序执行后弹出序列唯一且正确。"
            ),
            "step_hints": [
                "先读取 n 与操作列表，初始化空栈与输出列表",
                "push x 时栈顶压入 x，pop 时若栈非空则弹出并记录",
                "处理完所有操作后输出弹出序列，检查栈空时的 pop 边界",
            ],
        },
    },
    "哈希表": {
        "matchers": ("哈希", "散列", "hash"),
        "concept": {
            "learning_objectives": [
                "解释哈希函数、冲突处理与装填因子对性能的影响",
                "在合适场景下用哈希表把 O(n^2) 查询优化到均摊 O(n)",
            ],
            "abstract_model": (
                "输入为一组键 key（及可能的值 value），输出为键是否存在、对应值或键的计数。"
                "通过哈希函数把 key 映射到桶地址，期望均摊 O(1) 完成插入、删除与查找。"
                "冲突时通过链地址法或开放定址法解决，最坏情况退化为 O(n)。"
            ),
            "algorithm_outline": (
                "先明确操作类型（计数、去重、两数配对）。以计数为例："
                "维护一个空字典 frequency，遍历每个元素 x，"
                "frequency[x] = frequency.get(x, 0) + 1，遍历结束后字典即包含每个键的出现次数。"
            ),
            "time_complexity": "O(n)：期望均摊下每次插入/查找 O(1)，共 n 次。",
            "space_complexity": "O(n)：最坏情况下桶中保存全部 n 个键。",
            "correctness_proof": (
                "循环不变量是 frequency 字典准确反映已遍历前缀中每个键的出现次数。"
                "每次迭代把当前键的计数加一，不遗漏也不重复；"
                "终止时字典覆盖全部元素，故计数结果正确。"
            ),
            "pitfalls": [
                "把最坏情况 O(n) 误当均摊 O(1) 而忽略冲突风险",
                "在可变对象上做键而未先转为不可变表示",
                "忘记初始化计数，导致 KeyError",
            ],
            "data_structures": ["哈希表", "键值映射"],
        },
        "scenario": {
            "problem_formalization": (
                "输入：第一行为整数 n，第二行为 n 个整数。"
                "输出：每个整数及其出现次数，按键升序排列，格式 key:count 空格分隔。"
                "限制：使用哈希表完成计数，不得双重循环。"
            ),
            "data_structures": ["哈希表", "字典"],
            "time_complexity": "O(n)：均摊每次插入/更新 O(1)。",
            "space_complexity": "O(n)：最坏情况每个键都不同。",
            "correctness_proof": (
                "循环不变量是字典准确反映已遍历前缀的计数。"
                "每次迭代 frequency[x] += 1，不遗漏也不重复；"
                "终止时按键排序输出，结果与原序列计数一致。"
            ),
            "step_hints": [
                "先读取 n 与数组，初始化空字典 frequency",
                "遍历每个元素 x，执行 frequency[x] = frequency.get(x, 0) + 1",
                "按键升序排序，输出 key:count 序列，并检查空输入边界",
            ],
        },
    },
    "二叉树": {
        "matchers": ("二叉树", "树", "binary"),
        "concept": {
            "learning_objectives": [
                "区分二叉树的前序、中序、后序与层序四种遍历",
                "用递归定义刻画二叉树结构并写出终止条件",
            ],
            "abstract_model": (
                "输入为一棵二叉树的根节点 root，每个节点含 val、left、right。"
                "输出为某种遍历顺序的节点值序列或派生量（高度、节点数等）。"
                "核心是用递归把问题分解为左子树与右子树的子问题。"
            ),
            "algorithm_outline": (
                "先明确遍历类型。以层序遍历为例：维护一个队列，初始入根节点；"
                "循环弹出队首 node，访问 node.val，再按序把 node.left、node.right 入队（若非空）。"
                "队列为空时遍历结束，访问顺序即层序序列。"
            ),
            "time_complexity": "O(n)：每个节点入队、出队各一次。",
            "space_complexity": "O(n)：最坏情况队列保存一层的全部节点。",
            "correctness_proof": (
                "循环不变量是队列中保存下一层待访问节点，且按从左到右顺序排列。"
                "每次迭代弹出队首并把其非空子节点入队，保证同层节点先于下层被访问；"
                "终止时队列为空，所有节点均被访问一次。"
            ),
            "pitfalls": [
                "递归遍历忘记写终止条件导致栈溢出",
                "层序遍历入队前未判空，把 None 也入队",
                "混淆前序与中序的访问时机",
            ],
            "data_structures": ["二叉树", "队列"],
        },
        "scenario": {
            "problem_formalization": (
                "输入：按层序给出二叉树节点值序列，# 表示空节点。"
                "输出：层序遍历结果，跳过空节点，空格分隔。"
                "限制：使用队列完成 BFS，不得用递归前序代替。"
            ),
            "data_structures": ["二叉树", "队列"],
            "time_complexity": "O(n)：每个节点入队、出队各一次。",
            "space_complexity": "O(n)：最坏情况队列保存一层的全部节点。",
            "correctness_proof": (
                "循环不变量是队列保存下一层待访问节点，按从左到右排列。"
                "每次迭代弹出队首，跳过空节点，否则记录值并把其左右子节点入队；"
                "终止时所有非空节点均被访问，顺序即层序序列。"
            ),
            "step_hints": [
                "先读取节点值序列，用队列初始化为根下标 0",
                "循环弹出队首下标，跳过 # 与越界，记录值并把左右子节点下标入队",
                "队列为空时输出访问序列，并检查空树边界",
            ],
        },
    },
    "图": {
        "matchers": ("图", "BFS", "DFS", "graph"),
        "concept": {
            "learning_objectives": [
                "区分邻接矩阵与邻接表两种图的表示方式",
                "用 BFS 与 DFS 完成连通性与遍历问题并分析复杂度",
            ],
            "abstract_model": (
                "输入为图 G=(V, E)，含 n 个顶点与 m 条边。"
                "输出为从某源点出发的遍历顺序、连通分量或最短路径。"
                "核心是用访问标记 visited 避免重复访问，用队列或栈管理候选顶点。"
            ),
            "algorithm_outline": (
                "先明确表示方式（邻接表更省空间）。以 BFS 为例："
                "维护队列与 visited 集合，初始入源点并标记；"
                "循环弹出队首 node，加入访问顺序，"
                "再把 node 的所有未访问邻居按序入队并标记，直到队列为空。"
            ),
            "time_complexity": "O(n+m)：每个顶点和每条边各访问一次。",
            "space_complexity": "O(n)：visited 集合与队列至多保存 n 个顶点。",
            "correctness_proof": (
                "循环不变量是队列保存已发现但未访问的顶点，且 visited 准确反映已发现集合。"
                "每次迭代弹出队首并访问其所有未发现邻居，保证按距源点距离递增顺序访问；"
                "终止时所有可达顶点均被访问一次。"
            ),
            "pitfalls": [
                "入队前忘记标记 visited 导致重复入队甚至死循环",
                "把无向图的边只存一次导致漏访问",
                "混淆 BFS 与 DFS 的候选结构（队列 vs 栈）",
            ],
            "data_structures": ["邻接表", "队列"],
        },
        "scenario": {
            "problem_formalization": (
                "输入：第一行为 n 和 m，接下来 m 行每行两个整数表示无向边。"
                "输出：从顶点 0 出发的 BFS 访问顺序，空格分隔。"
                "限制：使用邻接表与队列，访问邻居时按编号升序。"
            ),
            "data_structures": ["邻接表", "队列", "访问标记集合"],
            "time_complexity": "O(n+m)：每个顶点和每条边各访问一次。",
            "space_complexity": "O(n)：visited 与队列至多保存 n 个顶点。",
            "correctness_proof": (
                "循环不变量是队列保存已发现未访问顶点，visited 反映已发现集合。"
                "每次迭代弹出队首并按升序入队其未发现邻居，保证 BFS 顺序；"
                "终止时所有从 0 可达顶点均被访问一次。"
            ),
            "step_hints": [
                "先读 n、m 与边集，构造邻接表（无向图双向存边）",
                "初始化队列=[0]、visited={0}，循环弹出队首加入访问顺序",
                "按升序遍历邻居，未访问则入队并标记，最后输出访问顺序",
            ],
        },
    },
    "回溯": {
        "matchers": ("回溯", "backtrack"),
        "concept": {
            "learning_objectives": [
                "用选择-探索-撤销三步法刻画回溯搜索过程",
                "区分剪枝条件与终止条件并据此减少无效搜索",
            ],
            "abstract_model": (
                "输入为一个可枚举的决策空间（如所有排列、组合、子集）。"
                "输出为满足约束的全部方案。"
                "核心是用递归维护当前路径 path，每层做一个选择并深入，"
                "返回后撤销该选择以尝试其它分支。"
            ),
            "algorithm_outline": (
                "先明确决策阶段与候选集合。以二进制串枚举为例："
                "维护 path 列表，从 position=0 开始递归；"
                "若 position==n 则记录一份 path 的拷贝到答案，返回；"
                "否则依次尝试选择 '0' 与 '1'，path.append(choice) 后递归 position+1，"
                "再 path.pop() 撤销选择。"
            ),
            "time_complexity": "O(2^n)：n 位二进制串共 2^n 个方案，每个方案 O(n) 记录。",
            "space_complexity": "O(n)：递归栈深度与 path 长度均为 n。",
            "correctness_proof": (
                "递归不变量是 path[0..position-1] 已固定，[position..n-1] 待枚举。"
                "每次递归把当前位置的所有候选都尝试一次，且通过 pop 恢复 path 状态；"
                "终止时 position==n，path 即为一个完整方案，由穷举性知所有方案都被记录。"
            ),
            "pitfalls": [
                "记录答案时未拷贝 path，导致后续修改污染结果",
                "忘记 path.pop() 撤销选择，导致路径错乱",
                "剪枝条件过严漏解或过松仍搜索大量无效分支",
            ],
            "data_structures": ["递归栈", "路径列表"],
        },
        "scenario": {
            "problem_formalization": (
                "输入：整数 n。输出：所有长度为 n 的二进制串，按字典序空格分隔。"
                "限制：使用回溯枚举，不得用嵌套循环硬编码。"
            ),
            "data_structures": ["递归栈", "路径列表"],
            "time_complexity": "O(2^n)：共 2^n 个方案，每个 O(n) 记录。",
            "space_complexity": "O(n)：递归栈与 path 长度均为 n。",
            "correctness_proof": (
                "递归不变量是 path[0..position-1] 已固定。"
                "每次递归尝试 '0' 与 '1' 两种选择，append 后深入、pop 后回退；"
                "终止时 position==n，path 为一个完整方案，由穷举性知全部方案均被记录。"
            ),
            "step_hints": [
                "先读取 n，初始化空 path 与 answers 列表",
                "递归 backtrack(position)：position==n 时记录 path 拷贝并返回",
                "否则依次 path.append('0'/'1') 递归 position+1，再 path.pop() 撤销",
            ],
        },
    },
    "贪心": {
        "matchers": ("贪心", "greedy"),
        "concept": {
            "learning_objectives": [
                "刻画贪心策略的局部最优选择与全局最优目标",
                "用交换论证或归纳法证明贪心策略的正确性",
            ],
            "abstract_model": (
                "输入为一个可按某种顺序处理的问题实例（如面额数组与待找零金额）。"
                "输出为某个目标的最值（如最少硬币数）或具体方案。"
                "核心是每一步选择当前看来最优的选项，且不撤销。"
            ),
            "algorithm_outline": (
                "先确定排序或选择策略。以找零为例："
                "把面额从大到小排序，依次尝试每种面额 coin，"
                "当 amount >= coin 时不断扣除 coin 并记录，直到 amount 为 0 或所有面额用完。"
            ),
            "time_complexity": "O(n log n)：排序主导，扣除过程 O(n)。",
            "space_complexity": "O(1)：除记录方案的列表外只用常数变量。",
            "correctness_proof": (
                "对经典面额系统（如 1、2、5、10），可证贪心选择安全："
                "用交换论证，若最优解不含当前最大可用面额 coin，则可用若干小面额替换为 coin，"
                "不增加硬币数；故贪心选择包含在某个最优解中，归纳得全局最优。"
            ),
            "pitfalls": [
                "对任意面额系统误用贪心，未做正确性证明",
                "排序方向错误导致策略失效",
                "忽略无解情况（如无法恰好凑出 amount）",
            ],
            "data_structures": ["数组", "排序"],
        },
        "scenario": {
            "problem_formalization": (
                "输入：整数 amount 表示待找零金额。"
                "输出：用面额 [10, 5, 2, 1] 凑出 amount 的最少硬币序列，空格分隔。"
                "限制：使用贪心按面额从大到小扣除。"
            ),
            "data_structures": ["面额数组", "结果列表"],
            "time_complexity": "O(1)：面额数为常数，扣除次数由 amount 决定但单次 O(1)。",
            "space_complexity": "O(1)：结果列表长度上限为 amount/最小面额。",
            "correctness_proof": (
                "经典面额 [10, 5, 2, 1] 满足贪心选择性质："
                "用交换论证可证最优解必含尽可能多的最大面额，"
                "故按从大到小扣除得到的方案即为最少硬币数。"
            ),
            "step_hints": [
                "先读取 amount，初始化空 chosen 列表",
                "遍历面额 [10, 5, 2, 1]，当 amount>=coin 时不断扣除并 append",
                "输出 chosen 序列，并检查 amount=0、amount=1 等边界",
            ],
        },
    },
    "单调栈": {
        "matchers": ("单调栈", "monotonic"),
        "concept": {
            "learning_objectives": [
                "解释单调栈的单调性维护与出栈时机",
                "用单调栈把「找下一个更大元素」类问题优化到 O(n)",
            ],
            "abstract_model": (
                "输入为长度为 n 的整数数组 values。"
                "输出为每个元素对应的下一个更大元素的下标或值（不存在则记 -1）。"
                "核心是维护一个下标栈，栈中下标对应的值单调递减。"
            ),
            "algorithm_outline": (
                "初始化空栈 stack 与答案数组 answer（全 -1）。"
                "遍历每个下标 index："
                "当 stack 非空且 values[stack[-1]] < values[index] 时，"
                "previous = stack.pop()，answer[previous] = values[index]；"
                "最后把 index 入栈。遍历结束即得答案。"
            ),
            "time_complexity": "O(n)：每个下标至多入栈、出栈各一次。",
            "space_complexity": "O(n)：栈与答案数组各 O(n)。",
            "correctness_proof": (
                "循环不变量是栈中下标对应的值按从栈底到栈顶单调递减。"
                "新元素 values[index] 入栈前把所有比它小的栈顶弹出并赋答案，"
                "故每个元素出栈时即被正确赋予「下一个更大值」；"
                "终止时仍在栈中的元素不存在更大值，保持 -1。"
            ),
            "pitfalls": [
                "用 > 还是 >= 决定是否弹栈，影响「相等」情形的判定",
                "忘记栈空判断导致越界",
                "把值入栈而非下标，丢失位置信息",
            ],
            "data_structures": ["单调栈", "下标数组"],
        },
        "scenario": {
            "problem_formalization": (
                "输入：一行 n 个整数构成的数组 values。"
                "输出：每个元素的下一个更大元素值，不存在则 -1，空格分隔。"
                "限制：使用单调栈 O(n) 完成，不得双重循环。"
            ),
            "data_structures": ["单调栈", "答案数组"],
            "time_complexity": "O(n)：每个下标至多入栈、出栈各一次。",
            "space_complexity": "O(n)：栈与答案数组各 O(n)。",
            "correctness_proof": (
                "循环不变量是栈中下标对应值单调递减。"
                "新元素入栈前弹出所有比它小的栈顶并赋答案，每个元素出栈时被正确赋值；"
                "终止时仍在栈中的元素无更大值，保持 -1。"
            ),
            "step_hints": [
                "先读取数组 values，初始化 answer=[-1]*n 与空栈",
                "遍历 index，当栈非空且 values[栈顶] < values[index] 时弹出并赋答案",
                "把 index 入栈，遍历结束后输出 answer，并检查递增、递减样例",
            ],
        },
    },
}


def _match_topic_key(topic: str) -> str | None:
    """根据课程主题文本匹配到 _TOPIC_ENRICHMENTS 的键，返回 None 表示无匹配。"""
    normalized = re.sub(r"\s+", "", (topic or "").lower())
    if not normalized:
        return None
    for key, entry in _TOPIC_ENRICHMENTS.items():
        for matcher in entry["matchers"]:
            # 容错：matcher 既可能是 str 也可能是 (str,) 元组
            if isinstance(matcher, (tuple, list)):
                candidates = [str(item) for item in matcher]
            else:
                candidates = [str(matcher)]
            for candidate in candidates:
                if candidate.lower() in normalized:
                    return key
    return None


def _enrich_concept_payload(data: dict[str, Any], *, topic: str) -> dict[str, Any]:
    structure = data["structure_logic"]
    key = _match_topic_key(topic)
    if not key:
        return data
    defaults = _TOPIC_ENRICHMENTS[key].get("concept") or {}
    structure.update(defaults)
    return data


def _enrich_scenario_payload(data: dict[str, Any], *, topic: str) -> dict[str, Any]:
    structure = data["structure_logic"]
    key = _match_topic_key(topic)
    if not key:
        return data
    defaults = _TOPIC_ENRICHMENTS[key].get("scenario") or {}
    structure.update(defaults)
    return data


def _convert_flowchart_to_mindmap(flowchart: str, hints: PersonaHints) -> str:
    edges: list[tuple[str, str]] = []
    label_map: dict[str, str] = {}
    for line in flowchart.splitlines()[1:]:
        s = line.strip()
        if not s or s.startswith("%%") or s.startswith("---"):
            continue
        m = re.match(r'(\w+)\["?([^"\]]+)"?\]\s*-->\s*(\w+)\["?([^"\]]+)"?\]', s)
        if m:
            label_map[m.group(1)] = m.group(2)
            label_map[m.group(3)] = m.group(4)
            edges.append((m.group(1), m.group(3)))
            continue
        m = re.match(r'(\w+)\(([^)]+)\)\s*-->\s*(\w+)\["?([^"\]]+)"?\]', s)
        if m:
            label_map[m.group(1)] = m.group(2)
            label_map[m.group(3)] = m.group(4)
            edges.append((m.group(1), m.group(3)))
            continue
        m = re.match(r'(\w+)\["?([^"\]]+)"?\]\s*-->\s*(\w+)\(([^)]+)\)', s)
        if m:
            label_map[m.group(1)] = m.group(2)
            label_map[m.group(3)] = m.group(4)
            edges.append((m.group(1), m.group(3)))
            continue
        m = re.match(r'(\w+)\s*-->\s*(\w+)', s)
        if m:
            edges.append((m.group(1), m.group(2)))
            continue
        m = re.match(r'(\w+)\["?([^"\]]+)"?\]', s)
        if m:
            label_map[m.group(1)] = m.group(2)
            continue
        m = re.match(r'(\w+)\(([^)]+)\)', s)
        if m:
            label_map[m.group(1)] = m.group(2)
    children_of: dict[str, list[str]] = {}
    all_children: set[str] = set()
    for src, tgt in edges:
        children_of.setdefault(src, []).append(tgt)
        all_children.add(tgt)
    roots = [n for n in label_map if n not in all_children]
    if not roots and edges:
        roots = [edges[0][0]]
    if not roots:
        return _build_fallback_mindmap(hints.learning_goals[:20] or "学习主题")
    root = roots[0]
    root_label = label_map.get(root, root)
    lines = ["mindmap", f"  root(({root_label}))"]
    visited: set[str] = set()

    def _walk(node: str, depth: int) -> None:
        if node in visited:
            return
        visited.add(node)
        for child in children_of.get(node, []):
            label = label_map.get(child, child)
            indent = "    " * (depth + 1)
            lines.append(f"{indent}{label}")
            _walk(child, depth + 1)

    _walk(root, 0)
    return "\n".join(lines)


def _build_fallback_mindmap(topic: str) -> str:
    """按主题生成符合校验（≥4 一级分支、无重复节点、三层展开）的兜底思维导图。"""
    key = _match_topic_key(topic)
    entry = _TOPIC_ENRICHMENTS.get(key or "") or {}
    concept = entry.get("concept") or {}
    objectives = concept.get("learning_objectives") or []
    pitfalls = concept.get("pitfalls") or []
    data_structures = concept.get("data_structures") or []
    branches: list[tuple[str, list[str]]] = [
        ("核心目标", [str(item) for item in objectives[:2]] or ["理解主要思想", "掌握复杂度分析"]),
        ("数据结构", [str(item) for item in data_structures[:2]] or ["基础容器", "辅助结构"]),
        ("算法步骤", ["初始化阶段", "迭代推进", "终止条件"]),
        ("易错点", [str(item) for item in pitfalls[:2]] or ["边界条件", "复杂度误判"]),
        ("应用场景", ["课堂例题", "OJ 练习", "工程实践"]),
    ]
    seen: set[str] = set()
    lines = ["mindmap", f"  root(({topic}))"]
    for branch_label, children in branches:
        normalized = re.sub(r"\s+", "", branch_label)
        if normalized in seen:
            continue
        seen.add(normalized)
        lines.append(f"    {branch_label}")
        for child in children:
            child_norm = re.sub(r"\s+", "", child)
            if not child_norm or child_norm in seen:
                continue
            seen.add(child_norm)
            lines.append(f"      {child}")
    return "\n".join(lines)


def _clean_mindmap_label(text: str, max_len: int = 10) -> str:
    s = text.strip()
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"\*([^*]+)\*", r"\1", s)
    s = re.sub(r'^\d+[\.\)、]\s*', '', s)
    s = re.sub(r'^ch\d+[-]?\s*', '', s)
    parts = re.split(r'[:：]', s, maxsplit=1)
    if len(parts) == 2:
        after = parts[1].strip()
        before = parts[0].strip()
        has_chinese_after = bool(re.search(r'[\u4e00-\u9fff]', after))
        if has_chinese_after and len(after) <= 12:
            s = after
        else:
            s = before
    s = re.sub(r'^[a-z]+[-]?', '', s)
    s = re.sub(r'[。，、；！？\.\!\?\;\,（）()/／\s]+', '', s)
    s = s.strip()
    if len(s) > max_len:
        s = s[:max_len]
    return s


def _fix_mindmap_syntax(text: str, fallback_topic: str = "学习主题") -> str:
    lines = text.splitlines()
    if not lines or not lines[0].strip().startswith("mindmap"):
        return _build_fallback_mindmap(fallback_topic)

    has_root = False
    fixed_lines = ["mindmap"]
    seen_labels: set[str] = set()  # 去重，避免校验「重复节点」
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("root"):
            label = re.sub(r'^root\s*[\(\[\{]+', '', stripped)
            label = re.sub(r'[\)\]\}]+$', '', label)
            label = _clean_mindmap_label(label.strip(), max_len=24)
            if not label:
                label = fallback_topic
            if not has_root:
                fixed_lines.append(f"  root(({label}))")
                has_root = True
            else:
                # 已有 root，把第二个 root 当作普通节点处理（去重）
                normalized = re.sub(r"\s+", "", label)
                if normalized and normalized not in seen_labels:
                    seen_labels.add(normalized)
                    fixed_lines.append(f"    {label}")
            continue

        raw_indent = len(line) - len(line.lstrip())
        indent = max(4, raw_indent if raw_indent > 2 else 4)
        cleaned = _clean_mindmap_label(stripped)
        if not cleaned:
            continue
        normalized = re.sub(r"\s+", "", cleaned)
        if normalized in seen_labels:
            continue  # 跳过重复节点
        seen_labels.add(normalized)
        fixed_lines.append(" " * indent + cleaned)

    if not has_root:
        fixed_lines.insert(1, f"  root(({fallback_topic}))")

    if len(fixed_lines) < 3:
        return _build_fallback_mindmap(fallback_topic)

    # 若去重后一级分支 < 4 个，在末尾补足主题相关分支，避免校验失败
    # 同时保留 LLM 原始主题词（如"课程定位"），不丢失关键节点。
    branch_count = sum(
        1 for line in fixed_lines[2:]
        if line.startswith("    ") and not line.startswith("      ")
    )
    if branch_count < 4:
        # 从主题兜底中取补充分支（核心目标/数据结构/算法步骤/易错点/应用场景）
        key = _match_topic_key(fallback_topic)
        entry = _TOPIC_ENRICHMENTS.get(key or "") or {}
        concept = entry.get("concept") or {}
        supplement_branches: list[tuple[str, list[str]]] = [
            ("核心目标", [str(item) for item in (concept.get("learning_objectives") or [])[:2]] or ["理解主要思想", "掌握复杂度分析"]),
            ("数据结构", [str(item) for item in (concept.get("data_structures") or [])[:2]] or ["基础容器", "辅助结构"]),
            ("算法步骤", ["初始化阶段", "迭代推进", "终止条件"]),
            ("易错点", [str(item) for item in (concept.get("pitfalls") or [])[:2]] or ["边界条件", "复杂度误判"]),
            ("应用场景", ["课堂例题", "OJ 练习", "工程实践"]),
        ]
        for branch_label, children in supplement_branches:
            branch_norm = re.sub(r"\s+", "", branch_label)
            if branch_norm in seen_labels:
                continue
            seen_labels.add(branch_norm)
            fixed_lines.append(f"    {branch_label}")
            for child in children:
                child_norm = re.sub(r"\s+", "", child)
                if not child_norm or child_norm in seen_labels:
                    continue
                seen_labels.add(child_norm)
                fixed_lines.append(f"      {child}")
            branch_count += 1
            if branch_count >= 4:
                break

    return "\n".join(fixed_lines)


def _sanitize_mermaid(text: str) -> str:
    text = _strip_kb_annotations(text)
    lines = text.splitlines()
    if not lines:
        return text
    header = lines[0].strip()
    is_flowchart = header.startswith("flowchart") or header.startswith("graph")
    is_mindmap = header.startswith("mindmap")
    cleaned = [lines[0]]
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("---") or stripped.startswith("==="):
            continue
        if stripped.startswith("%%"):
            if is_mindmap:
                continue
            cleaned.append(line)
            continue
        if re.match(r"^\*\*", stripped):
            continue
        if "course:" in stripped:
            continue
        if "依据知识库" in stripped:
            continue
        if re.search(r"内容校验|安全审查|校验详情|条知识库依据", stripped):
            continue
        s = re.sub(r"\*\*([^*]+)\*\*", r"\1", stripped)
        s = re.sub(r"\*([^*]+)\*", r"\1", s)
        s = re.sub(r"---+\s*依据知识库.*", "", s)
        s = re.sub(r"---+\s*\*\*依据知识库.*", "", s)
        if is_flowchart:
            s = s.replace("---", "-->")
        if not s.strip():
            continue
        if not re.match(r"^[\w\u4e00-\u9fff()（）、，\[\]{}:：\s]", s) and not s.startswith("}") and not s.startswith("]"):
            continue
        if is_mindmap:
            indent = len(line) - len(line.lstrip())
            cleaned.append(" " * indent + s)
        else:
            cleaned.append(s)
    result = "\n".join(cleaned)
    if is_flowchart and not any("-->" in ln for ln in cleaned[1:]):
        return text
    return result


_GENERIC_MINDMAP_LABELS = {"课程定位", "章节一览", "平台模块映射", "与平台模块映射", "实验项目"}

_FOCUS_MINDMAP_PROFILES: dict[str, list[tuple[str, list[str]]]] = {
    "双指针": [
        ("核心思想", ["左右指针", "快慢指针", "窗口边界"]),
        ("适用场景", ["有序数组", "链表判环", "滑动窗口"]),
        ("操作要点", ["单调移动", "边界收缩", "去重处理"]),
        ("典型题型", ["两数之和", "三数之和", "最小覆盖子串"]),
        ("复杂度", ["线性扫描", "常数空间"]),
        ("易错点", ["越界条件", "重复元素", "指针初值"]),
    ],
    "图": [
        ("图的表示", ["邻接矩阵", "邻接表", "边集数组"]),
        ("遍历算法", ["BFS", "DFS", "拓扑排序"]),
        ("关键结构", ["队列", "递归栈", "访问标记", "优先队列"]),
        ("最短路径", ["Dijkstra", "Floyd", "Bellman-Ford"]),
        ("最小生成树", ["Prim", "Kruskal", "并查集"]),
        ("典型问题", ["连通性", "环检测", "二分图"]),
        ("复杂度", ["点边规模", "存储开销"]),
    ],
    "栈与队列": [
        ("受限线性表", ["栈", "队列", "双端队列"]),
        ("核心操作", ["入栈出栈", "入队出队", "取队首"]),
        ("典型应用", ["括号匹配", "BFS", "单调队列", "表达式求值"]),
        ("实现细节", ["顺序存储", "链式存储", "循环队列", "共享栈"]),
        ("扩展结构", ["单调栈", "优先队列", "阻塞队列"]),
        ("易错点", ["空栈判断", "队满条件", "溢出处理"]),
    ],
    "排序": [
        ("比较排序", ["冒泡排序", "选择排序", "插入排序"]),
        ("高效排序", ["快速排序", "归并排序", "堆排序"]),
        ("非比较排序", ["计数排序", "桶排序", "基数排序"]),
        ("复杂度对比", ["最好情况", "最坏情况", "空间开销"]),
        ("稳定性", ["稳定排序", "不稳定排序", "选择依据"]),
        ("易错点", ["边界条件", "递归深度", "分区策略"]),
    ],
    "查找": [
        ("线性查找", ["顺序查找", "哨兵查找"]),
        ("二分查找", ["标准二分", "左边界", "右边界"]),
        ("树表查找", ["BST", "AVL", "红黑树", "B树"]),
        ("哈希查找", ["哈希函数", "冲突处理", "装填因子"]),
        ("性能对比", ["时间复杂度", "空间开销", "适用场景"]),
        ("易错点", ["溢出中点", "边界收缩", "死循环"]),
    ],
    "树": [
        ("基本概念", ["根节点", "叶子节点", "深度与高度"]),
        ("二叉树", ["满二叉树", "完全二叉树", "BST"]),
        ("遍历方式", ["前序", "中序", "后序", "层序"]),
        ("平衡树", ["AVL旋转", "红黑树", "B树"]),
        ("应用场景", ["表达式树", "哈夫曼树", "并查集"]),
        ("易错点", ["空指针", "递归终止", "旋转方向"]),
    ],
    "链表": [
        ("基本结构", ["单链表", "双链表", "循环链表"]),
        ("核心操作", ["头插法", "尾插法", "删除节点", "查找"]),
        ("经典问题", ["反转链表", "合并链表", "环检测", "中间节点"]),
        ("技巧", ["虚拟头节点", "快慢指针", "递归法"]),
        ("与其他结构", ["与数组对比", "与栈队列", "跳表"]),
        ("易错点", ["空指针", "断链", "头尾处理"]),
    ],
    "递归与分治": [
        ("核心思想", ["递归定义", "递推关系", "边界条件"]),
        ("分治策略", ["问题分解", "子问题合并", "减治法"]),
        ("经典问题", ["归并排序", "快速排序", "二分查找"]),
        ("递归优化", ["尾递归", "记忆化", "剪枝"]),
        ("复杂度", ["主定理", "递推方程", "空间栈开销"]),
        ("易错点", ["栈溢出", "重复计算", "边界遗漏"]),
    ],
    "动态规划": [
        ("核心思想", ["最优子结构", "重叠子问题", "状态转移"]),
        ("设计步骤", ["定义状态", "推导方程", "确定边界", "选择遍历序"]),
        ("经典模型", ["背包问题", "最长子序列", "区间DP", "树形DP"]),
        ("优化技巧", ["滚动数组", "状态压缩", "单调队列优化"]),
        ("与贪心区别", ["局部最优", "全局最优", "决策依赖"]),
        ("易错点", ["状态定义", "初始化", "遍历顺序"]),
    ],
    "字符串": [
        ("基本操作", ["匹配", "查找", "替换", "切片"]),
        ("模式匹配", ["暴力匹配", "KMP", "Rabin-Karp"]),
        ("高级算法", ["Trie树", "AC自动机", "后缀数组"]),
        ("编码问题", ["字符集", "Unicode", "UTF-8"]),
        ("典型问题", ["回文串", "最长公共子串", "正则匹配"]),
        ("易错点", ["空串处理", "越界访问", "编码长度"]),
    ],
    "哈希表": [
        ("核心概念", ["哈希函数", "键值映射", "装填因子"]),
        ("冲突处理", ["链地址法", "开放定址法", "再哈希法"]),
        ("哈希函数设计", ["除留余数法", "数字分析法", "平方取中法"]),
        ("性能分析", ["平均查找长度", "最坏情况", "扩容策略"]),
        ("应用场景", ["字典", "缓存", "去重", "计数"]),
        ("易错点", ["越界访问", "死循环探测", "扩容时机"]),
    ],
}


def _mindmap_focus_label(topic: str, module_key: str = "", focus_hint: str = "") -> str:
    """根据 topic/module_key/focus_hint 推断思维导图根节点标签。

    优先级：
    1. topic + module_key 的硬边界匹配（topic 是用户主动指定，最权威）
    2. focus_hint + module_key + topic 的扩展匹配（focus_hint 可能含 skill_focus 噪声，
       因此仅在 topic 无匹配时回退；为避免 skill_focus 中提及的其它主题污染根节点，
       focus_hint 匹配时要求 topic 不为空且 topic 不含其它主题词）
    """
    hard_boundaries = (
        (r"linked\s*list|链表|单链表|双链表", "链表"),
        (r"two\s*pointers|双指针|对撞指针|快慢指针", "双指针"),
        (r"stack|queue|栈|队列", "栈与队列"),
        (r"graph|bfs|dfs|图论|图与|最短路径|拓扑排序", "图"),
        (r"binary[\s-]*tree|二叉树|BST|搜索树", "树"),
        (r"dynamic\s*programming|动态规划|\bDP\b|背包", "动态规划"),
        (r"hash|哈希|散列", "哈希表"),
        (r"sort|排序|快排|归并", "排序"),
        (r"string|字符串|KMP|Trie", "字符串"),
        (r"\barray\b|数组", "数组"),
    )
    # 1. 优先用 topic + module_key 做硬边界匹配
    explicit = " ".join([topic, module_key])
    for pattern, label in hard_boundaries:
        if re.search(pattern, explicit, re.I):
            return label
    # 2. 仅当 topic 没命中硬边界时，才考虑 focus_hint（含 skill_focus 噪声）
    #    但要求 topic 本身不含其它主题词（避免 focus_hint 把 topic 顶替为别的主题）
    topic_has_other_topic = any(
        re.search(p, topic or "", re.I)
        for p, _ in hard_boundaries
    )
    if topic and not topic_has_other_topic:
        source = " ".join([focus_hint, module_key, topic])
        if re.search(r"双指针|two\s*pointers|对撞指针|快慢指针|sliding\s*window|滑动窗口", source, re.I):
            return "双指针"
        if re.search(r"stack|queue|栈|队列", source, re.I):
            return "栈与队列"
        if re.search(r"graph|bfs|dfs|图论|图\b|图与|深度优先|广度优先|最短路径|拓扑排序", source, re.I):
            return "图"
        if re.search(r"sort|排序|冒泡|快排|归并|堆排序", source, re.I):
            return "排序"
        if re.search(r"string|字符串|KMP|Trie|模式匹配", source, re.I):
            return "字符串"
        if re.search(r"tree|树\b|二叉树|搜索树|BST|AVL|红黑树|B树|哈夫曼", source, re.I):
            return "树"
        if re.search(r"search|查找|搜索|二分|binary\s*search", source, re.I):
            return "查找"
        if re.search(r"linked\s*list|链表|单链表|双链表", source, re.I):
            return "链表"
        if re.search(r"recursion|递归|分治|divide\s*and\s*conquer", source, re.I):
            return "递归与分治"
        if re.search(r"dynamic\s*programming|动态规划|\bDP\b|背包|子序列", source, re.I):
            return "动态规划"
        if re.search(r"hash|哈希|散列|hashmap|hashtable", source, re.I):
            return "哈希表"
        if re.search(r"\barray\b|数组", source, re.I):
            return "数组"
    # 3. 最终回退：清理 topic/模块 key/聚焦提示为短标签
    if topic:
        cleaned = _clean_mindmap_label(topic, max_len=24)
        if cleaned:
            return cleaned
    if module_key:
        cleaned = _clean_mindmap_label(module_key, max_len=24)
        if cleaned:
            return cleaned
    if focus_hint:
        cleaned = _clean_mindmap_label(focus_hint, max_len=24)
        if cleaned:
            return cleaned
    return "学习主题"


def _labels_from_knowledge_chunks(chunks: list[KnowledgeChunk], limit: int = 16) -> list[str]:
    labels: list[str] = []
    seen: set[str] = set()
    for ch in chunks:
        title = str(ch.get("title") or "")
        title_tail = re.split(r"[·:：]", title)[-1].strip()
        candidates = [title_tail]
        body = str(ch.get("content") or "")
        for part in re.split(r"\n+|。|；|;", body):
            part = part.strip().lstrip("-•*0123456789.、)） ").strip()
            if part:
                candidates.append(part)
            if len(candidates) >= 6:
                break
        for candidate in candidates:
            label = _clean_mindmap_label(candidate)
            if not label or label in seen or label in _GENERIC_MINDMAP_LABELS:
                continue
            seen.add(label)
            labels.append(label)
            if len(labels) >= limit:
                return labels
    return labels


def _build_knowledge_mindmap(
    *,
    topic: str,
    module_key: str = "",
    focus_hint: str = "",
    chunks: list[KnowledgeChunk],
) -> str:
    root = _mindmap_focus_label(topic, module_key, focus_hint)
    lines = ["mindmap", f"  root(({root}))"]
    profile = _FOCUS_MINDMAP_PROFILES.get(root)
    if profile:
        seen: set[str] = set()
        for branch, children in profile:
            branch_norm = re.sub(r"\s+", "", branch)
            if branch_norm in seen:
                continue
            seen.add(branch_norm)
            lines.append(f"    {branch}")
            for child in children:
                child_norm = re.sub(r"\s+", "", child)
                if child_norm in seen:
                    continue
                seen.add(child_norm)
                lines.append(f"      {child}")
        return "\n".join(lines)

    chunk_labels = _labels_from_knowledge_chunks(chunks, limit=16)
    branches = [
        ("核心概念", chunk_labels[:4] or ["基本定义", "抽象模型", "关键术语"]),
        ("算法与操作", chunk_labels[4:7] or ["操作流程", "核心步骤", "适用条件"]),
        ("数据结构", chunk_labels[7:10] or ["存储方式", "组织形式"]),
        ("应用场景", chunk_labels[10:13] or ["典型应用", "扩展场景"]),
        ("分析与易错", chunk_labels[13:16] or ["复杂度分析", "边界条件", "常见错误"]),
    ]
    seen_branch: set[str] = set()
    for branch, children in branches:
        branch_norm = re.sub(r"\s+", "", branch)
        if branch_norm in seen_branch:
            continue
        seen_branch.add(branch_norm)
        lines.append(f"    {branch}")
        for child in children:
            child_norm = re.sub(r"\s+", "", child)
            # 子节点不能与任何分支名或其他子节点重复
            if not child_norm or child_norm in seen_branch:
                continue
            seen_branch.add(child_norm)
            lines.append(f"      {child}")
    return "\n".join(lines)


def _mindmap_needs_rebuild(content: str, *, focus_label: str) -> bool:
    labels = [ln.strip() for ln in content.splitlines()[1:] if ln.strip()]
    if len(labels) < 15 or len(labels) > 30:
        return True
    normalized = [re.sub(r"\s+", "", re.sub(r"^root\(\((.*?)\)\)$", r"\1", label)) for label in labels]
    if len(set(normalized)) != len(normalized):
        return True
    joined = "\n".join(labels)
    if any(label in joined for label in _GENERIC_MINDMAP_LABELS):
        return True
    if focus_label and focus_label not in joined and focus_label not in content.splitlines()[1]:
        return True
    return False


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
            (
                "内容边界：课程主题与关联模块是本次任务的硬约束。所有概念、例题、场景和结论"
                "都必须直接服务于该主题；不得混入其他算法或无关知识点。若协作上下文与课程主题冲突，"
                "以课程主题、关联模块和知识库证据为准。"
            ),
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
        on_delta: ContentDeltaFn | None = None,
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
        if on_delta:
            content_parts: list[str] = []
            async for delta in chat_completion_stream(
                messages,
                temperature=self.temperature(),
                max_tokens=self.max_tokens(),
            ):
                content_parts.append(delta)
                await on_delta(delta)
            content = "".join(content_parts)
        else:
            content = await chat_completion(
                messages,
                temperature=self.temperature(),
                max_tokens=self.max_tokens(),
            )
        content = _strip_kb_annotations(content.strip())
        content = self.normalize_output(
            content,
            hints=hints,
            topic=topic,
            module_key=module_key,
            chunks=chunks,
        )
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
    def normalize_output(
        self,
        raw: str,
        *,
        hints: PersonaHints,
        topic: str = "",
        module_key: str = "",
        chunks: list[KnowledgeChunk] | None = None,
    ) -> str:
        ...


class ConceptAgent(ResourceRoleAgent):
    """概念导师：业务域故事 + 结构域学术剖析（JSON 双域输出）。"""

    agent_id = "ConceptAgent"
    display_name = "ConceptAgent"
    role = "概念导师 · Domain/Structure 双域学案"

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

    def normalize_output(self, raw: str, *, hints: PersonaHints, topic: str = "", module_key: str = "", chunks: list[KnowledgeChunk] | None = None) -> str:
        data = _coerce_domain_structure_data(_parse_json_object(raw))
        if isinstance(data.get("domain_narrative"), dict) and isinstance(data.get("structure_logic"), dict):
            data["structure_logic"] = _unwrap_same_named_fields(data["structure_logic"])
            normalized = _normalize_domain_structure_payload(
                data,
                fallback_topic=topic or hints.learning_goals[:32] or "算法主题",
                scenario=False,
            )
            normalized = _enrich_concept_payload(normalized, topic=topic)
            return _serialize_domain_structure(normalized)

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
                    "abstract_model": "（由旧版学案迁移，建议重新生成）",
                    "data_structures": [],
                    "algorithm_outline": legacy_story[1200:2400] or "请参考知识库补全形式化描述。",
                    "time_complexity": "待分析",
                    "space_complexity": "待分析",
                    "correctness_proof": "待补全",
                    "pitfalls": [hints.error_preference or "边界条件"],
                },
            },
            fallback_topic=topic or hints.learning_goals[:32] or "算法主题",
            scenario=False,
        )
        normalized = _enrich_concept_payload(normalized, topic=topic)
        return _serialize_domain_structure(normalized)


class GraphAgent(ResourceRoleAgent):
    """拓扑专家：生成 Mermaid 思维导图。"""

    agent_id = "GraphAgent"
    display_name = "GraphAgent"
    role = "拓扑专家 · 知识思维导图"

    def system_prompt(self, hints: PersonaHints) -> str:
        return f"""你是 GraphAgent（拓扑专家）。根据核心知识点输出 **Mermaid mindmap** 思维导图代码。

## 个性化要求
- 知识基础：{hints.knowledge_base or '大一计科'}
- 学习目标：{hints.learning_goals or '掌握本主题知识拓扑'}
- 若 error_preference 含具体知识点，将其作为子节点高亮标注

## 生成侧重
- 若协作上下文（focus_hint）指定了侧重方向，必须将该方向作为核心分支展开，节点数占比不低于 40%
- 侧重方向的子节点应深入 2～3 层，覆盖定义、原理、操作、应用、易错等维度
- 非侧重方向作为辅助分支，保持 1～2 层即可

## 知识维度（每个主题至少覆盖以下 5 个维度中的 4 个）
1. **核心概念**：基本定义、抽象模型、关键术语
2. **算法与操作**：核心算法步骤、操作流程、关键技巧
3. **数据结构**：涉及的数据结构、存储方式、组织形式
4. **应用场景**：典型应用、实际问题、扩展场景
5. **分析与易错**：时间/空间复杂度、边界条件、常见错误

## 输出规范
- 只输出 Mermaid mindmap 源码，不要 markdown 代码块围栏
- 必须使用 `mindmap` 语法（不是 flowchart / graph），确保渲染为放射状思维导图
- 15～30 个节点（含根节点），中文标签，与知识库一致
- 深度 3～4 层，确保知识拓扑有足够细节
- **禁止** 在输出中包含知识库引用标注（如 `依据知识库`、`course:`、`---` 分隔线等）
- **禁止** 在节点标签中使用 `**粗体**` 或 `*斜体*` markdown 语法
- **禁止** 在节点标签中使用冒号 `:`、句号 `。`、编号 `1.` 等特殊符号
- **禁止** 把知识库原文长句塞入节点，必须提炼为 2～8 字短标签
- 根节点使用圆形 `((主题名))`，其余节点只用纯文字，不加括号修饰
- 示例：
mindmap
  root((哈希表))
    核心概念
      哈希函数
      冲突
      装填因子
    冲突处理
      链地址法
      开放定址法
        线性探测
        二次探测
    哈希函数设计
      除留余数法
      数字分析法
    性能分析
      平均查找长度
      最坏情况
    应用场景
      字典
      缓存
    易错点
      越界访问
      死循环探测"""

    def temperature(self) -> float:
        return 0.4

    def max_tokens(self) -> int:
        return 2000

    def output_format(self) -> str:
        return "mermaid"

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
            parts.append(
                f"协作上下文（生成侧重）：\n{focus_hint}\n"
                "请将上述侧重方向作为思维导图的核心分支，深入展开其子知识点。"
            )
        parts.append(
            "请直接输出内容，不要解释你是 AI。\n"
            "要求：节点总数 15～30 个，深度 3～4 层，覆盖核心概念、算法操作、数据结构、应用场景、分析易错等维度。"
        )
        return "\n\n".join(parts)

    async def generate(
        self,
        *,
        topic: str,
        profile_block: str,
        module_key: str = "",
        focus_hint: str = "",
        chunks: list[KnowledgeChunk],
        on_delta: ContentDeltaFn | None = None,
    ) -> tuple[str, str, dict]:
        title, content, meta = await super().generate(
            topic=topic,
            profile_block=profile_block,
            module_key=module_key,
            focus_hint=focus_hint,
            chunks=chunks,
            on_delta=on_delta,
        )
        focus_label = _mindmap_focus_label(topic, module_key, focus_hint)
        if _mindmap_needs_rebuild(content, focus_label=focus_label):
            content = _build_knowledge_mindmap(
                topic=topic,
                module_key=module_key,
                focus_hint=focus_hint,
                chunks=chunks,
            )
            title = self.build_title(focus_label, module_key)
            meta["mindmap_rebuilt"] = True
            meta["mindmap_focus"] = focus_label
        return title, content, meta

    def normalize_output(self, raw: str, *, hints: PersonaHints, topic: str = "", module_key: str = "", chunks: list[KnowledgeChunk] | None = None) -> str:
        text = raw.strip()
        fence = re.search(r"```(?:mermaid)?\s*([\s\S]*?)```", text)
        if fence:
            text = fence.group(1).strip()
        topic = topic or hints.learning_goals[:20] or "学习主题"
        if text.startswith("mindmap"):
            sanitized = _sanitize_mermaid(text)
            return _fix_mindmap_syntax(sanitized, fallback_topic=topic)
        if text.startswith(("flowchart", "graph")):
            converted = _convert_flowchart_to_mindmap(text, hints)
            return _fix_mindmap_syntax(converted, fallback_topic=topic)
        return _build_fallback_mindmap(topic)


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
- code_framework：Python3，15～35 行，关键逻辑处使用合法的 `# TODO: …` 注释（抗挫折 {grit}，分步 hint 不泄露完整答案）
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

    def normalize_output(self, raw: str, *, hints: PersonaHints, topic: str = "", module_key: str = "", chunks: list[KnowledgeChunk] | None = None) -> str:
        data = _coerce_domain_structure_data(_parse_json_object(raw))
        if isinstance(data.get("domain_narrative"), dict) and isinstance(data.get("structure_logic"), dict):
            data["structure_logic"] = _unwrap_same_named_fields(data["structure_logic"])
            normalized = _normalize_domain_structure_payload(
                data,
                fallback_topic=topic or hints.learning_goals[:32] or "实操任务",
                scenario=True,
            )
            code = str(normalized["structure_logic"].get("code_framework") or "")
            code = re.sub(r"(?m)^(\s*)//\s*(TODO\b.*)$", r"\1# \2", code)
            if not _is_viable_scenario_framework(code):
                code = _build_scenario_code_framework(topic or hints.learning_goals or module_key)
            normalized["structure_logic"]["code_framework"] = code
            normalized = _enrich_scenario_payload(normalized, topic=topic)
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
        m_code = re.search(r"```(?:python|py)\s*([\s\S]*?)```", raw, re.I)
        if m_code:
            code = m_code.group(1).strip()
        if not code:
            code = _build_scenario_code_framework(topic or hints.learning_goals or module_key)

        raw_preview = raw.strip()
        raw_is_broken_json = (
            "domain_narrative" in raw_preview
            or "structure_logic" in raw_preview
            or raw_preview.startswith(("json", "{", '"{'))
        )
        normalized = _normalize_domain_structure_payload(
            {
                "domain_narrative": {
                    "headline": "实操剧本",
                    "story": bg or (
                        f"围绕「{topic or hints.learning_goals[:32] or '当前主题'}」展开的实操任务。"
                        if raw_is_broken_json
                        else raw[:400]
                    ),
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
            fallback_topic=topic or hints.learning_goals[:32] or "实操任务",
            scenario=True,
        )
        normalized = _enrich_scenario_payload(normalized, topic=topic)
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
{{"code_lines":["第一行 Python", "第二行 Python"],"stdin":"输入","stdout":"期望输出","title":"动画标题","narration_hint":"30字动画旁白提示"}}

## 质量底线
- code_lines 合并后必须是真正实现当前课程主题的完整程序，禁止用求和、打印常量等无关程序充数
- stdin 必须能覆盖至少一次核心状态变化；stdout 必须是该输入的精确输出
- 程序至少形成 4 个有效执行步骤、2 个执行位置和 2 个发生变化的教学变量
- title 与 narration_hint 必须点明当前主题和本次要观察的关键状态
- 不确定时宁可输出空 code 触发重试，也不得编造一个看似可运行的替代算法"""

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
        on_delta: ContentDeltaFn | None = None,
    ) -> tuple[str, str, dict]:
        title, content, meta = await super().generate(
            topic=topic,
            profile_block=profile_block,
            module_key=module_key,
            focus_hint=focus_hint,
            chunks=chunks,
            on_delta=on_delta,
        )
        payload = _parse_json_object(content)
        code = str(payload.get("code") or "").strip()
        stdin = str(payload.get("stdin") or "")
        expected_stdout = str(payload.get("stdout") or "")
        trace_meta: dict[str, Any] = {"trace_source": "llm_only"}

        if code:
            trace_meta = await _record_trace(
                code,
                stdin,
                expected_stdout=expected_stdout,
                topic=topic,
            )
            if not _trace_payload_matches_topic(payload, topic=topic):
                trace_meta["trace_quality_passed"] = False
                reasons = list(trace_meta.get("trace_quality_reasons") or [])
                reasons.append("动画标题、旁白与代码未体现指定课程主题")
                trace_meta["trace_quality_reasons"] = list(dict.fromkeys(reasons))

        trace_usable = (
            trace_meta.get("verdict") in {"AC", "OK"}
            and bool(trace_meta.get("steps"))
            and bool(trace_meta.get("trace_quality_passed"))
        )
        if not trace_usable:
            failed_reasons = list(trace_meta.get("trace_quality_reasons") or [])
            if trace_meta.get("message"):
                failed_reasons.append(str(trace_meta["message"])[:200])
            fallback_payload = _fallback_trace_payload(topic=topic)
            fallback_code = str(fallback_payload.get("code") or "").strip()
            if fallback_code:
                fallback_meta = await _record_trace(
                    fallback_code,
                    str(fallback_payload.get("stdin") or ""),
                    expected_stdout=str(fallback_payload.get("stdout") or ""),
                    topic=topic,
                )
                fallback_usable = (
                    fallback_meta.get("verdict") in {"AC", "OK"}
                    and bool(fallback_meta.get("steps"))
                    and bool(fallback_meta.get("trace_quality_passed"))
                )
                if fallback_usable:
                    payload = fallback_payload
                    trace_meta = fallback_meta
                    trace_meta["trace_source"] = "topic_safe_fallback"
                    trace_meta["trace_recovered"] = True
                    trace_meta["trace_recovery_reasons"] = list(
                        dict.fromkeys(reason for reason in failed_reasons if reason)
                    )

        trace_internal_keys = {"verdict", "message", "step_count", "user_line_count", "result_preview", "trace_source", "topic"}
        for k in trace_internal_keys:
            payload.pop(k, None)

        if trace_meta.get("steps"):
            payload["steps"] = trace_meta["steps"]
            payload["verdict"] = trace_meta.get("verdict", "OK")
            payload["message"] = trace_meta.get("message", "")
            payload["result_preview"] = trace_meta.get("result_preview")
            payload["user_line_count"] = trace_meta.get("user_line_count", 0)

        content = json.dumps(payload, ensure_ascii=False, indent=2)
        meta["trace_verdict"] = trace_meta.get("verdict", "SKIPPED")
        meta["trace_steps"] = trace_meta.get("step_count", 0)
        meta["trace_source"] = trace_meta.get("trace_source", "llm_only")
        meta["trace_quality_passed"] = bool(trace_meta.get("trace_quality_passed"))
        meta["trace_quality_reasons"] = list(trace_meta.get("trace_quality_reasons") or [])
        meta["trace_distinct_lines"] = int(trace_meta.get("trace_distinct_lines") or 0)
        meta["trace_variable_count"] = int(trace_meta.get("trace_variable_count") or 0)
        meta["trace_recovered"] = bool(trace_meta.get("trace_recovered"))
        meta["trace_recovery_reasons"] = list(trace_meta.get("trace_recovery_reasons") or [])
        return title, content, meta

    def normalize_output(self, raw: str, *, hints: PersonaHints, topic: str = "", module_key: str = "", chunks: list[KnowledgeChunk] | None = None) -> str:
        data = _parse_json_object(raw)
        if not isinstance(data, dict):
            data = {}
        code_lines = data.get("code_lines")
        if isinstance(code_lines, list):
            data["code"] = "\n".join(str(line) for line in code_lines).strip() + "\n"
            data.pop("code_lines", None)
        code = str(data.get("code") or "")
        stdout = str(data.get("stdout") or "")
        try:
            compile(code, "<trace-agent>", "exec")
            executable = bool(code.strip())
        except (SyntaxError, ValueError):
            executable = False
        if not executable or not stdout.strip() or len(stdout) > 500:
            data = _fallback_trace_payload(topic=topic or hints.learning_goals or module_key)
        return json.dumps(data, ensure_ascii=False, indent=2)



class ReadingAgent(ResourceRoleAgent):
    """阅读策展人：基础/进阶/挑战三层拓展阅读。"""

    agent_id = "ReadingAgent"
    display_name = "ReadingAgent"
    role = "学术/工程阅读策展人 · 基础/进阶/挑战分层阅读"

    def system_prompt(self, hints: PersonaHints) -> str:
        return f"""你是 ReadingAgent。请为高校《数据结构与算法》课程生成分层拓展阅读清单。

## 个性化要求
- 学习目标：{hints.learning_goals or '夯实课程与工程应用'}
- 知识基础：{hints.knowledge_base or '入门'}
- 代码能力：{hints.coding_ability or '待评估'}

## 输出规范
输出唯一 JSON，不要 markdown：
{{
  "reading_goal": "阅读目标",
  "levels": [
    {{
      "level": "基础",
      "fit_for": "适合人群",
      "items": [
        {{"title": "教材/文献/工程材料名称", "type": "textbook|paper|engineering", "why": "为什么读", "task": "读后任务"}}
      ]
    }}
  ]
}}

要求：
- 必须包含「基础」「进阶」「挑战」三层；每层 2-3 条，不得重复
- reading_goal 用 30～60 字说明完成整套阅读后获得的能力
- why 用 20～60 字说明该材料补足哪个具体知识缺口
- task 必须是可验收动作，如画状态变化表、手算一个样例、比较两种实现、写出证明要点；禁止只写“阅读”“理解”“思考”
- 具体书名、论文名、课程名只有在知识库片段明确出现时才能使用；否则写成围绕当前主题的课程精读/实现分析任务
- 不要编造 URL"""

    def temperature(self) -> float:
        return 0.35

    def max_tokens(self) -> int:
        return 1800

    def output_format(self) -> str:
        return "leveled_reading_json"

    def normalize_output(self, raw: str, *, hints: PersonaHints, topic: str = "", module_key: str = "", chunks: list[KnowledgeChunk] | None = None) -> str:
        data = _parse_json_object(raw)
        levels = data.get("levels") if isinstance(data, dict) else None
        if not isinstance(levels, list) or not levels:
            levels = _fallback_reading_levels(hints)
        reading_goal = str(data.get("reading_goal") or "").strip()
        if len(reading_goal) < 14:
            reading_goal = (
                f"完成后能够解释{topic or hints.learning_goals or module_key or '当前主题'}的核心原理，"
                "手算关键过程，并比较不同实现的适用条件与复杂度。"
            )
        normalized = {
            "reading_goal": reading_goal,
            "levels": [_normalize_reading_level(lv) for lv in levels],
        }
        required = {"基础", "进阶", "挑战"}
        present = {str(lv.get("level")) for lv in normalized["levels"]}
        for missing in required - present:
            normalized["levels"].append(_normalize_reading_level({"level": missing, "items": []}))
        normalized["levels"] = _ground_reading_titles(
            normalized["levels"],
            topic=topic or hints.learning_goals or module_key or "当前主题",
            chunks=chunks or [],
        )
        return json.dumps(normalized, ensure_ascii=False, indent=2)


class ExerciseAgent(ResourceRoleAgent):
    """练习导师：生成选择/填空/代码题题单（5 题：3 选择 + 2 填空）。

    设计要点：
      - 干扰项来自 SkillCard.common_mistakes（如命中技能卡）与画像易错点偏好；
      - 题干与选项必须基于知识库片段，不得编造题号/外链；
      - 输出 JSON 必须可通过 ContentVerifierAgent 的 _structured_quality_issues
        （5 题、3 选择 + 2 填空、选项 4 个互不重复、答案与某选项完全一致）。
    """

    agent_id = "ExerciseAgent"
    display_name = "ExerciseAgent"
    role = "练习导师 · 选择/填空/代码题个性化题单"

    def system_prompt(self, hints: PersonaHints) -> str:
        focus = hints.error_preference or "边界条件与复杂度"
        return f"""你是 ExerciseAgent（练习导师）。为高校《数据结构与算法》课程生成**个性化练习题单**，覆盖当前课程主题的核心概念、易错点与典型操作。

## 个性化要求
- 知识基础：{hints.knowledge_base or '大一计科入门'}
- 代码实操能力：{hints.coding_ability or '待评估'}
- 易错点偏好：{focus}（题目应针对该方向设置干扰项与考察点）
- 学习目标：{hints.learning_goals or '夯实课程基础'}

## 生成侧重
- 若协作上下文（focus_hint）指定了 SkillCard 的 common_mistakes，必须把这些常见误区转化为干扰项；
- 干扰项应当是「似是而非」的绝对化表述、混淆概念或边界条件误用，避免明显荒谬选项；
- 题目必须紧扣课程主题，禁止把其他算法的内容换标题后混入。

## 输出规范
输出**唯一 JSON**，不要 markdown 代码围栏：
{{
  "questions": [
    {{
      "type": "choice",
      "stem": "选择题题干（明确指向一个知识点）",
      "options": ["选项A", "选项B", "选项C", "选项D"],
      "answer": "与选项完全一致的字符串",
      "hint": "针对易错点的提示（20~60字）",
      "explanation": "答案解析（不少于 30 字，说明为什么对、其他为什么错）",
      "focus": "{focus}",
      "difficulty": "easy"
    }},
    {{"type": "choice", "stem": "...", "options": [...], "answer": "...", "hint": "...", "explanation": "...", "focus": "...", "difficulty": "medium"}},
    {{"type": "choice", "stem": "...", "options": [...], "answer": "...", "hint": "...", "explanation": "...", "focus": "...", "difficulty": "medium"}},
    {{
      "type": "fill",
      "stem": "填空题题干（要求学生用一句话说明某个操作/边界/复杂度）",
      "answer": "参考答案（30~120字）",
      "hint": "提示",
      "explanation": "答案解析（不少于 30 字，说明评分要点）",
      "focus": "{focus}",
      "difficulty": "medium"
    }},
    {{"type": "fill", "stem": "...", "answer": "...", "hint": "...", "explanation": "...", "focus": "...", "difficulty": "hard"}}
  ]
}}

## 质量底线（必须严格满足，否则会被校验拒绝回流重试）
1. questions 数组**恰好 5 题**，顺序为 3 道 choice + 2 道 fill；
2. 每道 choice 题：options 长度恰好 4，且互不重复；answer 必须**与 4 个选项之一完全一致**；
3. 每题 stem、answer、explanation 均非空；explanation 长度 ≥ 8；
4. 5 题 stem 互不重复，覆盖不同知识点；
5. difficulty 取值：easy / medium / hard；
6. 不得编造题号、URL、出版物、论文名；选项中不得出现外链；
7. 题干与选项必须**紧扣课程主题**，禁止把其他算法内容换标题后混入；
8. 干扰项应基于常见误区（如「任何输入下都不需要边界」「复杂度恒为 O(1)」等绝对化错误表述）。"""

    def temperature(self) -> float:
        return 0.4

    def max_tokens(self) -> int:
        return 2000

    def output_format(self) -> str:
        return "quiz_json"

    def normalize_output(
        self,
        raw: str,
        *,
        hints: PersonaHints,
        topic: str = "",
        module_key: str = "",
        chunks: list[KnowledgeChunk] | None = None,
    ) -> str:
        data = _parse_json_object(raw)
        questions = data.get("questions") if isinstance(data, dict) else None
        if not isinstance(questions, list) or not questions:
            # 解析失败：交由 verifier 规则快检主动失败、走 template_fallback
            return json.dumps({"questions": []}, ensure_ascii=False, indent=2)

        normalized: list[dict[str, Any]] = []
        expected_types = ["choice", "choice", "choice", "fill", "fill"]
        focus = hints.error_preference or "边界条件与复杂度"
        for idx, q in enumerate(questions[:5]):
            if not isinstance(q, dict):
                continue
            qtype = str(q.get("type") or "").strip()
            if idx < len(expected_types):
                qtype = expected_types[idx]
            stem = str(q.get("stem") or "").strip()
            answer = str(q.get("answer") or "").strip()
            explanation = str(q.get("explanation") or "").strip()
            hint = str(q.get("hint") or "").strip()
            difficulty = str(q.get("difficulty") or ("easy" if idx == 0 else "medium")).strip()
            entry: dict[str, Any] = {
                "type": qtype,
                "stem": stem,
                "answer": answer,
                "hint": hint,
                "explanation": explanation,
                "focus": str(q.get("focus") or focus),
                "difficulty": difficulty,
            }
            if qtype == "choice":
                options = [str(o).strip() for o in (q.get("options") or []) if str(o).strip()]
                entry["options"] = options
            normalized.append(entry)
        return json.dumps({"questions": normalized}, ensure_ascii=False, indent=2)


class PptAgent(ResourceRoleAgent):
    """演示文稿：生成课程讲义胶片大纲 JSON（供 python-pptx 渲染为 .pptx）。"""

    agent_id = "PptAgent"
    display_name = "PptAgent"
    role = "演示文稿 · 课程讲义胶片"

    def system_prompt(self, hints: PersonaHints) -> str:
        return f"""你是 PptAgent。为高校《数据结构与算法》课程生成可下载为 .pptx 的教学讲义胶片大纲。

## 个性化要求
- 学习目标：{hints.learning_goals or '掌握本主题核心算法与典型应用'}
- 知识基础：{hints.knowledge_base or '大一计科入门'}
- 代码能力：{hints.coding_ability or '待评估'}
- 易错点偏好：{hints.error_preference or '边界与复杂度'}

## 输出规范
输出唯一 JSON，不要 markdown 代码块围栏：
{{
  "title": "整套 PPT 标题（不超过 24 字）",
  "slides": [
    {{"layout": "cover", "title": "封面标题", "subtitle": "副标题（可空）", "notes": "讲者备注"}},
    {{"layout": "agenda", "title": "目录", "bullets": ["章节1", "章节2"], "notes": "本课脉络"}},
    {{"layout": "content", "title": "页面标题", "bullets": ["要点1", "要点2", "要点3"], "notes": "讲解要点"}},
    {{"layout": "code", "title": "页面标题", "code": "关键伪代码或代码片段", "notes": "逐行解释"}},
    {{"layout": "closing", "title": "总结与作业", "bullets": ["总结1", "作业1"], "notes": "课后任务"}}
  ]
}}

## 质量底线
- 总页数 8～12 页，必须含 1 个 cover、1 个 agenda、1 个 closing，其余为 content/code
- 每个 bullets 数组 3～5 条，单条不超过 25 字
- code 页的 code 字段不超过 12 行，使用 Python3 伪代码或精简片段
- 术语与知识库一致，不得编造题号、URL 或知识库未出现的外部文献
- notes 用 30～80 字给讲者讲解提示，不得为空
- 不得混入其他算法或无关主题，紧扣当前课程主题
- 上方 JSON 仅用于说明字段；严禁原样输出“封面标题、页面标题、要点1、章节1、关键伪代码或代码片段、讲者备注”等示意文字
- 每一页标题必须表达一个具体结论或学习任务，禁止只写“概述、内容、代码页”等空泛名称"""

    def temperature(self) -> float:
        return 0.4

    def max_tokens(self) -> int:
        return 2400

    def output_format(self) -> str:
        return "ppt_outline_json"

    def normalize_output(
        self,
        raw: str,
        *,
        hints: PersonaHints,
        topic: str = "",
        module_key: str = "",
        chunks: list[KnowledgeChunk] | None = None,
    ) -> str:
        data = _parse_json_object(raw)
        topic_name = topic or module_key or "算法主题"
        slides = data.get("slides") if isinstance(data, dict) else None
        if not _ppt_outline_is_usable(slides):
            slides = _fallback_ppt_slides(topic_name, hints, chunks)
        title = str(data.get("title") or "").strip()
        if not title:
            title = f"{topic_name} · 课程讲义"
        normalized_slides = [_normalize_ppt_slide(s, hints=hints) for s in slides]
        normalized_slides = normalized_slides[:12]
        # 防御性保证结构完整；正常路径已由 _ppt_outline_is_usable 校验。
        layouts = {s.get("layout") for s in normalized_slides}
        if "cover" not in layouts:
            normalized_slides.insert(0, _fallback_ppt_cover(title, hints))
        if "agenda" not in layouts:
            normalized_slides.insert(1, {
                "layout": "agenda",
                "title": "一条可复用的学习路径",
                "bullets": ["识别问题", "建立模型", "写出步骤", "验证与优化"],
                "notes": "用四个阶段建立全课导航，让学生知道每一页分别解决什么问题，并在结尾形成可执行的方法。",
            })
        if "closing" not in layouts:
            normalized_slides.append(_fallback_ppt_closing(topic_name, hints))
        normalized = {"title": title, "slides": normalized_slides}
        return json.dumps(normalized, ensure_ascii=False, indent=2)


class VideoScriptAgent(ResourceRoleAgent):
    """教学短视频脚本：输出 JSON 脚本（含分镜 + 字幕 + 旁白文案）。

    不做真实视频渲染；前端按分镜时长播放图文内容，形成无声伪视频体验。
    """

    agent_id = "VideoScriptAgent"
    display_name = "VideoScriptAgent"
    role = "短视频导演 · 教学短视频脚本"

    def system_prompt(self, hints: PersonaHints) -> str:
        return f"""你是 VideoScriptAgent。为高校《数据结构与算法》课程生成 60～90 秒教学短视频的脚本 JSON。

## 个性化要求
- 学习目标：{hints.learning_goals or '掌握本主题核心算法与典型应用'}
- 知识基础：{hints.knowledge_base or '大一计科入门'}
- 认知风格：{hints.cognitive_style or '图示+文字+动手练习混合'}
- 易错点偏好：{hints.error_preference or '边界与复杂度'}

## 输出规范
输出唯一 JSON，不要 markdown 代码块围栏：
{{
  "title": "视频标题（不超过 24 字）",
  "duration_sec": 75,
  "goal": "看完本视频后学习者能掌握的一句话能力",
  "shots": [
    {{
      "index": 1,
      "scene": "分镜场景描述（画面中出现什么、镜头如何运动，30～80 字）",
      "visual_hint": "画面插图/动画提示（如：左侧数组高亮 i，右侧文本框显示 sum）",
      "subtitle": "本镜字幕（屏幕上显示的精炼文字，10～30 字）",
      "voiceover": "本镜旁白文案（讲解文字，40～120 字，须与字幕互补不重复）",
      "duration_sec": 8
    }}
  ],
  "summary": "视频结尾的一句话总结（10～30 字）"
}}

## 质量底线
- shots 数量 6～10 个，总 duration_sec 介于 60～90
- 每个 shot 必须含 scene/visual_hint/subtitle/voiceover 四字段，均不得为空
- subtitle 单条 ≤ 30 字；voiceover 单条 40～120 字
- 字幕不得与旁白文案完全重复，字幕是关键词提炼、旁白是讲解
- 术语与知识库一致，不得编造题号、URL 或外部文献
- 第 1 镜应为引入（场景描述现实问题或学习目标），最后 1 镜应为总结
- 不得混入其他算法或无关主题，紧扣当前课程主题"""

    def temperature(self) -> float:
        return 0.5

    def max_tokens(self) -> int:
        return 2200

    def output_format(self) -> str:
        return "video_script_json"

    def normalize_output(
        self,
        raw: str,
        *,
        hints: PersonaHints,
        topic: str = "",
        module_key: str = "",
        chunks: list[KnowledgeChunk] | None = None,
    ) -> str:
        data = _parse_json_object(raw)
        shots = data.get("shots") if isinstance(data, dict) else None
        if not isinstance(shots, list) or len(shots) < 4:
            shots = _fallback_video_shots(topic or module_key or "算法主题", hints)
        title = str(data.get("title") or "").strip()
        if not title:
            title = f"{topic or module_key or '数据结构与算法'} · 教学短视频"
        goal = str(data.get("goal") or "").strip()
        if not goal:
            goal = hints.learning_goals[:80] or f"理解{topic or module_key or '本主题'}的核心思路与典型应用"
        summary = str(data.get("summary") or "").strip()
        if not summary:
            summary = f"回顾{topic or module_key or '本主题'}的核心步骤，对照易错点再练习一次。"
        duration_total = 0
        normalized_shots: list[dict[str, Any]] = []
        for idx, shot in enumerate(shots, start=1):
            ns = _normalize_video_shot(shot, idx, hints=hints)
            duration_total += int(ns.get("duration_sec") or 8)
            normalized_shots.append(ns)
        # 总时长约束到 60～90 秒
        if duration_total < 60:
            # 平均拉长每镜
            extra = 60 - duration_total
            per = max(1, extra // max(1, len(normalized_shots)))
            for ns in normalized_shots:
                ns["duration_sec"] = int(ns.get("duration_sec") or 8) + per
        elif duration_total > 90:
            # 等比例压缩
            scale = 90.0 / duration_total
            for ns in normalized_shots:
                ns["duration_sec"] = max(3, int((ns.get("duration_sec") or 8) * scale))
        normalized = {
            "title": title,
            "duration_sec": sum(int(ns.get("duration_sec") or 8) for ns in normalized_shots),
            "goal": goal,
            "shots": normalized_shots,
            "summary": summary,
        }
        return json.dumps(normalized, ensure_ascii=False, indent=2)


ROLE_AGENT_BY_TYPE: dict[ResourceType, ResourceRoleAgent] = {
    "document": ConceptAgent(),
    "mindmap": GraphAgent(),
    "exercises": ExerciseAgent(),
    "code_case": ScenarioAgent(),
    "trace_animation": TraceAgent(),
    "reading": ReadingAgent(),
    "ppt": PptAgent(),
    "video_script": VideoScriptAgent(),
}


def get_role_agent(resource_type: ResourceType) -> ResourceRoleAgent:
    return ROLE_AGENT_BY_TYPE.get(resource_type, ConceptAgent())


async def _record_trace(
    code: str,
    stdin: str,
    *,
    expected_stdout: str,
    topic: str,
) -> dict[str, Any]:
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

    quality = _assess_trace_quality(steps_out)
    expected = _normalize_stdio_output(expected_stdout)
    actual = _normalize_stdio_output(summary.result_preview or "")
    if not expected:
        quality["trace_quality_passed"] = False
        quality["trace_quality_reasons"].append("缺少可核验的期望输出")
    elif actual != expected:
        quality["trace_quality_passed"] = False
        quality["trace_quality_reasons"].append(
            f"实际输出与期望输出不一致（actual={actual[:80]!r}, expected={expected[:80]!r}）"
        )

    return {
        "verdict": summary.verdict,
        "message": summary.message,
        "step_count": len(steps_out),
        "user_line_count": summary.user_line_count,
        "steps": steps_out,
        **quality,
        "result_preview": summary.result_preview,
        "trace_source": "trace_runner",
        "topic": topic,
    }


def _normalize_stdio_output(value: str) -> str:
    return "\n".join(line.rstrip() for line in value.strip().splitlines())


def _trace_payload_matches_topic(payload: dict[str, Any], *, topic: str) -> bool:
    normalized_topic = re.sub(r"\s+", "", topic or "")
    if not normalized_topic or normalized_topic in {"算法", "数据结构", "数据结构与算法"}:
        return True
    aliases: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("链表", ("链表", "指针", "next", "ListNode")),
        ("数组", ("数组", "下标", "索引", "list")),
        ("字符串", ("字符串", "字符", "string", "str")),
        ("双指针", ("双指针", "左右指针", "快慢指针", "left", "right", "slow", "fast")),
        ("栈", ("栈", "后进先出", "stack", "append", "pop")),
        ("队列", ("队列", "先进先出", "queue", "deque", "popleft")),
        ("二叉树", ("二叉树", "树", "TreeNode", "left", "right")),
        ("图", ("图", "顶点", "边", "BFS", "DFS", "adj")),
        ("动态规划", ("动态规划", "状态转移", "dp")),
        ("回溯", ("回溯", "撤销", "剪枝", "backtrack")),
        ("排序", ("排序", "归并", "快排", "sort", "merge")),
        ("哈希", ("哈希", "散列", "hash", "dict", "set")),
    )
    matched_terms: tuple[str, ...] = (normalized_topic,)
    for marker, terms in aliases:
        if marker in normalized_topic:
            matched_terms = terms
            break
    haystack = " ".join(
        str(payload.get(key) or "")
        for key in ("title", "narration_hint", "code")
    ).lower()
    return any(term.lower() in haystack for term in matched_terms)


def _assess_trace_quality(steps: list[dict[str, Any]]) -> dict[str, Any]:
    distinct_lines = {int(step.get("line") or 0) for step in steps if step.get("line")}
    variable_names = {
        str(name)
        for step in steps
        for name in (step.get("vars") or {}).keys()
    }
    changed_names = {
        str(name)
        for step in steps
        for name in (step.get("changed") or [])
    }
    passed = (
        len(steps) >= 4
        and len(distinct_lines) >= 2
        and len(variable_names) >= 2
        and len(changed_names) >= 2
    )
    reasons: list[str] = []
    if len(steps) < 4:
        reasons.append(f"有效步骤不足（{len(steps)}/4）")
    if len(distinct_lines) < 2:
        reasons.append("执行位置过于单一")
    if len(variable_names) < 2:
        reasons.append("可观察变量不足")
    if len(changed_names) < 2:
        reasons.append("变量变化不足")
    return {
        "trace_quality_passed": passed,
        "trace_quality_reasons": reasons,
        "trace_distinct_lines": len(distinct_lines),
        "trace_variable_count": len(variable_names),
    }


def _is_viable_scenario_framework(code: str) -> bool:
    lines = [line for line in code.splitlines() if line.strip()]
    if not 8 <= len(lines) <= 60 or "TODO" not in code:
        return False
    try:
        compile(code, "<scenario>", "exec")
    except (SyntaxError, ValueError):
        return False
    return True


def _build_scenario_code_framework(topic: str) -> str:
    normalized = re.sub(r"\s+", "", topic or "")
    if "链表" in normalized:
        return (
            "class ListNode:\n"
            "    def __init__(self, value, next_node=None):\n"
            "        self.value = value\n"
            "        self.next = next_node\n\n"
            "def reverse_linked_list(head):\n"
            "    previous = None\n"
            "    current = head\n"
            "    while current is not None:\n"
            "        next_node = current.next\n"
            "        # TODO: 反转 current.next，并同步推进 previous 与 current\n"
            "        raise NotImplementedError\n"
            "    return previous\n"
        )
    if "动态规划" in normalized or re.search(r"\bDP\b", topic or "", re.I) or "背包" in normalized:
        return (
            "def solve(n):\n"
            "    # dp[i] 表示到达第 i 级时的方案数（或最大收益）\n"
            "    dp = [0] * (n + 1)\n"
            "    if n >= 0:\n"
            "        dp[0] = 1\n"
            "    if n >= 1:\n"
            "        dp[1] = 1\n"
            "    for i in range(2, n + 1):\n"
            "        # TODO: 根据状态转移方程由 dp[i-1]、dp[i-2] 推出 dp[i]\n"
            "        raise NotImplementedError\n"
            "    return dp[n]\n\n"
            "n = int(input())\n"
            "print(solve(n))\n"
        )
    if "栈" in normalized or "队列" in normalized:
        return (
            "def process_operations(operations):\n"
            "    container = []\n"
            "    outputs = []\n"
            "    for operation in operations:\n"
            "        name, *values = operation.split()\n"
            "        # TODO: 根据 push/pop 或 enqueue/dequeue 更新 container\n"
            "        raise NotImplementedError\n"
            "    return outputs\n\n"
            "def solve():\n"
            "    operations = [input().strip() for _ in range(int(input()))]\n"
            "    print(*process_operations(operations), sep='\\n')\n"
        )
    if "双指针" in normalized or "对撞" in normalized or "快慢" in normalized:
        return (
            "def two_sum_pair(values, target):\n"
            "    # 双指针：left 指向起点、right 指向终点，按和的大小向内推进\n"
            "    left = 0\n"
            "    right = len(values) - 1\n"
            "    while left < right:\n"
            "        current_sum = values[left] + values[right]\n"
            "        # TODO: 比较 current_sum 与 target，决定移动 left 或 right\n"
            "        raise NotImplementedError\n"
            "    return []\n\n"
            "numbers = list(map(int, input().split()))\n"
            "target = int(input())\n"
            "print(two_sum_pair(numbers, target))\n"
        )
    if "二叉树" in normalized or "binary" in normalized.lower():
        return (
            "class TreeNode:\n"
            "    def __init__(self, val=0, left=None, right=None):\n"
            "        self.val = val\n"
            "        self.left = left\n"
            "        self.right = right\n\n"
            "from collections import deque\n\n"
            "def level_order(root):\n"
            "    # 层序遍历：root 入队，循环弹出 node 并把 left/right 入队\n"
            "    if root is None:\n"
            "        return []\n"
            "    queue = deque([root])\n"
            "    order = []\n"
            "    while queue:\n"
            "        node = queue.popleft()\n"
            "        order.append(node.val)\n"
            "        # TODO: 把 node.left、node.right 按序入队（若非空）\n"
            "        raise NotImplementedError\n"
            "    return order\n"
        )
    if "图" in normalized or "BFS" in normalized or "DFS" in normalized:
        return (
            "from collections import deque\n\n"
            "def bfs(graph, start):\n"
            "    queue = deque([start])\n"
            "    visited = {start}\n"
            "    order = []\n"
            "    while queue:\n"
            "        node = queue.popleft()\n"
            "        order.append(node)\n"
            "        # TODO: 按顺序加入尚未访问的相邻顶点\n"
            "        raise NotImplementedError\n"
            "    return order\n"
        )
    if "哈希" in normalized or "散列" in normalized or "hash" in normalized.lower():
        return (
            "def count_pairs(values, target_sum):\n"
            "    # 用 dict 记录每个值出现的次数，扫描一次即可统计配对数\n"
            "    counter = {}\n"
            "    answer = 0\n"
            "    for value in values:\n"
            "        complement = target_sum - value\n"
            "        # TODO: 查 dict 中 complement 的计数并累加到 answer\n"
            "        raise NotImplementedError\n"
            "    return answer\n\n"
            "numbers = list(map(int, input().split()))\n"
            "target = int(input())\n"
            "print(count_pairs(numbers, target))\n"
        )
    if "回溯" in normalized or "backtrack" in normalized.lower():
        return (
            "def backtrack(path, choices, results):\n"
            "    # path：当前已选；choices：剩余可选；results：收集完整解\n"
            "    if not choices:\n"
            "        results.append(list(path))\n"
            "        return\n"
            "    for index, choice in enumerate(choices):\n"
            "        path.append(choice)\n"
            "        # TODO: 计算剩余 choices（剪枝条件可加在此处）并递归\n"
            "        raise NotImplementedError\n"
            "        path.pop()  # 撤销选择\n\n"
            "def solve():\n"
            "    items = list(input().split())\n"
            "    results = []\n"
            "    backtrack([], items, results)\n"
            "    print(len(results))\n"
        )
    if "字符串" in normalized or "string" in normalized.lower() or "字符" in normalized:
        return (
            "def longest_common_prefix(strs):\n"
            "    # 字符串处理：以第一个 str 为基准，逐字符比较其它 string\n"
            "    if not strs:\n"
            "        return ''\n"
            "    prefix = strs[0]\n"
            "    for word in strs[1:]:\n"
            "        # TODO: 截短 prefix 直到 word 以前缀开头\n"
            "        raise NotImplementedError\n"
            "    return prefix\n\n"
            "words = input().split()\n"
            "print(longest_common_prefix(words))\n"
        )
    if "排序" in normalized:
        return (
            "def bubble_sort(values):\n"
            "    for end in range(len(values) - 1, 0, -1):\n"
            "        swapped = False\n"
            "        for index in range(end):\n"
            "            # TODO: 比较相邻元素，逆序时交换并更新 swapped\n"
            "            raise NotImplementedError\n"
            "        if not swapped:\n"
            "            break\n"
            "    return values\n\n"
            "numbers = list(map(int, input().split()))\n"
            "print(*bubble_sort(numbers))\n"
        )
    return (
        "def solve(values):\n"
        "    result = []\n"
        "    state = None\n"
        "    for value in values:\n"
        "        # TODO: 根据题意更新 state，并把阶段结果加入 result\n"
        "        raise NotImplementedError\n"
        "    return result\n\n"
        "numbers = list(map(int, input().split()))\n"
        "print(*solve(numbers))\n"
    )


def _fallback_trace_payload(*, topic: str) -> dict[str, Any]:
    normalized = re.sub(r"\s+", "", topic or "")
    if "单调栈" in normalized:
        code = (
            "values = list(map(int, input().split()))\n"
            "answer = [-1] * len(values)\n"
            "stack = []\n"
            "for index, value in enumerate(values):\n"
            "    while stack and values[stack[-1]] < value:\n"
            "        previous = stack.pop()\n"
            "        answer[previous] = value\n"
            "    stack.append(index)\n"
            "print(*answer)\n"
        )
        return {
            "title": f"{topic} · 下一个更大元素",
            "code": code,
            "stdin": "2 1 5 3 4\n",
            "stdout": "5 5 -1 4 -1\n",
            "narration_hint": "观察栈内下标如何保持单调，以及元素何时找到答案",
            "generated_fallback": "topic_safe_trace",
        }
    if "链表" in normalized:
        code = (
            "values = list(map(int, input().split()))\n"
            "next_index = list(range(1, len(values))) + [-1]\n"
            "previous = -1\n"
            "current = 0 if values else -1\n"
            "while current != -1:\n"
            "    following = next_index[current]\n"
            "    next_index[current] = previous\n"
            "    previous = current\n"
            "    current = following\n"
            "result = []\n"
            "while previous != -1:\n"
            "    result.append(values[previous])\n"
            "    previous = next_index[previous]\n"
            "print(*result)\n"
        )
        return {
            "title": f"{topic} · 引用方向逐步反转",
            "code": code,
            "stdin": "1 2 3 4\n",
            "stdout": "4 3 2 1\n",
            "narration_hint": "观察 previous、current 与 following 如何保持未处理部分可达",
            "generated_fallback": "topic_safe_trace",
        }
    if "双指针" in normalized:
        code = (
            "values = list(map(int, input().split()))\n"
            "target = values.pop(0)\n"
            "left = 0\n"
            "right = len(values) - 1\n"
            "found = False\n"
            "while left < right:\n"
            "    current_sum = values[left] + values[right]\n"
            "    if current_sum == target:\n"
            "        found = True\n"
            "        break\n"
            "    if current_sum < target:\n"
            "        left += 1\n"
            "    else:\n"
            "        right -= 1\n"
            "print(left, right if found else -1)\n"
        )
        return {
            "title": f"{topic} · 左右指针相向移动",
            "code": code,
            "stdin": "9 1 2 4 5 7\n",
            "stdout": "1 4\n",
            "narration_hint": "观察 left、right 如何根据当前和排除不可能区间",
            "generated_fallback": "topic_safe_trace",
        }
    if "数组" in normalized:
        code = (
            "values = list(map(int, input().split()))\n"
            "prefix = []\n"
            "running_sum = 0\n"
            "for index, value in enumerate(values):\n"
            "    running_sum += value\n"
            "    prefix.append(running_sum)\n"
            "print(*prefix)\n"
        )
        return {
            "title": f"{topic} · 下标遍历与前缀状态",
            "code": code,
            "stdin": "3 1 4 2\n",
            "stdout": "3 4 8 10\n",
            "narration_hint": "观察下标、当前元素与前缀和数组如何同步更新",
            "generated_fallback": "topic_safe_trace",
        }
    if "哈希" in normalized or "散列" in normalized:
        code = (
            "values = list(map(int, input().split()))\n"
            "frequency = {}\n"
            "for value in values:\n"
            "    frequency[value] = frequency.get(value, 0) + 1\n"
            "pairs = []\n"
            "for key in sorted(frequency):\n"
            "    pairs.append(f'{key}:{frequency[key]}')\n"
            "print(' '.join(pairs))\n"
        )
        return {
            "title": f"{topic} · 键值映射计数",
            "code": code,
            "stdin": "3 1 3 2 1 3\n",
            "stdout": "1:2 2:1 3:3\n",
            "narration_hint": "观察哈希表中键的创建与计数更新",
            "generated_fallback": "topic_safe_trace",
        }
    if "字符串" in normalized:
        code = (
            "text = input().strip()\n"
            "left = 0\n"
            "right = len(text) - 1\n"
            "matched = True\n"
            "while left < right:\n"
            "    if text[left] != text[right]:\n"
            "        matched = False\n"
            "        break\n"
            "    left += 1\n"
            "    right -= 1\n"
            "print('YES' if matched else 'NO')\n"
        )
        return {
            "title": f"{topic} · 字符匹配与边界收缩",
            "code": code,
            "stdin": "level\n",
            "stdout": "YES\n",
            "narration_hint": "观察字符比较与左右边界逐步收缩",
            "generated_fallback": "topic_safe_trace",
        }
    if "栈" in normalized or "队列" in normalized:
        code = (
            "tokens = input().split()\n"
            "stack = []\n"
            "pairs = {')': '(', ']': '[', '}': '{'}\n"
            "valid = True\n"
            "for token in tokens:\n"
            "    if token in '([{':\n"
            "        stack.append(token)\n"
            "    elif not stack or stack.pop() != pairs[token]:\n"
            "        valid = False\n"
            "        break\n"
            "print('YES' if valid and not stack else 'NO')\n"
        )
        return {
            "title": f"{topic} · 栈的后进先出过程",
            "code": code,
            "stdin": "( [ ] { } )\n",
            "stdout": "YES\n",
            "narration_hint": "观察左括号入栈与右括号匹配出栈",
            "generated_fallback": "topic_safe_trace",
        }
    if "排序" in normalized:
        code = (
            "values = list(map(int, input().split()))\n"
            "for end in range(len(values) - 1, 0, -1):\n"
            "    swapped = False\n"
            "    for index in range(end):\n"
            "        if values[index] > values[index + 1]:\n"
            "            values[index], values[index + 1] = values[index + 1], values[index]\n"
            "            swapped = True\n"
            "    if not swapped:\n"
            "        break\n"
            "print(*values)\n"
        )
        return {
            "title": f"{topic} · 相邻元素交换过程",
            "code": code,
            "stdin": "5 1 4 2 3\n",
            "stdout": "1 2 3 4 5\n",
            "narration_hint": "观察相邻比较、交换与有序边界的收缩",
            "generated_fallback": "topic_safe_trace",
        }
    if "二叉树" in normalized or normalized.endswith("树入门"):
        code = (
            "values = input().split()\n"
            "queue = [0]\n"
            "order = []\n"
            "while queue:\n"
            "    index = queue.pop(0)\n"
            "    if index >= len(values) or values[index] == '#':\n"
            "        continue\n"
            "    order.append(values[index])\n"
            "    queue.append(index * 2 + 1)\n"
            "    queue.append(index * 2 + 2)\n"
            "print(*order)\n"
        )
        return {
            "title": f"{topic} · 二叉树层序遍历",
            "code": code,
            "stdin": "A B C D E # F\n",
            "stdout": "A B C D E F\n",
            "narration_hint": "观察候选节点队列与访问顺序如何逐层推进",
            "generated_fallback": "topic_safe_trace",
        }
    if "回溯" in normalized:
        code = (
            "n = int(input())\n"
            "path = []\n"
            "answers = []\n"
            "def backtrack(position):\n"
            "    if position == n:\n"
            "        answers.append(''.join(path))\n"
            "        return\n"
            "    for choice in ('0', '1'):\n"
            "        path.append(choice)\n"
            "        backtrack(position + 1)\n"
            "        path.pop()\n"
            "backtrack(0)\n"
            "print(*answers)\n"
        )
        return {
            "title": f"{topic} · 选择与撤销过程",
            "code": code,
            "stdin": "2\n",
            "stdout": "00 01 10 11\n",
            "narration_hint": "观察 path 的选择、递归深入与撤销恢复",
            "generated_fallback": "topic_safe_trace",
        }
    if "贪心" in normalized:
        code = (
            "amount = int(input())\n"
            "coins = [10, 5, 2, 1]\n"
            "chosen = []\n"
            "for coin in coins:\n"
            "    while amount >= coin:\n"
            "        amount -= coin\n"
            "        chosen.append(coin)\n"
            "print(*chosen)\n"
        )
        return {
            "title": f"{topic} · 局部最优选择过程",
            "code": code,
            "stdin": "18\n",
            "stdout": "10 5 2 1\n",
            "narration_hint": "观察每一步如何选择当前可用的最大面额并缩小剩余量",
            "generated_fallback": "topic_safe_trace",
        }
    if "图" in normalized or "BFS" in normalized or "DFS" in normalized:
        code = (
            "from collections import deque\n"
            "n, m = map(int, input().split())\n"
            "graph = [[] for _ in range(n)]\n"
            "for _ in range(m):\n"
            "    source, target = map(int, input().split())\n"
            "    graph[source].append(target)\n"
            "    graph[target].append(source)\n"
            "queue = deque([0])\n"
            "visited = {0}\n"
            "order = []\n"
            "while queue:\n"
            "    node = queue.popleft()\n"
            "    order.append(node)\n"
            "    for neighbor in sorted(graph[node]):\n"
            "        if neighbor not in visited:\n"
            "            visited.add(neighbor)\n"
            "            queue.append(neighbor)\n"
            "print(*order)\n"
        )
        return {
            "title": f"{topic} · 图的广度优先遍历",
            "code": code,
            "stdin": "5 5\n0 1\n0 2\n1 3\n2 3\n3 4\n",
            "stdout": "0 1 2 3 4\n",
            "narration_hint": "观察访问标记、候选顶点队列与 BFS 顺序",
            "generated_fallback": "topic_safe_trace",
        }
    if "动态规划" in normalized or re.search(r"\bDP\b", topic, re.I):
        code = (
            "n = int(input())\n"
            "dp = [0] * (n + 1)\n"
            "if n >= 1:\n"
            "    dp[1] = 1\n"
            "for index in range(2, n + 1):\n"
            "    dp[index] = dp[index - 1] + dp[index - 2]\n"
            "print(dp[n])\n"
        )
        return {
            "title": f"{topic} · 状态表递推过程",
            "code": code,
            "stdin": "7\n",
            "stdout": "13\n",
            "narration_hint": "观察状态定义、初值与相邻状态如何推出当前结果",
            "generated_fallback": "topic_safe_trace",
        }
    return {
        "title": f"{topic or '算法演示'} · 生成失败",
        "code": "",
        "stdin": "",
        "stdout": "",
        "narration_hint": "未生成与主题匹配的可执行题解，等待自动重试",
        "generation_error": "missing_topic_safe_trace",
    }



def _fallback_reading_levels(hints: PersonaHints) -> list[dict[str, Any]]:
    topic = hints.learning_goals[:32] or "数据结构与算法"
    return [
        {
            "level": "基础",
            "fit_for": hints.knowledge_base or "概念尚不稳定的学习者",
            "items": [
                {
                    "title": "《数据结构（C语言版）》相关章节",
                    "type": "textbook",
                    "why": f"用于补齐{topic}的定义、存储结构与基本操作。",
                    "task": "整理 5 个关键术语，并用自己的话复述。",
                },
                {
                    "title": "《算法导论》基础数据结构章节",
                    "type": "textbook",
                    "why": "建立抽象数据类型、循环不变量与复杂度分析的标准表达。",
                    "task": "为一个例题写出输入、输出和复杂度。",
                },
            ],
        },
        {
            "level": "进阶",
            "fit_for": "已能完成基础题、希望提升建模能力的学习者",
            "items": [
                {
                    "title": "《算法》第 4 版相关算法范式章节",
                    "type": "textbook",
                    "why": "通过工程化示例理解同一结构在不同问题中的复用方式。",
                    "task": "对比两道题的状态定义或数据结构选择。",
                },
                {
                    "title": "CPython / STL 容器实现说明",
                    "type": "engineering",
                    "why": "理解列表、哈希表、树形结构在真实运行时中的成本。",
                    "task": "写出一次操作的均摊/最坏复杂度前提。",
                },
            ],
        },
        {
            "level": "挑战",
            "fit_for": "准备竞赛、考研或大厂面试的学习者",
            "items": [
                {
                    "title": "经典动态规划与贪心正确性证明材料",
                    "type": "paper",
                    "why": "训练从经验解法上升到可证明策略的能力。",
                    "task": "用交换论证或归纳法证明一个策略正确。",
                },
                {
                    "title": "开源判题系统沙盒与资源隔离设计资料",
                    "type": "engineering",
                    "why": "理解算法平台如何限制时间、内存与系统调用。",
                    "task": "画出一次提交从编译到运行隔离的流程图。",
                },
            ],
        },
    ]


# ── PPT 大纲 fallback 与归一化 ──

_PPT_ALLOWED_LAYOUTS = ("cover", "agenda", "content", "code", "closing")
_PPT_PLACEHOLDER_TEXT = (
    "封面标题",
    "页面标题",
    "代码页",
    "要点1",
    "要点2",
    "要点3",
    "章节1",
    "章节2",
    "关键伪代码或代码片段",
    "副标题（可空）",
    "讲者备注",
    "逐行解释",
)


def _ppt_outline_is_usable(slides: Any) -> bool:
    """Reject short, structurally weak, or prompt-echo PPT outlines."""
    if not isinstance(slides, list) or not (8 <= len(slides) <= 12):
        return False
    if not all(isinstance(slide, dict) for slide in slides):
        return False
    layouts = [str(slide.get("layout") or "").strip().lower() for slide in slides]
    if layouts[0] != "cover" or layouts[-1] != "closing":
        return False
    if layouts.count("cover") != 1 or layouts.count("closing") != 1 or "agenda" not in layouts:
        return False
    titles: list[str] = []
    for slide, layout in zip(slides, layouts):
        title = str(slide.get("title") or "").strip()
        notes = str(slide.get("notes") or "").strip()
        flattened = json.dumps(slide, ensure_ascii=False)
        if not title or len(notes) < 10:
            return False
        if any(token in flattened for token in _PPT_PLACEHOLDER_TEXT):
            return False
        titles.append(title)
        if layout in {"agenda", "content", "closing"}:
            bullets = slide.get("bullets")
            if not isinstance(bullets, list) or not (3 <= len(bullets) <= 5):
                return False
        if layout == "code":
            code_lines = [line for line in str(slide.get("code") or "").splitlines() if line.strip()]
            if not (3 <= len(code_lines) <= 12):
                return False
    return len(set(titles)) == len(titles)


def _fallback_ppt_cover(title: str, hints: PersonaHints) -> dict[str, Any]:
    topic_label = re.split(r"[：·]", title, maxsplit=1)[0].strip()[:28] or "本课主题"
    return {
        "layout": "cover",
        "title": title,
        "subtitle": f"掌握{topic_label}的核心模型、实现步骤与边界条件",
        "notes": "开场介绍本课主题，与学生的学习目标对齐，明确本节课的产出。",
    }


def _fallback_ppt_closing(topic: str, hints: PersonaHints) -> dict[str, Any]:
    return {
        "layout": "closing",
        "title": f"{topic} · 总结与作业",
        "bullets": [
            f"回顾{topic}的核心概念与典型操作",
            f"针对{hints.error_preference or '边界与初始条件'}设计反例",
            f"完成一道{topic}基础练习并复盘",
        ],
        "notes": "总结要点并布置课后任务，提示学生回顾本课易错点。",
    }


def _ppt_points(value: Any, *, limit: int = 4) -> list[str]:
    """Turn grounded prose into short, presentation-ready claims."""
    if isinstance(value, list):
        raw_points = [str(item).strip() for item in value]
    else:
        raw_points = re.split(r"[。；;，,\n]+", str(value or ""))
    points: list[str] = []
    for point in raw_points:
        cleaned = re.sub(r"^[-*•\s]+", "", point).strip()
        if len(cleaned) < 4 or cleaned in points:
            continue
        points.append(cleaned[:50].rstrip("，、（("))
        if len(points) >= limit:
            break
    return points


def _ppt_pad_points(
    points: list[str],
    fallbacks: list[str],
    *,
    minimum: int = 3,
    limit: int = 4,
) -> list[str]:
    """Return enough distinct bullets to keep a content slide scannable."""
    merged = list(dict.fromkeys([*points, *fallbacks]))
    return merged[:limit] if len(merged) >= minimum else merged


def _ppt_chunk_points(
    chunks: list[KnowledgeChunk] | None,
    *,
    markers: tuple[str, ...],
    limit: int = 4,
) -> list[str]:
    if not chunks:
        return []
    matched: list[str] = []
    for chunk in chunks:
        title = str(chunk.get("title") or "")
        if markers and not any(marker in title for marker in markers):
            continue
        matched.extend(_ppt_points(chunk.get("content"), limit=limit))
        if len(matched) >= limit:
            break
    return list(dict.fromkeys(matched))[:limit]


def _ppt_code_sample(topic: str) -> str:
    key = _match_topic_key(topic) or ""
    samples = {
        "链表": (
            "def reverse_list(head):\n"
            "    prev, cur = None, head\n"
            "    while cur:\n"
            "        nxt = cur.next\n"
            "        cur.next = prev\n"
            "        prev, cur = cur, nxt\n"
            "    return prev"
        ),
        "动态规划": (
            "def climb_stairs(n):\n"
            "    if n <= 1:\n"
            "        return 1\n"
            "    prev2, prev1 = 1, 1\n"
            "    for _ in range(2, n + 1):\n"
            "        prev2, prev1 = prev1, prev1 + prev2\n"
            "    return prev1"
        ),
        "排序": (
            "def bubble_sort(a):\n"
            "    for end in range(len(a) - 1, 0, -1):\n"
            "        swapped = False\n"
            "        for i in range(end):\n"
            "            if a[i] > a[i + 1]:\n"
            "                a[i], a[i + 1] = a[i + 1], a[i]\n"
            "                swapped = True\n"
            "        if not swapped: break\n"
            "    return a"
        ),
        "数组": (
            "def prefix_sums(values):\n"
            "    prefix = [0]\n"
            "    for value in values:\n"
            "        prefix.append(prefix[-1] + value)\n"
            "    return prefix"
        ),
        "字符串": (
            "from collections import Counter\n\n"
            "def is_anagram(left, right):\n"
            "    return Counter(left) == Counter(right)"
        ),
        "双指针": (
            "def pair_sum(a, target):\n"
            "    left, right = 0, len(a) - 1\n"
            "    while left < right:\n"
            "        total = a[left] + a[right]\n"
            "        if total == target: return left, right\n"
            "        if total < target: left += 1\n"
            "        else: right -= 1\n"
            "    return None"
        ),
        "栈与队列": (
            "def valid_brackets(text):\n"
            "    pairs = {')': '(', ']': '[', '}': '{'}\n"
            "    stack = []\n"
            "    for char in text:\n"
            "        if char in '([{': stack.append(char)\n"
            "        elif not stack or stack.pop() != pairs[char]:\n"
            "            return False\n"
            "    return not stack"
        ),
        "哈希表": (
            "def two_sum(values, target):\n"
            "    seen = {}\n"
            "    for i, value in enumerate(values):\n"
            "        need = target - value\n"
            "        if need in seen: return seen[need], i\n"
            "        seen[value] = i\n"
            "    return None"
        ),
        "二叉树": (
            "def max_depth(root):\n"
            "    if root is None:\n"
            "        return 0\n"
            "    left = max_depth(root.left)\n"
            "    right = max_depth(root.right)\n"
            "    return 1 + max(left, right)"
        ),
        "图": (
            "from collections import deque\n\n"
            "def bfs(graph, start):\n"
            "    queue, seen = deque([start]), {start}\n"
            "    while queue:\n"
            "        node = queue.popleft()\n"
            "        for nxt in graph[node]:\n"
            "            if nxt not in seen:\n"
            "                seen.add(nxt); queue.append(nxt)\n"
            "    return seen"
        ),
        "回溯": (
            "def subsets(values):\n"
            "    result, path = [], []\n"
            "    def dfs(index):\n"
            "        if index == len(values):\n"
            "            result.append(path.copy()); return\n"
            "        dfs(index + 1)\n"
            "        path.append(values[index])\n"
            "        dfs(index + 1); path.pop()\n"
            "    dfs(0); return result"
        ),
        "贪心": (
            "def max_non_overlapping(intervals):\n"
            "    intervals.sort(key=lambda item: item[1])\n"
            "    count, last_end = 0, float('-inf')\n"
            "    for start, end in intervals:\n"
            "        if start >= last_end:\n"
            "            count, last_end = count + 1, end\n"
            "    return count"
        ),
    }
    return samples.get(key, "")


def _ppt_complexity_claim(value: Any, label: str) -> str:
    text = str(value or "").strip()
    match = re.match(r"^(O\s*\([^)]*\))\s*[：:]?\s*(.*)$", text, re.I)
    notation = match.group(1).replace(" ", "") if match else ""
    detail = match.group(2) if match else text
    first_clause = re.split(r"[。；;，,]", detail, maxsplit=1)[0].strip()
    if notation:
        return f"{label} {notation}：{first_clause[:32]}"
    return f"{label}：{first_clause[:38] or '依据状态数与单次操作代价计算'}"


def _fallback_ppt_slides(
    topic: str,
    hints: PersonaHints,
    chunks: list[KnowledgeChunk] | None = None,
) -> list[dict[str, Any]]:
    """Build a grounded 10–11 slide teaching narrative when LLM output is unusable."""
    topic_name = (topic or "本课主题")[:36]
    key = _match_topic_key(topic_name)
    concept = (_TOPIC_ENRICHMENTS.get(key or "") or {}).get("concept") or {}
    objectives = _ppt_points(concept.get("learning_objectives"), limit=3) or [
        f"解释{topic_name}解决的问题",
        "独立写出核心步骤与边界",
        "用小样例验证实现正确性",
    ]
    objectives = _ppt_pad_points(
        objectives,
        [
            f"解释{topic_name}解决的问题",
            "独立写出核心步骤与边界",
            "用最小样例和边界输入验证实现正确性",
        ],
        limit=3,
    )
    model_points = _ppt_points(concept.get("abstract_model"), limit=4) or [
        "明确输入、输出与规模约束",
        "找出贯穿过程的核心状态",
        "写清操作前后必须保持的不变量",
    ]
    algorithm_points = _ppt_points(concept.get("algorithm_outline"), limit=4) or [
        "先定义状态与每个变量的语义",
        "再写核心操作或状态转移",
        "补齐初值、终止条件与遍历顺序",
        "最后用最小样例逐步验证",
    ]
    structures = _ppt_points(concept.get("data_structures"), limit=3)
    proof = _ppt_points(concept.get("correctness_proof"), limit=2)
    structure_points = _ppt_pad_points(
        structures + proof,
        [
            "明确每个状态或结构的职责",
            "每一步都保持关键不变量",
            "终止时结果覆盖全部输入",
        ],
    )
    case_points = _ppt_chunk_points(chunks, markers=("课堂案例", "案例", "例题"), limit=4)
    if len(case_points) < 3:
        case_points.extend([
            "先选一个最小但完整的输入",
            "逐步记录状态变化与中间结果",
            "再用一个边界样例反向检查",
        ])
    pitfalls = _ppt_points(concept.get("pitfalls"), limit=4) or [
        hints.error_preference or "忽略边界与初始条件",
        "变量含义与实际更新逻辑不一致",
        "只验证常规输入，没有验证最小规模",
    ]
    complexity = [
        _ppt_complexity_claim(concept.get("time_complexity"), "时间"),
        _ppt_complexity_claim(concept.get("space_complexity"), "空间"),
        "先保证正确，再依据重复计算或冗余状态优化",
    ]
    if key in {"dp", "动态规划"}:
        complexity = [
            "时间 O(n)：每个状态只计算一次",
            "基础表格占用 O(n)，当前滚动变量代码降为 O(1)",
            "先写对状态转移，再压缩只依赖相邻状态的存储",
        ]
    code = _ppt_code_sample(topic_name)
    title = f"{topic_name}：从概念到实现"
    slides: list[dict[str, Any]] = [
        _fallback_ppt_cover(title, hints),
        {
            "layout": "agenda",
            "title": "一条可复用的学习路径",
            "bullets": ["识别问题", "建立模型", "写出步骤", "验证与优化"],
            "notes": "用四个阶段建立全课导航。提醒学生后续每一页都会回答其中一个问题，并最终形成可执行的方法。",
        },
        {
            "layout": "content",
            "title": "学完这节，你能完成三件事",
            "bullets": objectives,
            "notes": "先明确可观察的学习产出。讲解时要求学生用自己的话复述目标，避免只记住术语而不会应用。",
        },
        {
            "layout": "content",
            "title": "先把问题压缩成一个清晰模型",
            "bullets": model_points,
            "notes": "从输入、输出、状态和不变量四个角度拆解问题。这里不急着写代码，先确保模型能够解释每一步。",
        },
        {
            "layout": "content",
            "title": "把方法写成可执行的四个步骤",
            "bullets": algorithm_points,
            "notes": "按顺序讲清初始化、核心更新、终止与返回值。每讲一步都追问变量此刻代表什么，防止机械背诵。",
        },
        {
            "layout": "content",
            "title": "关键结构决定了过程是否正确",
            "bullets": structure_points[:4],
            "notes": "把数据结构与正确性联系起来。重点强调不变量在每一次更新后仍成立，终止时自然得到目标结果。",
        },
        {
            "layout": "content",
            "title": "课堂案例：先用小样例看见状态变化",
            "bullets": list(dict.fromkeys(case_points))[:4],
            "notes": "带学生手算一个最小完整案例，逐步记录状态变化。随后更换边界输入，验证同一套规则是否仍然成立。",
        },
    ]
    if code:
        slides.append({
            "layout": "code",
            "title": "把核心方法落到一段可运行代码",
            "code": code,
            "notes": "逐行对应前一页的算法步骤，先指出状态变量和更新语句，再用最小样例走一遍，确认返回值与模型一致。",
        })
    slides.extend([
        {
            "layout": "content",
            "title": "复杂度不是结论，而是设计约束",
            "bullets": complexity,
            "notes": "先说明状态数或操作次数，再解释单次代价，最后讨论空间换时间的条件。不要只让学生背复杂度符号。",
        },
        {
            "layout": "content",
            "title": "真正拉开差距的是边界与易错点",
            "bullets": pitfalls,
            "notes": "把易错点改写成检查清单。要求学生为每一项构造一个能触发错误的输入，并说明预期结果。",
        },
        _fallback_ppt_closing(topic_name, hints),
    ])
    return slides


def _normalize_ppt_slide(raw: Any, *, hints: PersonaHints) -> dict[str, Any]:
    slide = raw if isinstance(raw, dict) else {}
    layout = str(slide.get("layout") or "content").strip().lower()
    if layout not in _PPT_ALLOWED_LAYOUTS:
        layout = "content"
    title = str(slide.get("title") or "").strip()
    if not title:
        title = "（未命名页）"
    notes = str(slide.get("notes") or "").strip()
    if not notes:
        notes = "本页讲解要点请由教师补充。"
    normalized: dict[str, Any] = {"layout": layout, "title": title, "notes": notes}
    subtitle = str(slide.get("subtitle") or "").strip()
    if subtitle:
        normalized["subtitle"] = subtitle
    bullets_raw = slide.get("bullets")
    if isinstance(bullets_raw, list):
        bullets = [str(b).strip() for b in bullets_raw if str(b).strip()]
        bullets = [b[:60] for b in bullets[:5]]
        if bullets:
            normalized["bullets"] = bullets
    code = str(slide.get("code") or "").strip()
    if code:
        # 截断到 12 行，避免一页过载
        lines = code.splitlines()[:12]
        normalized["code"] = "\n".join(lines)
    return normalized


# ── VideoScript fallback 与归一化 ──

_VIDEO_ALLOWED_SHOT_KEYS = ("index", "scene", "visual_hint", "subtitle", "voiceover", "duration_sec")


def _fallback_video_shots(topic: str, hints: PersonaHints) -> list[dict[str, Any]]:
    """LLM 输出不可用时的最小可用 6 镜教学短视频脚本。"""
    topic_name = topic[:32] or "本主题"
    error_hint = hints.error_preference or "边界条件与初始状态"
    return [
        {
            "index": 1,
            "scene": (
                f"开场镜头：教室白板特写，老师写下「{topic_name}」三个字，"
                "镜头缓慢拉远展示学习目标。"
            ),
            "visual_hint": f"白板居中显示「{topic_name}」，下方列出 2 条学习目标",
            "subtitle": f"今天我们用 60 秒搞懂{topic_name}",
            "voiceover": (
                f"同学们好，今天我们用一分钟时间，把{topic_name}的核心思路与"
                "最容易踩坑的地方讲清楚。看完之后，你应该能独立完成一道基础练习。"
            ),
            "duration_sec": 8,
        },
        {
            "index": 2,
            "scene": (
                f"问题动机镜头：现实场景图片淡入（如排队、查找、路径规划），"
                f"配以箭头标注引出「{topic_name}」要解决的问题。"
            ),
            "visual_hint": "左侧现实场景图，右侧抽象出输入/输出格式",
            "subtitle": "它解决的是这类典型问题",
            "voiceover": (
                f"在工程或竞赛中，我们经常遇到这样的问题：给定一组数据，"
                f"需要按某种规则高效地完成一次操作。{topic_name}就是为这类问题设计的核心方法。"
            ),
            "duration_sec": 10,
        },
        {
            "index": 3,
            "scene": (
                f"概念定义镜头：屏幕中央浮现「{topic_name}」的形式化定义，"
                "关键词逐字打字机效果出现。"
            ),
            "visual_hint": "中央文字定义 + 关键词高亮（不变量/输入/输出）",
            "subtitle": "记住这三个关键词",
            "voiceover": (
                f"{topic_name}的关键在于三个要点：明确的输入输出、贯穿始终的不变量、"
                "以及终止条件。这三个要点也是后续判断代码正确性的依据。"
            ),
            "duration_sec": 10,
        },
        {
            "index": 4,
            "scene": (
                "算法步骤镜头：分屏左侧显示伪代码，右侧手算 5 元素示例，"
                "高亮当前执行的代码行与对应数据位置。"
            ),
            "visual_hint": "左侧伪代码逐行高亮，右侧数组/状态逐步变化",
            "subtitle": "手算一遍比看十遍更有效",
            "voiceover": (
                "我们用 5 个元素的样例手算一遍：每一步保持不变量成立，"
                "状态随循环推进，直到终止条件满足。请暂停视频自己先算一次再对照。"
            ),
            "duration_sec": 12,
        },
        {
            "index": 5,
            "scene": (
                "易错点镜头：红色警告图标浮现，列出 2～3 个常见错误，"
                f"每条配反例截图。突出「{error_hint}」。"
            ),
            "visual_hint": "红色警告图标 + 反例代码片段（带删除线）",
            "subtitle": f"小心：{error_hint[:18]}",
            "voiceover": (
                f"同学们最容易在「{error_hint}」上栽跟头：要么忘了初始化，"
                "要么边界少算一格，导致结果偏差或死循环。请每次写完代码都先自查这一处。"
            ),
            "duration_sec": 10,
        },
        {
            "index": 6,
            "scene": (
                "总结镜头：白板上的「{topic_name}」三个字下方浮现 3 条要点，"
                "镜头定格后淡出。"
            ),
            "visual_hint": "白板 + 3 条要点 + 课后练习提示",
            "subtitle": "回顾要点，课后练一题",
            "voiceover": (
                f"总结一下：{topic_name}的核心是不变量与边界，手算样例是检验标准，"
                f"易错点要重点自查。课后请完成一道基础练习巩固。下节课见。"
            ),
            "duration_sec": 8,
        },
    ]


def _normalize_video_shot(raw: Any, index: int, *, hints: PersonaHints) -> dict[str, Any]:
    shot = raw if isinstance(raw, dict) else {}
    scene = str(shot.get("scene") or "").strip()
    if not scene:
        scene = f"第 {index} 镜：围绕当前课程主题展开分镜，配以示意图与字幕。"
    visual_hint = str(shot.get("visual_hint") or "").strip()
    if not visual_hint:
        visual_hint = "画面以示意图 + 关键文字为主，避免冗余装饰"
    subtitle = str(shot.get("subtitle") or "").strip()
    if not subtitle:
        subtitle = f"第 {index} 镜 · 关键要点"
    subtitle = subtitle[:30]
    voiceover = str(shot.get("voiceover") or "").strip()
    if not voiceover:
        voiceover = (
            f"本镜口播：请围绕第 {index} 镜的场景与字幕展开 40～120 字的讲解，"
            "强调与课程主题相关的核心思路或易错点。"
        )
    # voiceover 限长 200，避免溢出；不足 40 字也不强行填充（由校验层提示）
    voiceover = voiceover[:200]
    duration_raw = shot.get("duration_sec")
    try:
        duration = int(duration_raw) if duration_raw is not None else 8
    except (TypeError, ValueError):
        duration = 8
    duration = max(3, min(20, duration))
    return {
        "index": index,
        "scene": scene,
        "visual_hint": visual_hint,
        "subtitle": subtitle,
        "voiceover": voiceover,
        "duration_sec": duration,
    }


def _normalize_reading_level(raw: Any) -> dict[str, Any]:
    item = raw if isinstance(raw, dict) else {}
    level = str(item.get("level") or "基础")
    entries = item.get("items")
    if not isinstance(entries, list):
        entries = []
    normalized_items = []
    for entry in entries[:3]:
        e = entry if isinstance(entry, dict) else {}
        normalized_items.append(
            {
                "title": str(e.get("title") or "课程拓展材料"),
                "type": str(e.get("type") or "textbook"),
                "why": str(e.get("why") or "巩固课程知识点并连接工程实践。"),
                "task": str(e.get("task") or "读后写出 3 条要点。"),
            }
        )
    if not normalized_items:
        normalized_items.append(
            {
                "title": f"{level}层拓展阅读材料",
                "type": "textbook",
                "why": "围绕当前模块补齐知识深度。",
                "task": "完成一页读书摘要。",
            }
        )
    while len(normalized_items) < 2:
        normalized_items.append(
            {
                "title": f"{level}层补充阅读",
                "type": "textbook",
                "why": "从不同角度巩固理解。",
                "task": "对比两种材料的侧重点。",
            }
        )
    fit_for_raw = item.get("fit_for")
    if isinstance(fit_for_raw, list):
        fit_for = "、".join(str(value) for value in fit_for_raw if str(value).strip())
    else:
        fit_for = str(fit_for_raw or f"{level}学习者")
    return {
        "level": level,
        "fit_for": fit_for,
        "items": normalized_items,
    }


def _strip_kb_annotations(raw: str) -> str:
    cleaned = re.sub(r"---\*\*依据知识库\*\*[\s\S]*", "", raw)
    cleaned = re.sub(r"\n\*\*依据知识库\*\*[\s\S]*", "", cleaned)
    cleaned = re.sub(r"---{2,}\s*依据知识库[\s\S]*", "", cleaned)
    cleaned = re.sub(r"\n---+\s*\n\*\*依据知识库\*\*[\s\S]*", "", cleaned)
    cleaned = re.sub(r"\n---{3,}[\s\S]*", "", cleaned)
    cleaned = re.sub(r"\ncourse:[\w\-:]+\n", "\n", cleaned)
    cleaned = re.sub(r"\n内容校验[\s\S]*", "", cleaned)
    cleaned = re.sub(r"\n安全审查[\s\S]*", "", cleaned)
    return cleaned.strip()


def _parse_json_object(raw: str) -> dict[str, Any]:
    text = _strip_kb_annotations(raw.strip())
    for _ in range(4):
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.I)
        if fence:
            text = fence.group(1).strip()
        text = re.sub(r"^\s*json\s*(?:\\n|\r?\n)", "", text, count=1, flags=re.I).strip()
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            data = None
        if isinstance(data, dict):
            return data
        if isinstance(data, str):
            text = data.strip()
            continue
        # 部分模型会去掉最外层引号，却保留整段 JSON 的转义符。
        if "\\n" in text and ('\\"domain_narrative\\"' in text or '\\"code\\"' in text):
            decoded = text.replace("\\r\\n", "\n").replace("\\n", "\n").replace('\\"', '"')
            if decoded != text:
                text = decoded.strip()
                continue
        break
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        candidate = text[start : end + 1]
        try:
            data = json.loads(candidate)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            pass
        brace = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                brace += 1
            elif text[i] == "}":
                brace -= 1
                if brace == 0:
                    try:
                        data = json.loads(text[start : i + 1])
                        return data if isinstance(data, dict) else {}
                    except json.JSONDecodeError:
                        break
    return {}

def _ground_reading_titles(
    levels: list[dict[str, Any]],
    *,
    topic: str,
    chunks: list[KnowledgeChunk],
) -> list[dict[str, Any]]:
    """Replace unsupported named publications with explicit course-reading tasks."""
    knowledge_text = " ".join(
        f"{chunk.get('title', '')} {chunk.get('content', '')}" for chunk in chunks
    ).lower()
    suspicious = re.compile(r"《|》|MIT|Stanford|Coursera|LeetCode|力扣|算法导论|论文|官方文档", re.I)
    task_labels = ("概念精读", "实现分析", "边界复盘")
    grounded: list[dict[str, Any]] = []
    for level in levels:
        copied = dict(level)
        items: list[dict[str, Any]] = []
        for index, raw in enumerate(level.get("items") or []):
            item = dict(raw) if isinstance(raw, dict) else {}
            title = str(item.get("title") or "").strip()
            level_name = str(level.get("level") or "分层")
            title_is_placeholder = title in {
                "教材/文献/工程材料名称", "课程拓展材料", "拓展阅读材料", "材料名称",
            } or "工程材料名称" in title
            if title_is_placeholder:
                label = task_labels[index % len(task_labels)]
                item["title"] = f"{topic} · {level_name}{label}"
                item["type"] = "course_material"
            elif suspicious.search(title) and title.lower() not in knowledge_text:
                label = task_labels[index % len(task_labels)]
                item["title"] = f"{topic} · {level_name}{label}"
                item["type"] = "course_material"
                item["why"] = f"基于当前课程知识库，聚焦{topic}的定义、核心操作与成立前提。"
            elif topic not in title:
                item["title"] = f"{topic} · {title or task_labels[index % len(task_labels)]}"
            why = str(item.get("why") or "").strip()
            if len(why) < 12 or why in {"为什么读", "巩固概念", "加深理解"}:
                item["why"] = (
                    f"聚焦{topic}在{level_name}阶段必须掌握的定义、操作顺序、成立前提与常见错误。"
                )
            task = str(item.get("task") or "").strip()
            if len(task) < 8 or task in {"读一读", "阅读", "理解", "思考"}:
                actions = (
                    f"手算一个{topic}样例，记录每一步关键状态并核对最终结果。",
                    f"比较两种{topic}实现，写出复杂度、适用条件和一个反例。",
                    f"整理{topic}的循环不变量，并用三句话说明初始化、保持与终止。",
                )
                item["task"] = actions[index % len(actions)]
            items.append(item)
        copied["items"] = items
        grounded.append(copied)
    return grounded
