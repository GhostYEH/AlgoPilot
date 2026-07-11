"""追踪步骤去噪：仅保留对用户可视化有意义的步。"""

from __future__ import annotations

import re
from typing import TypeVar

T = TypeVar("T")

# 读入 / 构造阶段特征：仅匹配明确的"数据读入"和"空容器构造"操作。
# 注意：push_back / append / emplace_back 不能单独算初始化——BFS 入队、
# 单调栈入栈、结果收集都会用这些操作，需交给 _container_growing_only 判断。
# 注意：for(int i=0;...) 不能算初始化——算法核心循环也是这个形式。
_INIT_PATTERNS = (
    re.compile(r"\bcin\s*>>"),            # C++ cin >> x
    re.compile(r"\bscanf\s*\("),          # C scanf
    re.compile(r"\binput\s*\("),          # Python input()
    re.compile(r"=\s*(?:std::)?(?:vector|deque|list|map|set|unordered_map|unordered_set)\s*<", re.I),  # C++ 构造容器
    re.compile(r"=\s*list\s*\("),         # Python list()
    re.compile(r"=\s*dict\s*\("),         # Python dict()
    re.compile(r"=\s*deque\s*\("),        # Python deque()
)


def _is_initialization_line(text: str) -> bool:
    """该行是否属于读入/构造阶段。"""
    stripped = text.strip()
    if not stripped:
        return False
    return any(p.search(stripped) for p in _INIT_PATTERNS)


def _container_growing_only(changed_vars: list[str]) -> bool:
    """变化的变量是否仅是"按递增下标写入的输入缓冲容器"。

    仅保留明确的"读入缓冲"容器名（a/arr/nums/v/vec/buf/data/input/tmp/temp）。
    绝不把算法核心数据结构（dp/seen/visited/q/st/stack/queue/graph/grid/matrix）
    误判为读入阶段——这些是算法的主角，必须完整追踪。
    """
    if not changed_vars:
        return False
    ok_names = {
        "a", "arr", "nums", "v", "vec", "buf", "data", "input", "nums2",
        "tmp", "temp",
    }
    for v in changed_vars:
        low = v.lower().split("[", 1)[0].split(".", 1)[0]
        if low in ok_names:
            continue
        if low.endswith("_arr") or low.endswith("_list") or low.endswith("_vec"):
            continue
        # 其他变量（如 res / ans / i / j / cnt / dp / seen / q）出现 → 不是纯读入阶段
        return False
    return True


def compress_initialization_phase(
    steps: list[T],
    *,
    source: str = "",
    keep_first: int = 1,
    keep_last: int = 1,
    min_compress: int = 4,
) -> list[T]:
    """压缩"读入/构造阶段"的连续步骤，只保留首末态。

    识别规则：
    - 连续多步停留在属于读入/构造特征的源码行
    - 或：同行多步且变化变量仅为"按递增下标写入的容器"
    满足以上任一，则该段为"准备阶段"，仅保留首 keep_first 步 + 末 keep_last 步。

    算法核心阶段（非读入特征 + 非纯容器写入）一律保留。
    """
    if not steps or not source.strip():
        return steps

    lines = source.splitlines()
    n = len(steps)

    def _line_text(step: T) -> str:
        ln = _line(step)
        if 1 <= ln <= len(lines):
            return lines[ln - 1]
        return ""

    # 标记每一步是否属于"准备阶段"
    is_init = [False] * n
    for i, s in enumerate(steps):
        text = _line_text(s)
        changed = _changed(s)
        if _is_initialization_line(text):
            is_init[i] = True
        elif len(changed) > 0 and _container_growing_only(changed):
            is_init[i] = True

    # 分段：连续的 is_init=True 视为一段；连续的 is_init=False 视为算法核心段
    out: list[T] = []
    i = 0
    while i < n:
        if not is_init[i]:
            out.append(steps[i])
            i += 1
            continue
        # 找到一段准备阶段的终点
        j = i
        while j < n and is_init[j]:
            j += 1
        seg = steps[i:j]
        if len(seg) < min_compress:
            # 段太短不压缩，避免抖动
            out.extend(seg)
        else:
            # 仅保留首 keep_first + 末 keep_last
            head = seg[:keep_first]
            tail = seg[-keep_last:] if keep_last > 0 else []
            out.extend(head)
            out.extend(tail)
        i = j

    # 重新计算 changed：压缩后首步的 changed 可能丢失前文，但 filter_meaningful_steps 会再次校正
    return out


def _changed(s: T) -> list:
    if isinstance(s, dict):
        return list(s.get("changed") or [])
    return list(getattr(s, "changed", None) or [])


def _line(s: T) -> int:
    if isinstance(s, dict):
        return int(s.get("line") or 0)
    return int(getattr(s, "line", 0) or 0)


def _vars(s: T) -> dict:
    if isinstance(s, dict):
        return dict(s.get("vars") or {})
    return dict(getattr(s, "vars", None) or {})


def _set_changed(s: T, changed: list[str]) -> None:
    if isinstance(s, dict):
        s["changed"] = changed
    else:
        setattr(s, "changed", changed)


def collapse_consecutive_same_line_steps(steps: list[T]) -> list[T]:
    """Drop only the first pre-statement frame from each same-line GDB run."""
    if not steps:
        return []
    collapsed: list[T] = []
    index = 0
    while index < len(steps):
        end = index + 1
        while end < len(steps) and _line(steps[end]) == _line(steps[index]):
            end += 1
        run = steps[index:end]
        collapsed.extend(run[1:] if len(run) > 1 else run)
        index = end

    previous: dict = {}
    for step in collapsed:
        current = _vars(step)
        changed = [name for name, value in current.items() if previous.get(name) != value]
        _set_changed(step, changed)
        previous = current
    return collapsed


def filter_meaningful_steps(steps: list[T], *, max_steps: int = 200) -> list[T]:
    """保留首步、末步，以及变量发生变化的步。"""
    if not steps:
        return []
    out: list[T] = []
    last = len(steps) - 1
    for i, s in enumerate(steps):
        if i == 0 or i == last or _changed(s):
            out.append(s)
    return out[:max_steps]
