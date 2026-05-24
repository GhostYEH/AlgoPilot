

from __future__ import annotations

import json
import re

import gdb  # type: ignore

MAX_ITEMS = 64
TREE_MAX_NODES = 64
TREE_MAX_DEPTH = 30
MARKER_START = "@@TRACE_VIZ_JSON@@"
MARKER_END = "@@END@@"

_GDB_NOISE = frozenset(
    {
        "lock_free",
        "fiberid",
        "nested",
        "startinfo",
        "ret",
        "__saved_mask",
        "__unguarded",
        "__atomic",
    }
)


def _type_str(val: gdb.Value) -> str:
    try:
        return str(val.type)
    except Exception:
        return ""


def _gdb_print_text(val: gdb.Value) -> str:
    try:
        return str(val)
    except Exception:
        return ""


def _read_cpp_string(val: gdb.Value) -> str | None:
    """读取 std::string / basic_string（MinGW libstdc++ 多种布局）。"""
    try:
        s = val.string()
        if s is not None:
            return s
    except Exception:
        pass
    for path in (
        ("_M_dataplus", "_M_p"),
        ("_M_p",),
        ("_M_data",),
    ):
        try:
            cur = val
            for p in path:
                cur = cur[p]
            if int(cur) == 0:
                return ""
            raw = cur.string("utf-8", "ignore", 200)
            if raw is not None:
                return raw
        except Exception:
            continue
    try:
        length = int(val["_M_string_length"])
        if length <= 0:
            return ""
        for path in (("_M_dataplus", "_M_p"), ("_M_p",)):
            try:
                cur = val
                for p in path:
                    cur = cur[p]
                raw = cur.string("utf-8", "ignore", min(length, 200))
                if raw is not None:
                    return raw[:length]
            except Exception:
                continue
    except Exception:
        pass
    text = _gdb_print_text(val)
    for pat in (
        r'std::(?:basic_)?string[^"]*"([^"]*)"',
        r'=\s*"([^"]*)"',
        r'\[(\d+)\]\s*=\s*"([^"]*)"',
    ):
        m = re.search(pat, text)
        if m:
            return m.group(m.lastindex or 1)
    if text in ('""', "{}"):
        return ""
    return None


def _coerce_display_string(s: str | None, *, fallback: str = "?") -> str:
    if s is None or s in ("<string?>", "<未初始化>"):
        return fallback
    return s


def _parse_int_from_gdb_text(text: str, field: str = "val") -> int | None:
    m = re.search(rf"\b{re.escape(field)}\s*=\s*(-?\d+)\b", text)
    if m:
        return int(m.group(1))
    m2 = re.search(r"(-?\d+)", text)
    if m2 and field == "val":
        return int(m2.group(1))
    return None


def _read_int_from_value(val: gdb.Value) -> int | None:
    try:
        if val.type.code == gdb.TYPE_CODE_INT:
            return int(val)
    except Exception:
        pass
    try:
        t = _type_str(val)
        if "basic_string" not in t and "string" not in t:
            return int(val)
    except Exception:
        pass
    return None


def _tree_val_from_ptr(ptr: gdb.Value) -> int | str:
    """从 TreeNode* 读取 val（优先 C 表达式，避免把 int 误当 string）。"""
    try:
        if int(ptr) == 0:
            return "null"
    except Exception:
        return "?"
    addr = int(ptr)
    for expr in (
        f"(int)((TreeNode*){addr})->val",
        f"(int)((struct TreeNode*){addr})->val",
        f"((TreeNode*){addr})->val",
        f"((struct TreeNode*){addr})->val",
    ):
        try:
            v = gdb.parse_and_eval(expr)
            if "string" in _type_str(v):
                s = _read_cpp_string(v)
                if s is not None:
                    if s == "null":
                        return "null"
                    try:
                        return int(s)
                    except ValueError:
                        return s
            i = _read_int_from_value(v)
            if i is not None:
                return i
        except Exception:
            continue
    try:
        node = ptr.dereference()
        return _tree_val_from_node(node)
    except Exception:
        pass
    parsed = _parse_int_from_gdb_text(_gdb_print_text(ptr))
    if parsed is not None:
        return parsed
    return "?"


