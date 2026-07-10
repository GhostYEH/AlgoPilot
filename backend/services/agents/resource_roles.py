"""个性化资源生成角色 Agent。"""

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


def _serialize_domain_structure(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


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
    return (
        f"mindmap\n"
        f"  root(({topic}))\n"
        f"    核心概念\n"
        f"    关键算法\n"
        f"    应用场景"
    )


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
                fixed_lines.append(f"    {label}")
            continue

        raw_indent = len(line) - len(line.lstrip())
        indent = max(4, raw_indent if raw_indent > 2 else 4)
        cleaned = _clean_mindmap_label(stripped)
        if not cleaned:
            continue
        fixed_lines.append(" " * indent + cleaned)

    if not has_root:
        fixed_lines.insert(1, f"  root(({fallback_topic}))")

    if len(fixed_lines) < 3:
        return _build_fallback_mindmap(fallback_topic)

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
    if focus_hint:
        return _clean_mindmap_label(focus_hint, max_len=24) or _clean_mindmap_label(topic, max_len=24)
    if module_key:
        return _clean_mindmap_label(module_key, max_len=24) or _clean_mindmap_label(topic, max_len=24)
    return _clean_mindmap_label(topic, max_len=24) or "学习主题"


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
        for branch, children in profile:
            lines.append(f"    {branch}")
            for child in children:
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
    for branch, children in branches:
        lines.append(f"    {branch}")
        for child in children:
            lines.append(f"      {child}")
    return "\n".join(lines)


def _mindmap_needs_rebuild(content: str, *, focus_label: str) -> bool:
    labels = [ln.strip() for ln in content.splitlines()[1:] if ln.strip()]
    if len(labels) < 10:
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
        content = _strip_kb_annotations(content.strip())
        content = self.normalize_output(content, hints=hints)
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
        if isinstance(data.get("domain_narrative"), dict) and isinstance(data.get("structure_logic"), dict):
            normalized = _normalize_domain_structure_payload(
                data,
                fallback_topic=hints.learning_goals[:32] or "算法主题",
                scenario=False,
            )
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
    ) -> tuple[str, str, dict]:
        title, content, meta = await super().generate(
            topic=topic,
            profile_block=profile_block,
            module_key=module_key,
            focus_hint=focus_hint,
            chunks=chunks,
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

    def normalize_output(self, raw: str, *, hints: PersonaHints) -> str:
        text = raw.strip()
        fence = re.search(r"```(?:mermaid)?\s*([\s\S]*?)```", text)
        if fence:
            text = fence.group(1).strip()
        topic = hints.learning_goals[:20] or "学习主题"
        if text.startswith("mindmap"):
            sanitized = _sanitize_mermaid(text)
            return _fix_mindmap_syntax(sanitized, fallback_topic=topic)
        if text.startswith(("flowchart", "graph")):
            converted = _convert_flowchart_to_mindmap(text, hints)
            return _fix_mindmap_syntax(converted, fallback_topic=topic)
        return _build_fallback_mindmap(topic)


class QuizAgent(ResourceRoleAgent):
    """考题官：5 道个性化练习题（3 选择 + 2 填空）。"""

    agent_id = "QuizAgent"
    display_name = "QuizAgent"
    role = "考题官 · 个性化题单"

    def system_prompt(self, hints: PersonaHints) -> str:
        return f"""你是 QuizAgent（考题官）。根据学生知识短板与易错点生成 **5 道**个性化练习题。

## 个性化要求
- 知识基础：{hints.knowledge_base or '待评估'}
- 易错点偏好：{hints.error_preference or '边界条件与复杂度'}
- 代码能力：{hints.coding_ability or '入门'}，题目难度与之匹配

## 输出规范（必须严格遵守）
- 输出**唯一** JSON，不要 markdown 代码块
- **禁止** 在输出中包含知识库引用标注（如 `依据知识库`、`course:`、`---` 分隔线等），仅输出纯 JSON
- 固定 5 题：**前 3 题必须是 choice，后 2 题必须是 fill**（禁止 code 编程题）
- **choice 题必须恰好 4 个选项**，不能多也不能少，每个选项须有实质区分度（禁止"以上都对"等废话选项）
- fill 题不要有 options 字段（或设为空数组）
- 每题含 stem、hint、focus、difficulty(easy|medium|hard)
- stem 必须紧扣知识库具体知识点，禁止泛泛而谈
- 难度梯度：第1题 easy，第2题 medium，第3题 medium，第4题 medium，第5题 hard

## JSON 示例（严格遵守此结构）
{{"questions":[{{"type":"choice","stem":"…","options":["选项A","选项B","选项C","选项D"],"hint":"…","focus":"…","difficulty":"easy"}},{{"type":"choice","stem":"…","options":["选项A","选项B","选项C","选项D"],"hint":"…","focus":"…","difficulty":"medium"}},{{"type":"choice","stem":"…","options":["选项A","选项B","选项C","选项D"],"hint":"…","focus":"…","difficulty":"medium"}},{{"type":"fill","stem":"…","hint":"…","focus":"…","difficulty":"medium"}},{{"type":"fill","stem":"…","hint":"…","focus":"…","difficulty":"hard"}}]}}"""

    def temperature(self) -> float:
        return 0.3

    def max_tokens(self) -> int:
        return 2200

    def output_format(self) -> str:
        return "quiz_json"

    def normalize_output(self, raw: str, *, hints: PersonaHints) -> str:
        data = _parse_json_object(raw)
        validated, issues = validate_quiz_payload(data if isinstance(data, dict) else {})
        if validated is not None:
            trimmed: list[QuizQuestion] = list(validated.questions[:5])
            while len(trimmed) < 5:
                trimmed.append(
                    QuizQuestion(
                        type="fill",
                        stem="请用一句话总结本主题要点",
                        hint="参考讲解文档",
                        focus=hints.error_preference or "综合",
                        difficulty="medium",
                    )
                )
            trimmed = _enforce_quiz_type_mix(trimmed, hints)
            return json.dumps(
                {"questions": [q.model_dump() for q in trimmed[:5]]},
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
                            "type": "choice",
                            "stem": "下列哪种表述与知识库一致？",
                            "options": ["与知识库一致", "编造题号", "忽略边界", "跳过定义"],
                            "hint": "选与知识库一致项",
                            "focus": "概念",
                            "difficulty": "medium",
                        },
                        {
                            "type": "choice",
                            "stem": f"关于本主题的核心操作，下列哪项说法正确？（侧重：{focus}）",
                            "options": ["需要辅助数据结构", "暴力即可", "无需考虑边界", "复杂度均为 O(1)"],
                            "hint": "结合知识库与课程讲义",
                            "focus": focus,
                            "difficulty": "medium",
                        },
                        {
                            "type": "fill",
                            "stem": "请填写本主题的核心时间复杂度符号（如 O(n)）",
                            "hint": "参考知识库",
                            "focus": "复杂度",
                            "difficulty": "medium",
                        },
                        {
                            "type": "fill",
                            "stem": "请用一句话描述本主题最关键的算法思想或不变量",
                            "hint": "结合课程讲义与知识库",
                            "focus": "核心思想",
                            "difficulty": "hard",
                        },
                    ]
                },
                ensure_ascii=False,
                indent=2,
            )
        trimmed = [q for q in questions if isinstance(q, dict)][:5]
        while len(trimmed) < 5:
            trimmed.append(
                {
                    "type": "fill",
                    "stem": "请用一句话总结本主题要点",
                    "hint": "参考讲解文档",
                    "focus": hints.error_preference or "综合",
                    "difficulty": "medium",
                }
            )
        trimmed = _enforce_quiz_type_mix_dict(trimmed, hints)
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
        if isinstance(data.get("domain_narrative"), dict) and isinstance(data.get("structure_logic"), dict):
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

        trace_internal_keys = {"verdict", "message", "step_count", "user_line_count", "result_preview", "trace_source", "topic"}
        for k in trace_internal_keys:
            payload.pop(k, None)

        if trace_meta.get("steps"):
            payload["steps"] = trace_meta["steps"]

        content = json.dumps(payload, ensure_ascii=False, indent=2)
        meta["trace_verdict"] = trace_meta.get("verdict", "SKIPPED")
        meta["trace_steps"] = trace_meta.get("step_count", 0)
        meta["trace_source"] = trace_meta.get("trace_source", "llm_only")
        return title, content, meta

    def normalize_output(self, raw: str, *, hints: PersonaHints) -> str:
        data = _parse_json_object(raw)
        if not isinstance(data, dict):
            data = {}
        if not data.get("code"):
            data = _fallback_trace_payload(topic=hints.learning_goals or "算法演示")
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

