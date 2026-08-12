"""链表等结构的追踪序列化（供 trace_runner 内嵌脚本与单测复用）。"""

from __future__ import annotations

from typing import Any

LL_MAX_DEPTH = 50
TREE_MAX_NODES = 64
TREE_MAX_DEPTH = 30
MATRIX_MAX_CELLS = 400
MATRIX_OVERFLOW_MSG = "数据规模过大，仅支持小规模用例可视化（矩阵不超过 400 格）"


def is_matrix(val: list) -> bool:
    """list of list 且各行等长 → 二维矩阵（DP 表），不按尺寸拒绝。"""
    if not val or not isinstance(val, list):
        return False
    if not all(isinstance(row, list) for row in val):
        return False
    col_len: int | None = None
    for row in val:
        if col_len is None:
            col_len = len(row)
        elif len(row) != col_len:
            return False
    return True


def matrix_payload(val: list) -> dict[str, Any]:
    rows = len(val)
    cols = len(val[0]) if rows else 0
    if rows * cols > MATRIX_MAX_CELLS:
        return {
            "type": "matrix_overflow",
            "value": {
                "rows": rows,
                "cols": cols,
                "cells": [],
                "message": MATRIX_OVERFLOW_MSG,
            },
        }
    cells: list[list[Any]] = []
    for row_in in val:
        row: list[Any] = []
        for cell in row_in:
            if isinstance(cell, (bool, int, float, str)) or cell is None:
                row.append(cell)
            else:
                row.append(str(cell)[:16])
        cells.append(row)
    return {"type": "matrix", "value": {"rows": rows, "cols": cols, "cells": cells}}

# 反转链表等场景：整链入口（树题 root 由 is_tree_node 优先识别）
_LINKED_LIST_NAMES = frozenset({"head", "dummy", "sentinel", "l1", "list1", "list"})
_TREE_ROOT_NAMES = frozenset({"root", "tree", "t1", "t2"})
_TREE_POINTER_NAMES = frozenset(
    {"curr", "current", "left", "right", "node", "parent", "child", "p", "tail"}
)
# 多指针
_STACK_NAMES = frozenset(
    {
        "st",
        "stack",
        "stk",
        "s",
        "brackets",
        "paren_stack",
        "char_stack",
    }
)


def is_stack_var_name(name: str) -> bool:
    low = name.lower().strip()
    return low in _STACK_NAMES or low.endswith("_stack") or low.endswith("stack")


_NODE_REF_NAMES = frozenset(
    {
        "prev",
        "curr",
        "current",
        "next",
        "nxt",
        "tail",
        "slow",
        "fast",
        "p",
        "q",
        "left",
        "right",
    }
)


def is_list_node(val: Any) -> bool:
    return (
        val is not None
        and hasattr(val, "val")
        and hasattr(val, "next")
        and not hasattr(val, "left")
    )


def is_tree_node(val: Any) -> bool:
    return (
        val is not None
        and hasattr(val, "val")
        and (hasattr(val, "left") or hasattr(val, "right"))
        and not is_list_node(val)
    )


def var_ll_kind(name: str) -> str:
    """返回 linked_list（整链起点）或 node_ref（指针）。"""
    low = name.lower().strip()
    if low in _LINKED_LIST_NAMES or low.endswith("head"):
        return "linked_list"
    if low in _NODE_REF_NAMES or low.endswith("prev") or low.endswith("curr") or low.endswith("next"):
        return "node_ref"
    # 默认：非 head 命名的 ListNode 视为指针（如局部变量 node）
    return "node_ref"


def register_node(node: Any, visited_ids: dict[int, str]) -> str | None:
    if node is None:
        return None
    oid = id(node)
    if oid in visited_ids:
        return visited_ids[oid]
    nid = f"n{len(visited_ids)}"
    visited_ids[oid] = nid
    return nid


