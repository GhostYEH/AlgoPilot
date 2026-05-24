"""算法模块目录（与前端 constants/modules 对齐）。"""

from typing import TypedDict


class ModuleCatalogItem(TypedDict):
    key: str
    label: str
    phase: str
    available: bool


MODULE_CATALOG: list[ModuleCatalogItem] = [
    {"key": "array", "label": "数组", "phase": "foundation", "available": True},
    {"key": "linked-list", "label": "链表", "phase": "foundation", "available": True},
    {"key": "hash-table", "label": "哈希表", "phase": "foundation", "available": True},
    {"key": "string", "label": "字符串", "phase": "foundation", "available": True},
    {"key": "two-pointers", "label": "双指针法", "phase": "technique", "available": True},
    {"key": "stack-queue", "label": "栈与队列", "phase": "technique", "available": True},
    {"key": "binary-tree", "label": "二叉树", "phase": "tree", "available": True},
    {"key": "backtracking", "label": "回溯算法", "phase": "tree", "available": True},
    {"key": "greedy", "label": "贪心算法", "phase": "advanced", "available": True},
    {"key": "dp", "label": "动态规划", "phase": "advanced", "available": True},
    {"key": "monotonic-stack", "label": "单调栈", "phase": "advanced", "available": True},
    {"key": "graph", "label": "图论", "phase": "advanced", "available": False},
]

VALID_MODULE_KEYS = {m["key"] for m in MODULE_CATALOG}

PHASE_LABELS = {
    "foundation": "基础结构",
    "technique": "解题技巧",
    "tree": "树与搜索",
    "advanced": "进阶算法",
}

DEFAULT_ORDER = [m["key"] for m in MODULE_CATALOG]

# 模块依赖 DAG（前置 module_key → 后继须在后）
MODULE_DEPENDENCIES: dict[str, list[str]] = {
    "array": [],
    "linked-list": ["array"],
    "hash-table": ["array"],
    "string": ["array"],
    "two-pointers": ["array", "linked-list", "hash-table"],
    "stack-queue": ["array"],
    "binary-tree": ["linked-list", "stack-queue"],
    "backtracking": ["binary-tree"],
    "greedy": ["binary-tree"],
    "dp": ["greedy", "backtracking"],
    "monotonic-stack": ["stack-queue"],
    "graph": ["binary-tree", "dp"],
}

PHASE_RANK = {"foundation": 0, "technique": 1, "tree": 2, "advanced": 3}