要求：必须包含「基础」「进阶」「挑战」三层；每层 2-3 条；优先使用经典教材、公开工程材料、算法课程通用材料；不要编造 URL。"""

    def temperature(self) -> float:
        return 0.35

    def max_tokens(self) -> int:
        return 1800

    def output_format(self) -> str:
        return "leveled_reading_json"

    def normalize_output(self, raw: str, *, hints: PersonaHints) -> str:
        data = _parse_json_object(raw)
        levels = data.get("levels") if isinstance(data, dict) else None
        if not isinstance(levels, list) or not levels:
            levels = _fallback_reading_levels(hints)
        normalized = {
            "reading_goal": str(data.get("reading_goal") or "从课堂概念过渡到工程与面试应用"),
            "levels": [_normalize_reading_level(lv) for lv in levels],
        }
        required = {"基础", "进阶", "挑战"}
        present = {str(lv.get("level")) for lv in normalized["levels"]}
        for missing in required - present:
            normalized["levels"].append(_normalize_reading_level({"level": missing, "items": []}))
        return json.dumps(normalized, ensure_ascii=False, indent=2)


ROLE_AGENT_BY_TYPE: dict[ResourceType, ResourceRoleAgent] = {
    "document": ConceptAgent(),
    "mindmap": GraphAgent(),
    "exercises": QuizAgent(),
    "code_case": ScenarioAgent(),
    "trace_animation": TraceAgent(),
    "reading": ReadingAgent(),
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
    return {
        "level": level,
        "fit_for": str(item.get("fit_for") or f"{level}学习者"),
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
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    else:
        text = _strip_kb_annotations(text)
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        pass
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


def _pad_choice_options(opts: list[str]) -> list[str]:
    if len(opts) >= 4:
        return opts[:4]
    padded = list(opts)
    while len(padded) < 4:
        padded.append(f"选项{chr(65 + len(padded))}")
    return padded


def _enforce_quiz_type_mix(
    questions: list[QuizQuestion], hints: PersonaHints
) -> list[QuizQuestion]:
    result: list[QuizQuestion] = []
    choice_count = 0
    fill_count = 0
    for q in questions:
        if q.type == "choice" and choice_count < 3:
            opts = _pad_choice_options(q.options)
            result.append(QuizQuestion(**{**q.model_dump(), "options": opts}))
            choice_count += 1
        elif q.type == "fill" and fill_count < 2:
            result.append(QuizQuestion(**{**q.model_dump(), "options": []}))
            fill_count += 1
        elif q.type == "choice" and choice_count >= 3 and fill_count < 2:
            result.append(
                QuizQuestion(
                    type="fill",
                    stem=q.stem,
                    hint=q.hint,
                    focus=q.focus,
                    difficulty=q.difficulty,
                    options=[],
                )
            )
            fill_count += 1
    while len(result) < 3 and choice_count < 3:
        focus = hints.error_preference or "综合"
        result.append(
            QuizQuestion(
                type="choice",
                stem=f"关于本主题（侧重：{focus}），下列哪项说法正确？",
                options=["与知识库一致", "忽略边界条件", "任意规模都 O(1)", "无需数据结构"],
                hint="对照课程讲义",
                focus=focus,
                difficulty="easy" if choice_count == 0 else "medium",
            )
        )
        choice_count += 1
    while fill_count < 2:
        result.append(
            QuizQuestion(
                type="fill",
                stem="请用一句话总结本主题的核心思想或复杂度结论",
                hint="参考讲解文档与知识库",
                focus=hints.error_preference or "综合",
                difficulty="medium" if fill_count == 0 else "hard",
            )
        )
        fill_count += 1
    return result[:5]


def _enforce_quiz_type_mix_dict(
    questions: list[dict[str, Any]], hints: PersonaHints
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    choice_count = 0
    fill_count = 0
    for q in questions:
        qtype = str(q.get("type", "choice"))
        if qtype == "choice" and choice_count < 3:
            opts = _pad_choice_options(q.get("options") or [])
            result.append({**q, "type": "choice", "options": opts})
            choice_count += 1
        elif qtype == "fill" and fill_count < 2:
            result.append({**q, "type": "fill", "options": []})
            fill_count += 1
        elif qtype == "choice" and choice_count >= 3 and fill_count < 2:
            result.append({
                "type": "fill",
                "stem": str(q.get("stem", "")),
                "hint": str(q.get("hint", "")),
                "focus": str(q.get("focus", "")),
                "difficulty": str(q.get("difficulty", "medium")),
                "options": [],
            })
            fill_count += 1
    while len(result) < 3 and choice_count < 3:
        focus = hints.error_preference or "综合"
        result.append({
            "type": "choice",
            "stem": f"关于本主题（侧重：{focus}），下列哪项说法正确？",
            "options": ["与知识库一致", "忽略边界条件", "任意规模都 O(1)", "无需数据结构"],
            "hint": "对照课程讲义",
            "focus": focus,
            "difficulty": "easy" if choice_count == 0 else "medium",
        })
        choice_count += 1
    while fill_count < 2:
        result.append({
            "type": "fill",
            "stem": "请用一句话总结本主题的核心思想或复杂度结论",
            "hint": "参考讲解文档与知识库",
            "focus": hints.error_preference or "综合",
            "difficulty": "medium" if fill_count == 0 else "hard",
            "options": [],
        })
        fill_count += 1
    return result[:5]