def walk_list_edges(
    node: Any,
    nodes: dict[str, dict[str, Any]],
    visited_ids: dict[int, str],
    *,
    depth: int = 0,
) -> None:
    """将可达节点写入 nodes 表，next 为节点 id 或 null；防环、最大深度 50。"""
    if node is None or depth >= LL_MAX_DEPTH:
        return
    oid = id(node)
    if oid not in visited_ids:
        register_node(node, visited_ids)
    nid = visited_ids[oid]
    if nid not in nodes:
        nodes[nid] = {
            "id": nid,
            "val": getattr(node, "val", 0),
            "next": None,
        }
    nxt = getattr(node, "next", None)
    if nxt is None:
        nodes[nid]["next"] = None
        return
    nxt_id = register_node(nxt, visited_ids)
    nodes[nid]["next"] = nxt_id
    if nxt_id and nxt_id not in nodes:
        nodes[nxt_id] = {
            "id": nxt_id,
            "val": getattr(nxt, "val", 0),
            "next": None,
        }
    if nxt is not None and id(nxt) not in {id(node)}:
        walk_list_edges(nxt, nodes, visited_ids, depth=depth + 1)


def merge_nodes_from_locals(locals_dict: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """从当前帧所有 ListNode 变量合并出统一 nodes 表。"""
    nodes: dict[str, dict[str, Any]] = {}
    visited_ids: dict[int, str] = {}
    for _name, val in locals_dict.items():
        if is_list_node(val):
            walk_list_edges(val, nodes, visited_ids)
    return nodes


def register_tree_node(node: Any, visited_ids: dict[int, str]) -> str | None:
    if node is None:
        return None
    oid = id(node)
    if oid in visited_ids:
        return visited_ids[oid]
    nid = f"t{len(visited_ids)}"
    visited_ids[oid] = nid
    return nid


def walk_tree_edges(
    node: Any,
    nodes: dict[str, dict[str, Any]],
    visited_ids: dict[int, str],
    *,
    depth: int = 0,
) -> None:
    """BFS 写入 nodes 表；防环、最大节点数/深度。"""
    if node is None or depth >= TREE_MAX_DEPTH or len(nodes) >= TREE_MAX_NODES:
        return
    queue: list[tuple[Any, int]] = [(node, depth)]
    seen_obj: set[int] = set()
    while queue and len(nodes) < TREE_MAX_NODES:
        cur, d = queue.pop(0)
        if cur is None or d >= TREE_MAX_DEPTH:
            continue
        oid = id(cur)
        if oid in seen_obj:
            continue
        seen_obj.add(oid)
        nid = register_tree_node(cur, visited_ids)
        if nid is None:
            continue
        if nid not in nodes:
            nodes[nid] = {
                "id": nid,
                "val": getattr(cur, "val", 0),
                "left": None,
                "right": None,
            }
        left = getattr(cur, "left", None)
        right = getattr(cur, "right", None)
        left_id = register_tree_node(left, visited_ids) if left is not None else None
        right_id = register_tree_node(right, visited_ids) if right is not None else None
        nodes[nid]["left"] = left_id
        nodes[nid]["right"] = right_id
        if left is not None and id(left) not in seen_obj:
            queue.append((left, d + 1))
        if right is not None and id(right) not in seen_obj:
            queue.append((right, d + 1))


def merge_trees_from_locals(locals_dict: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """从当前帧所有 TreeNode 变量合并出统一 nodes 表。"""
    nodes: dict[str, dict[str, Any]] = {}
    visited_ids: dict[int, str] = {}
    for _name, val in locals_dict.items():
        if is_tree_node(val):
            walk_tree_edges(val, nodes, visited_ids)
    return nodes


def tree_snapshot(
    node: Any,
    tree_nodes: dict[str, dict[str, Any]],
    tree_visited: dict[int, str],
) -> dict[str, Any]:
    if node is None:
        return {"type": "none", "value": None}
    walk_tree_edges(node, tree_nodes, tree_visited)
    nid = register_tree_node(node, tree_visited)
    return {"type": "tree", "value": {"root": nid, "nodes": dict(tree_nodes)}}


def serialize_value(
    val: Any,
    visited_ids: dict[int, str],
    nodes: dict[str, dict[str, Any]],
    var_name: str,
    tree_visited: dict[int, str] | None = None,
    tree_nodes: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    将 Python 值转为 trace JSON 快照。
    链表：节点 id 稳定存放在 nodes 表，绝不输出内存地址。
    """
    if val is None:
        if var_name and var_ll_kind(var_name) == "node_ref":
            return {"type": "node_ref", "value": {"node": None, "nodes": dict(nodes)}}
        return {"type": "none", "value": None}

    if is_list_node(val):
        walk_list_edges(val, nodes, visited_ids)
        nid = register_node(val, visited_ids)
        kind = var_ll_kind(var_name)
        if kind == "linked_list":
            return {"type": "linked_list", "value": {"head": nid, "nodes": dict(nodes)}}
        return {"type": "node_ref", "value": {"node": nid, "nodes": dict(nodes)}}

    if is_tree_node(val):
        tn = tree_nodes if tree_nodes is not None else {}
        tv = tree_visited if tree_visited is not None else {}
        low = var_name.lower()
        if low in _TREE_POINTER_NAMES:
            walk_tree_edges(val, tn, tv)
            nid = register_tree_node(val, tv)
            return {"type": "tree_node_ref", "value": {"node": nid, "nodes": dict(tn)}}
        return tree_snapshot(val, tn, tv)

    if isinstance(val, bool):
        return {"type": "bool", "value": val}
    if isinstance(val, int):
        return {"type": "int", "value": val}
    if isinstance(val, float):
        return {"type": "float", "value": val}
    if isinstance(val, str):
        return {"type": "str", "value": val[:200]}
    if isinstance(val, dict):
        entries: list[dict[str, Any]] = []
        for k, v in list(val.items())[:64]:
            if isinstance(k, (int, float, bool, str)) and isinstance(v, (int, float, bool, str, type(None))):
                entries.append({"key": k, "value": v})
            else:
                entries.append({"key": str(k)[:32], "value": str(v)[:32]})
        return {"type": "dict", "value": {"entries": entries}}

    if isinstance(val, list):
        if is_matrix(val):
            return matrix_payload(val)
        flat = list(val[:64])
        if is_stack_var_name(var_name):
            items: list[str] = []
            for x in flat:
                if isinstance(x, str):
                    items.append(x[:8])
                elif isinstance(x, (int, float, bool)):
                    items.append(str(int(x) if isinstance(x, bool) else x))
                else:
                    items.append(str(x)[:8])
            return {"type": "stack", "value": items}
        return {"type": "list", "value": flat}

    try:
        from collections import deque

        if isinstance(val, deque):
            items: list[Any] = []
            for x in list(val)[:64]:
                if isinstance(x, bool):
                    items.append(int(x))
                elif isinstance(x, (int, float)):
                    items.append(int(x))
                else:
                    items.append(x)
            return {"type": "queue", "value": items}
    except ImportError:
        pass

    return {"type": "other", "value": str(val)[:120]}


def collect_frame_vars(locals_dict: dict[str, Any], skip: set[str]) -> dict[str, dict[str, Any]]:
    """收集一帧变量：先合并链表 nodes，再逐变量 serialize_value。"""
    filtered = {
        k: v
        for k, v in locals_dict.items()
        if not k.startswith("_") and k not in skip and not callable(v)
    }
    nodes = merge_nodes_from_locals(filtered)
    tree_nodes = merge_trees_from_locals(filtered)
    visited_ids: dict[int, str] = {}
    tree_visited: dict[int, str] = {}
    for k, v in filtered.items():
        if is_list_node(v):
            register_node(v, visited_ids)
        if is_tree_node(v):
            register_tree_node(v, tree_visited)
    out: dict[str, dict[str, Any]] = {}
    for k, v in filtered.items():
        try:
            out[k] = serialize_value(
                v, visited_ids, nodes, k, tree_visited=tree_visited, tree_nodes=tree_nodes
            )
        except Exception:
            out[k] = {"type": "other", "value": "?"}
    return out