def _tree_val_from_node(node: gdb.Value) -> int | str:
    try:
        field = node["val"]
        ft = _type_str(field)
        if "basic_string" in ft or ("string" in ft and "TreeNode" not in ft):
            s = _read_cpp_string(field)
            if s is not None:
                if s == "null":
                    return "null"
                try:
                    return int(s)
                except ValueError:
                    return s
            return "?"
        i = _read_int_from_value(field)
        if i is not None:
            return i
    except Exception:
        pass
    try:
        addr = int(node.address)
        for expr in (
            f"(int)((TreeNode*){addr})->val",
            f"(int)((struct TreeNode*){addr})->val",
        ):
            try:
                return int(gdb.parse_and_eval(expr))
            except Exception:
                continue
    except Exception:
        pass
    parsed = _parse_int_from_gdb_text(_gdb_print_text(node))
    if parsed is not None:
        return parsed
    return "?"


def _parse_gdb_char_text(text: str) -> dict | None:
    """GDB 控制台/Value 字符串形如 ``40 '('`` 或 ``0 '\\000'``。"""
    text = text.strip()
    m = re.match(r"^(-?\d+)\s+'((?:\\.|[^'\\])*)'$", text)
    if not m:
        return None
    code = int(m.group(1))
    literal = m.group(2)
    if code == 0 or literal in ("\\000", "\\0"):
        return None
    if 32 <= code <= 126:
        return {"type": "str", "value": chr(code)}
    return None


def _scalar(val: gdb.Value) -> dict | None:
    t = _type_str(val)
    try:
        if "bool" in t and "vector" not in t and "basic_string" not in t:
            return {"type": "bool", "value": bool(int(val))}
        if any(x in t for x in ("char", "wchar", "unsigned char", "signed char")) and "basic_string" not in t:
            ch = int(val)
            if ch == 0 or ch < 32 or ch > 126:
                return None
            return {"type": "str", "value": chr(ch)}
        if any(x in t for x in ("int", "long", "short", "size_t")) and "*" not in t:
            return {"type": "int", "value": int(val)}
        if "float" in t or "double" in t:
            return {"type": "float", "value": float(val)}
        if "basic_string" in t or "std::string" in t:
            s = _read_cpp_string(val)
            if s is None:
                return None
            if s and any(ord(c) < 32 and c not in "\t\n\r" for c in s):
                return {"type": "other", "value": "<未初始化>"}
            return {"type": "str", "value": s[:200]}
    except Exception:
        pass
    return None


def _elem_display(child_val: gdb.Value) -> str | int | float | bool:
    if child_val.type.code == gdb.TYPE_CODE_PTR:
        try:
            if int(child_val) == 0:
                return "null"
            if _is_tree_node_ptr(child_val):
                return _tree_val_from_ptr(child_val)
        except Exception:
            pass
    else:
        text = _gdb_print_text(child_val)
        m = re.search(r"(0x[0-9a-fA-F]+)", text)
        if m:
            try:
                p = gdb.parse_and_eval(m.group(1))
                if _is_tree_node_ptr(p):
                    return _tree_val_from_ptr(p)
            except Exception:
                pass
    sc = _scalar(child_val)
    if sc:
        v = sc["value"]
        if isinstance(v, str) and len(v) == 1:
            return v
        if isinstance(v, str):
            return _coerce_display_string(v)
        return v
    t = _type_str(child_val)
    if "basic_string" in t or "std::string" in t:
        return _coerce_display_string(_read_cpp_string(child_val))
    try:
        parsed = _parse_gdb_char_text(str(child_val).strip())
        if parsed and isinstance(parsed.get("value"), str):
            return parsed["value"]
    except Exception:
        pass
    try:
        return int(child_val)
    except Exception:
        pass
    try:
        return str(child_val)[:32]
    except Exception:
        return "?"


