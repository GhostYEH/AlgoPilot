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
    {"key": "sorting", "label": "排序算法", "phase": "technique", "available": True},
    {"key": "binary-tree", "label": "二叉树", "phase": "tree", "available": True},
    {"key": "backtracking", "label": "回溯算法", "phase": "tree", "available": True},
    {"key": "greedy", "label": "贪心算法", "phase": "advanced", "available": True},
    {"key": "dp", "label": "动态规划", "phase": "advanced", "available": True},
    {"key": "monotonic-stack", "label": "单调栈", "phase": "advanced", "available": True},
    {"key": "graph", "label": "图论", "phase": "advanced", "available": True},
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
    "sorting": ["array", "two-pointers"],
    "binary-tree": ["linked-list", "stack-queue"],
    "backtracking": ["binary-tree"],
    "greedy": ["binary-tree"],
    "dp": ["greedy", "backtracking"],
    "monotonic-stack": ["stack-queue"],
    "graph": ["stack-queue", "binary-tree"],
}

PHASE_RANK = {"foundation": 0, "technique": 1, "tree": 2, "advanced": 3}

# 学情降级：受挫知识点 → 临时插播的基础巩固模块（须为 catalog 中已有 key）
REMEDIATION_BY_TOPIC: dict[str, dict[str, str]] = {
    "动态规划": {"module_key": "array", "label": "数组基础巩固", "reason": "降级：先掌握一维数组与前缀和思想"},
    "dp": {"module_key": "array", "label": "数组基础巩固", "reason": "降级：动态规划受挫，回退数组与前缀和"},
    "二叉树": {"module_key": "linked-list", "label": "链表巩固", "reason": "降级：树结构受挫，巩固指针与链表"},
    "binary-tree": {"module_key": "linked-list", "label": "链表巩固", "reason": "降级：树模块受挫，回退链表"},
    "图论": {"module_key": "binary-tree", "label": "二叉树巩固", "reason": "降级：图论受挫，巩固树遍历"},
    "graph": {"module_key": "binary-tree", "label": "二叉树巩固", "reason": "降级：图论受挫，巩固树遍历"},
    "贪心": {"module_key": "stack-queue", "label": "栈队列巩固", "reason": "降级：贪心受挫，巩固基础结构"},
    "greedy": {"module_key": "stack-queue", "label": "栈队列巩固", "reason": "降级：贪心受挫，巩固基础结构"},
    "回溯": {"module_key": "binary-tree", "label": "二叉树巩固", "reason": "降级：回溯受挫，巩固递归与树"},
    "backtracking": {"module_key": "binary-tree", "label": "二叉树巩固", "reason": "降级：回溯受挫，巩固递归与树"},
    "排序": {"module_key": "array", "label": "数组与下标巩固", "reason": "降级：排序受挫，先巩固数组遍历与区间边界"},
    "sorting": {"module_key": "array", "label": "数组与下标巩固", "reason": "降级：排序受挫，先巩固数组遍历与区间边界"},
}

DEFAULT_REMEDIATION = {
    "module_key": "array",
    "label": "数组基础巩固",
    "reason": "降级：检测到连续作答失败，插入基础巩固关卡",
}


def _merge_course_into_module_dependencies() -> dict[str, list[str]]:
    """将 course_manifest 章节先修合并进模块 DAG（不删除原有边）。"""
    merged = {k: list(v) for k, v in MODULE_DEPENDENCIES.items()}
    try:
        from services.knowledge.course_loader import (
            load_manifest,
            module_dependency_edges_from_course,
        )

        manifest = load_manifest()
        for mk, pres in module_dependency_edges_from_course(manifest).items():
            if mk not in merged:
                merged[mk] = []
            for p in pres:
                if p in VALID_MODULE_KEYS and p not in merged[mk]:
                    merged[mk].append(p)
    except Exception:
        pass
    return merged


# 路径规划使用的模块先修（手工 DAG + 课程 manifest 合并）
MODULE_DEPENDENCIES_RESOLVED: dict[str, list[str]] = _merge_course_into_module_dependencies()


def lookup_remediation(knowledge_point: str, module_key: str = "") -> dict[str, str]:
    """根据知识点或模块 key 查找降级巩固节点。"""
    for key in (knowledge_point, module_key):
        if not key:
            continue
        if key in REMEDIATION_BY_TOPIC:
            return REMEDIATION_BY_TOPIC[key]
        for topic, spec in REMEDIATION_BY_TOPIC.items():
            if topic in key or key in topic:
                return spec
    return DEFAULT_REMEDIATION
