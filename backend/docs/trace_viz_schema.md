# 可视化调试 · `steps[].vars` JSON 协议

每步结构：

```json
{
  "line": 12,
  "changed": ["dp", "j"],
  "vars": {
    "dp": { "type": "matrix", "value": { "rows": 2, "cols": 2, "cells": [[1, 4], [3, 5]] } },
    "head": { "type": "linked_list", "value": { "head": "n0", "nodes": { "n0": { "id": "n0", "val": 1, "next": "n1" } } } },
    "curr": { "type": "node_ref", "value": { "node": "n1", "nodes": { "...": "..." } } },
    "root": { "type": "tree", "value": { "root": "t0", "nodes": { "t0": { "id": "t0", "val": 3, "left": null, "right": null } } } },
    "i": { "type": "int", "value": 0 }
  }
}
```

## `type` 枚举

| type | value | 前端组件 |
|------|-------|----------|
| `none` / `int` / `float` / `bool` / `str` | 标量 | 标量 chip |
| `list` | `number[]` | GameArrayBoard |
| `matrix` | `{ rows, cols, cells[][] }` | TraceMatrixGrid |
| `matrix_overflow` | `{ rows, cols, message }` | 警告条（超过 400 格） |
| `linked_list` | `{ head, nodes }` | TraceLinkedList |
| `node_ref` | `{ node, nodes }` | 指针悬浮在 TraceLinkedList（prev/curr/nxt） |
| `tree` | `{ root, nodes }` | TraceTreePanel |
| `sequence` | `unknown[]` + `view_hint`: `vector` \| `deque` \| `stack` \| `queue` \| `priority_queue` | TraceSequenceViz（通用线性） |
| `associative` | `{key,value}[]` + `view_hint`: `map` \| `set` \| `unordered_map` \| `unordered_set` | TraceAssociativeViz |
| `list` / `stack` / `queue` / `dict` | 同上（旧协议） | 前端自动归一化为 sequence / associative |
| `other` | string | 兜底 |

### 通用协议示例

```json
{
  "st": { "type": "sequence", "view_hint": "stack", "value": ["(", ")"] },
  "seen": {
    "type": "associative",
    "view_hint": "unordered_map",
    "value": [{ "key": 2, "value": 0 }]
  }
}
```

C++ 追踪由 `gdb_stl_extract.py`（GDB Python + Pretty-Printers）注入生成；失败时回退正则解析并同样归一化。

矩阵单元格高亮：前端对比相邻两步的 `cells`，不依赖后端逐格 `changed`。

## 确定性旁白（无 LLM）

见 `services/oj/trace_demo_narration.py`：`reverse-linked-list` → 链表旁白；`unique-paths` → DP 填表旁白。

追踪接口 `POST /api/oj/problems/{slug}/trace` 成功时自动附带 `narrations`。