def _children_from_pp(val: gdb.Value) -> list:
    try:
        pp = gdb.default_visualizer(val)
    except Exception:
        pp = None
    if pp is None:
        return []
    items: list = []
    try:
        if hasattr(pp, "children"):
            for i, child in enumerate(pp.children()):
                if i >= MAX_ITEMS:
                    break
                try:
                    items.append(_elem_display(child[1] if isinstance(child, tuple) else child))
                except Exception:
                    items.append("?")
        elif hasattr(pp, "display_hint") and pp.display_hint() == "array":
            for i in range(min(int(val.type.sizeof() // val[0].type.sizeof() if False else 0), 0)):
                pass
    except Exception:
        pass
    return items


def _vector_elements(val: gdb.Value) -> list:
    t = _type_str(val)
    if "vector" not in t:
        return []
    for path in (
        ("_M_impl", "_M_start"),
        ("_M_data",),
    ):
        try:
            start = val
            for p in path:
                start = start[p]
            finish = val["_M_impl"]["_M_finish"]
            size = int(finish - start)
            if size < 0 or size > MAX_ITEMS:
                return []
            out: list = []
            for i in range(size):
                out.append(_elem_display(start[i]))
            return out
        except Exception:
            continue
    pp_items = _children_from_pp(val)
    if pp_items:
        return pp_items
    return []


def _deque_elements(val: gdb.Value) -> list:
    t = _type_str(val)
    if "deque" not in t:
        return []
    pp_items = _children_from_pp(val)
    if pp_items:
        return pp_items
    for path in (("_M_impl", "_M_start"),):
        try:
            cur = val
            for p in path:
                cur = cur[p]
            n = int(val["_M_impl"]["_M_finish"] - cur)  # often wrong for deque
            if 0 <= n <= MAX_ITEMS:
                return [_elem_display(cur[i]) for i in range(n)]
        except Exception:
            pass
    return []


def _unwrap_adapter(val: gdb.Value) -> gdb.Value:
    t = _type_str(val)
    if not any(x in t for x in ("stack", "queue", "priority_queue")):
        return val
    for field in ("c", "_M_c", "_M_container", "comp", "_M_comp"):
        try:
            inner = val[field]
            if inner.type.code != gdb.TYPE_CODE_VOID:
                return inner
        except Exception:
            continue
    return val


def _map_entries(val: gdb.Value) -> list[dict]:
    t = _type_str(val)
    if not any(x in t for x in ("map", "unordered_map", "set", "unordered_set")):
        return []
    hint_unordered = "unordered" in t
    is_set = re.search(r"::set\b", t) is not None and "map" not in t.split("::")[-1]
    entries: list[dict] = []
    pp_items = _children_from_pp(val)
    if pp_items:
        for item in pp_items[:MAX_ITEMS]:
            if isinstance(item, dict) and "key" in item:
                entries.append(item)
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                k, v = item[0], item[1]
                entries.append({"key": k, "value": v})
            else:
                s = str(item)
                m = re.match(r"\[([^\]]+)\]\s*=\s*(.+)", s)
                if m:
                    entries.append({"key": m.group(1).strip(), "value": m.group(2).strip()})
                elif is_set:
                    entries.append({"key": str(item), "value": None})
        if entries:
            return entries
    try:
        tree = val["_M_t"]
        node = tree["_M_impl"]["_M_header"]["_M_left"]
        count = 0
        while count < MAX_ITEMS:
            if int(node) == 0:
                break
            if is_set:
                try:
                    k = node["_M_value_field"]
                except Exception:
                    k = node["_M_storage"]
                entries.append({"key": _elem_display(k), "value": None})
            else:
                try:
                    pair = node["_M_value_field"]
                    entries.append(
                        {
                            "key": _elem_display(pair["first"]),
                            "value": _elem_display(pair["second"]),
                        }
                    )
                except Exception:
                    pass
            try:
                node = node["_M_right"]
            except Exception:
                break
            count += 1
    except Exception:
        pass
    if not entries and hint_unordered:
        _ = is_set  # noqa: F841 — reserved for bucket walk
    return entries[:MAX_ITEMS]


def _contains_tree_node_ptr(val: gdb.Value) -> bool:
    t = _type_str(val)
    if "TreeNode" in t:
        return True
    if any(x in t for x in ("stack", "queue", "priority_queue", "deque")):
        inner = _unwrap_adapter(val)
        if "TreeNode" in _type_str(inner):
            return True
    if "vector" in t or "deque" in t:
        try:
            inner_t = str(val.type.strip_typedefs()) if hasattr(val.type, "strip_typedefs") else t
            if "TreeNode" in inner_t:
                return True
        except Exception:
            pass
    return False


def _view_hint_for_sequence(val: gdb.Value) -> str:
    t = _type_str(val)
    if _contains_tree_node_ptr(val):
        return "tree_build_queue"
    if "stack" in t:
        return "stack"
    if "priority_queue" in t:
        return "priority_queue"
    if "queue" in t:
        return "queue"
    if "deque" in t:
        return "deque"
    if "vector" in t:
        return "vector"
    return "vector"


_TREE_ROOT_NAMES = frozenset({"root", "tree", "t1", "t2"})
_TREE_POINTER_NAMES = frozenset(
    {"curr", "current", "left", "right", "node", "parent", "child", "p", "tail"}
)


def _view_hint_for_associative(val: gdb.Value) -> str:
    t = _type_str(val)
    if "unordered_map" in t:
        return "unordered_map"
    if "unordered_set" in t:
        return "unordered_set"
    if "map" in t:
        return "map"
    if "set" in t:
        return "set"
    return "map"


def _is_tree_node_ptr(val: gdb.Value) -> bool:
    try:
        if val.type.code != gdb.TYPE_CODE_PTR:
            return False
        if int(val) == 0:
            return False
        pointee = val.dereference()
        t = _type_str(pointee)
        if "TreeNode" in t:
            return True
        for field in ("val", "left", "right"):
            try:
                _ = pointee[field]
            except Exception:
                return False
        else:
            return True
    except Exception:
        return False


def _tree_field_val(node: gdb.Value, name: str) -> int | str:
    if name == "val":
        return _tree_val_from_node(node)
    try:
        field = node[name]
        i = _read_int_from_value(field)
        if i is not None:
            return i
    except Exception:
        pass
    return "?"


def _tree_field_ptr(node: gdb.Value, name: str) -> gdb.Value | None:
    try:
        p = node[name]
        if int(p) == 0:
            return None
        return p
    except Exception:
        return None


def _register_tree_ptr(
    ptr: gdb.Value,
    tree_nodes: dict[str, dict],
    ptr_to_id: dict[int, str],
) -> str | None:
    try:
        addr = int(ptr)
    except Exception:
        return None
    if addr == 0:
        return None
    if addr in ptr_to_id:
        return ptr_to_id[addr]
    nid = f"t{len(ptr_to_id)}"
    ptr_to_id[addr] = nid
    return nid


def _walk_tree_ptr(
    root_ptr: gdb.Value,
    tree_nodes: dict[str, dict],
    ptr_to_id: dict[int, str],
) -> None:
    if int(root_ptr) == 0 or len(tree_nodes) >= TREE_MAX_NODES:
        return
    queue: list[tuple[gdb.Value, int]] = [(root_ptr, 0)]
    seen: set[int] = set()
    while queue and len(tree_nodes) < TREE_MAX_NODES:
        ptr, depth = queue.pop(0)
        try:
            addr = int(ptr)
        except Exception:
            continue
        if addr == 0 or depth >= TREE_MAX_DEPTH or addr in seen:
            continue
        seen.add(addr)
        nid = _register_tree_ptr(ptr, tree_nodes, ptr_to_id)
        if nid is None:
            continue
        if nid not in tree_nodes:
            try:
                node = ptr.dereference()
            except Exception:
                continue
            left_ptr = _tree_field_ptr(node, "left")
            right_ptr = _tree_field_ptr(node, "right")
            left_id = (
                _register_tree_ptr(left_ptr, tree_nodes, ptr_to_id) if left_ptr is not None else None
            )
            right_id = (
                _register_tree_ptr(right_ptr, tree_nodes, ptr_to_id)
                if right_ptr is not None
                else None
            )
            raw_val = _tree_field_val(node, "val")
            tree_nodes[nid] = {
                "id": nid,
                "val": raw_val if raw_val != "?" else 0,
                "left": left_id,
                "right": right_id,
            }
            if left_ptr is not None and int(left_ptr) not in seen:
                queue.append((left_ptr, depth + 1))
            if right_ptr is not None and int(right_ptr) not in seen:
                queue.append((right_ptr, depth + 1))


def _tree_snapshot(
    ptr: gdb.Value,
    tree_nodes: dict[str, dict],
    ptr_to_id: dict[int, str],
) -> dict:
    try:
        if int(ptr) == 0:
            return {"type": "none", "value": None}
    except Exception:
        return {"type": "none", "value": None}
    _walk_tree_ptr(ptr, tree_nodes, ptr_to_id)
    root_id = ptr_to_id.get(int(ptr))
    return {"type": "tree", "value": {"root": root_id, "nodes": dict(tree_nodes)}}


def _serialize_value(
    val: gdb.Value,
    var_name: str = "",
    tree_nodes: dict[str, dict] | None = None,
    ptr_to_id: dict[int, str] | None = None,
) -> dict | None:
    t = _type_str(val)
    if val.type.code == gdb.TYPE_CODE_PTR:
        try:
            if int(val) == 0:
                if var_name.lower() in ("root", "left", "right", "node", "p", "q"):
                    return {"type": "none", "value": None}
                return {"type": "node_ref", "value": {"node": None, "nodes": {}}}
        except Exception:
            pass
        if _is_tree_node_ptr(val):
            tn = tree_nodes if tree_nodes is not None else {}
            pid = ptr_to_id if ptr_to_id is not None else {}
            low = var_name.lower()
            if low in _TREE_POINTER_NAMES:
                _walk_tree_ptr(val, tn, pid)
                nid = ptr_to_id.get(int(val)) if ptr_to_id is not None else None
                return {
                    "type": "tree_node_ref",
                    "value": {"node": nid, "nodes": dict(tn)},
                }
            if low in _TREE_ROOT_NAMES or low == "root":
                return _tree_snapshot(val, tn, pid)
            return _tree_snapshot(val, tn, pid)
        return {"type": "other", "value": str(val)[:120]}

    sc = _scalar(val)
    if sc:
        return sc

    char_snap = _parse_gdb_char_text(str(val).strip())
    if char_snap:
        return char_snap

    if any(x in t for x in ("stack", "queue", "priority_queue")):
        inner = _unwrap_adapter(val)
        items = _deque_elements(inner) or _vector_elements(inner)
        return {
            "type": "sequence",
            "view_hint": _view_hint_for_sequence(val),
            "value": items,
        }

    if "vector" in t:
        return {
            "type": "sequence",
            "view_hint": "vector",
            "value": _vector_elements(val),
        }

    if "deque" in t:
        return {
            "type": "sequence",
            "view_hint": "deque",
            "value": _deque_elements(val),
        }

    if any(x in t for x in ("map", "unordered_map", "set", "unordered_set")):
        entries = _map_entries(val)
        return {
            "type": "associative",
            "view_hint": _view_hint_for_associative(val),
            "value": entries,
        }

    if val.type.code == gdb.TYPE_CODE_ARRAY:
        try:
            n = int(val.type.sizeof() // val[0].type.sizeof())
            if 0 < n <= MAX_ITEMS:
                return {
                    "type": "sequence",
                    "view_hint": "vector",
                    "value": [_elem_display(val[i]) for i in range(n)],
                }
        except Exception:
            pass

    return {"type": "other", "value": str(val)[:120]}


def _iter_local_names() -> list[str]:
    frame = gdb.selected_frame()
    if frame is None:
        return []
    names: list[str] = []
    block = frame.block()
    seen: set[str] = set()
    while block is not None:
        try:
            for sym in block:
                if not sym.is_argument and not sym.is_variable:
                    continue
                n = sym.name
                if not n or n.startswith("__") or n in _GDB_NOISE:
                    continue
                if n not in seen:
                    seen.add(n)
                    names.append(n)
        except Exception:
            pass
        try:
            block = block.superblock
        except Exception:
            break
    return names


def _dump_locals_dict() -> dict[str, dict]:
    tree_nodes: dict[str, dict] = {}
    ptr_to_id: dict[int, str] = {}
    names = _iter_local_names()
    for name in names:
        try:
            val = gdb.parse_and_eval(name)
            if _is_tree_node_ptr(val):
                _walk_tree_ptr(val, tree_nodes, ptr_to_id)
        except Exception:
            pass
    out: dict[str, dict] = {}
    for name in names:
        try:
            val = gdb.parse_and_eval(name)
            snap = _serialize_value(val, name, tree_nodes, ptr_to_id)
            if snap is None:
                continue
            if snap.get("type") == "other":
                text = str(snap.get("value", ""))
                if "Cannot access memory" in text or (
                    text.startswith("<") and (":" in text or "?" in text)
                ):
                    continue
            out[name] = snap
        except Exception:
            continue
    return out


class TraceVizDumpLocals(gdb.Command):
    """Dump locals as trace_viz JSON between markers."""

    def __init__(self) -> None:
        super().__init__("trace-viz-dump-locals", gdb.COMMAND_USER, gdb.COMPLETE_NONE)

    def invoke(self, _arg: str, _from_tty: bool) -> None:
        try:
            payload = _dump_locals_dict()
            blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        except Exception as e:
            blob = json.dumps({"__error": str(e)})
        gdb.write(f"{MARKER_START}{blob}{MARKER_END}\n")
        


TraceVizDumpLocals()
