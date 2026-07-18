"""修复 tests_bundle.json 中 Binary Tree 类题目的错误测试用例。

对每个目标题目：
1. 使用参考解法重新计算 expected（对 verify_test_cases.py 中存在 bug 的题目，
   使用本文件内的更稳健的解法）。
2. 若 expected 与参考解法结果不一致，则更新 expected。
3. 用 services.oj.stdio_io.leetcode_case_to_stdio 重新生成 stdin/stdout。
4. 对于 symmetric-tree：hidden[6]-[9] 原为 same-tree 的双树用例（错误），
   用正确的 symmetric-tree 单树用例替换。
5. 写回 tests_bundle.json，并打印每道题修改了哪些用例。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

from services.oj.stdio_io import leetcode_case_to_stdio  # noqa: E402
from verify_test_cases import (  # noqa: E402
    SOLUTIONS,
    compare_result,
    tree_to_list,
)

BUNDLE_PATH = BACKEND / "data" / "oj" / "tests_bundle.json"

TARGET_SLUGS = [
    "symmetric-tree",
    "same-tree",
    "invert-binary-tree",
    "maximum-depth-of-binary-tree",
    "minimum-depth-of-binary-tree",
    "balanced-binary-tree",
    "path-sum",
    "path-sum-ii",
    "binary-tree-paths",
    "binary-tree-inorder-traversal",
    "binary-tree-postorder-traversal",
    "binary-tree-right-side-view",
    "average-of-levels-in-binary-tree",
    "merge-two-binary-trees",
    "sum-of-left-leaves",
    "find-bottom-left-tree-value",
    "maximum-binary-tree",
    "convert-bst-to-greater-tree",
    "convert-sorted-array-to-binary-search-tree",
    "trim-a-binary-search-tree",
    "search-in-a-binary-search-tree",
    "insert-into-a-binary-search-tree",
    "delete-node-in-a-bst",
    "lowest-common-ancestor-of-a-binary-tree",
    "construct-binary-tree-from-preorder-and-inorder-traversal",
    "construct-binary-tree-from-inorder-and-postorder-traversal",
    "subtree-of-another-tree",
]


# ─── 稳健的工具函数 ───

def list_to_tree_safe(arr):
    """LeetCode 层序数组 → 二叉树。

    与 verify_test_cases.list_to_tree 行为一致，但对 [None, ...]
    （根为 null）按 LeetCode 语义视作空树，避免出现 val=None 的节点。
    """
    if not arr or arr[0] is None:
        return None
    root = {"val": arr[0], "left": None, "right": None}
    queue = [root]
    i = 1
    while queue and i < len(arr):
        node = queue.pop(0)
        if i < len(arr) and arr[i] is not None:
            node["left"] = {"val": arr[i], "left": None, "right": None}
            queue.append(node["left"])
        i += 1
        if i < len(arr) and arr[i] is not None:
            node["right"] = {"val": arr[i], "left": None, "right": None}
            queue.append(node["right"])
        i += 1
    return root


# ─── 对 verify_test_cases.py 中存在 bug 的题目提供更稳健的解法 ───

def _merge_two_binary_trees_safe(p, q):
    """合并两棵二叉树（LC 617）。

    verify_test_cases._merge_two_trees 在 arr[0] is None 时会构造
    val=None 的根节点并触发 `int + None` 异常；这里使用
    list_to_tree_safe 以避免该问题。
    """
    t1 = list_to_tree_safe(p)
    t2 = list_to_tree_safe(q)

    def merge(a, b):
        if not a:
            return b
        if not b:
            return a
        a["val"] += b["val"]
        a["left"] = merge(a["left"], b["left"])
        a["right"] = merge(a["right"], b["right"])
        return a

    return tree_to_list(merge(t1, t2))


def _construct_from_in_post_safe(inorder, postorder):
    """由中序+后序构造二叉树（LC 106）。

    verify_test_cases._construct_from_in_post 的 build 函数中有一行
    `right = build(ino[idx+1:], post[idx:idx+1] if ... else post[idx:])`
    会先于正确的 `right = build(ino[idx+1:], post[idx:-1])` 执行并可能抛
    `ValueError: x is not in list`；这里只保留正确的右子树切片。
    """
    def build(ino, post):
        if not post:
            return None
        root_val = post[-1]
        idx = ino.index(root_val)
        left = build(ino[:idx], post[:idx])
        right = build(ino[idx + 1:], post[idx:-1])
        return {"val": root_val, "left": left, "right": right}

    return tree_to_list(build(inorder, postorder))


# 覆盖 SOLUTIONS 中存在 bug 的解法
SOLUTIONS_OVERRIDES: dict[str, Any] = {
    "merge-two-binary-trees": lambda args: _merge_two_binary_trees_safe(*args),
    "construct-binary-tree-from-inorder-and-postorder-traversal": (
        lambda args: _construct_from_in_post_safe(*args)
    ),
}


# ─── symmetric-tree 错误用例的替换 ───

# hidden[6]-[9] 原为 same-tree 风格的双树用例，与 symmetric-tree 题意不符。
# 替换为正确的单树用例（去重 hidden[0]-[5] 已有情形）。
SYMMETRIC_TREE_REPLACEMENTS = [
    {"args": [[1, 2, 2, 3, None, None, 3]], "expected": True},   # 镜像结构
    {"args": [[2, 3, 3, 4, 5, 5, 4]], "expected": True},          # 经典对称
    {"args": [[1, 2, 2, None, 3, None, 4]], "expected": False},   # 末层不对称
    {"args": [[1, None, 2, None, 3]], "expected": False},         # 右斜链
]


def _format_value(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False)


def fix_case(
    slug: str, label: str, idx: int, case: dict, solver
) -> list[str]:
    """修复单个用例，返回变更描述列表。"""
    changes: list[str] = []
    args = case.get("args")
    if args is None:
        args = []
        case["args"] = args

    # 运行参考解法
    try:
        actual = solver(args)
    except Exception as e:
        changes.append(f"参考解法异常: {type(e).__name__}: {e}")
        return changes

    # 比较 expected
    old_expected = case.get("expected")
    if not compare_result(old_expected, actual, slug):
        changes.append(
            f"expected 修复: {_format_value(old_expected)} -> {_format_value(actual)}"
        )
        case["expected"] = actual

    # 重新生成 stdin/stdout
    new_stdin, new_stdout = leetcode_case_to_stdio(args, case.get("expected"))
    old_stdin = case.get("stdin")
    old_stdout = case.get("stdout")
    if old_stdin != new_stdin:
        changes.append(
            f"stdin 修复: {_format_value(old_stdin)} -> {_format_value(new_stdin)}"
        )
        case["stdin"] = new_stdin
    if old_stdout != new_stdout:
        changes.append(
            f"stdout 修复: {_format_value(old_stdout)} -> {_format_value(new_stdout)}"
        )
        case["stdout"] = new_stdout

    return changes


def replace_symmetric_tree_hidden(hidden: list[dict]) -> int:
    """替换 symmetric-tree 中错误的双树 hidden 用例。"""
    replaced = 0
    for i in range(6, min(10, len(hidden))):
        replacement_idx = i - 6
        if replacement_idx >= len(SYMMETRIC_TREE_REPLACEMENTS):
            break
        new = SYMMETRIC_TREE_REPLACEMENTS[replacement_idx]
        stdin, stdout = leetcode_case_to_stdio(new["args"], new["expected"])
        hidden[i] = {
            "args": new["args"],
            "expected": new["expected"],
            "stdin": stdin,
            "stdout": stdout,
        }
        replaced += 1
    return replaced


def main() -> int:
    bundle = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
    total_changed_cases = 0

    for slug in TARGET_SLUGS:
        cfg = bundle.get(slug)
        if cfg is None:
            print(f"[警告] 题目 {slug} 不存在，跳过")
            continue

        solver = SOLUTIONS_OVERRIDES.get(slug) or SOLUTIONS.get(slug)
        if solver is None:
            print(f"[警告] 题目 {slug} 无参考解法，跳过")
            continue

        print(f"\n=== [{slug}] ===")
        slug_changed = 0

        # symmetric-tree 特殊处理：替换错误的双树 hidden 用例
        if slug == "symmetric-tree":
            hidden = cfg.get("hidden") or []
            replaced = replace_symmetric_tree_hidden(hidden)
            for i in range(6, 6 + replaced):
                new_case = hidden[i]
                print(
                    f"  hidden[{i}] 替换为单树用例: "
                    f"args={_format_value(new_case['args'])} "
                    f"expected={_format_value(new_case['expected'])}"
                )
                slug_changed += 1

        for label in ("samples", "hidden"):
            cases = cfg.get(label) or []
            for i, case in enumerate(cases):
                changes = fix_case(slug, label, i, case, solver)
                if changes:
                    print(f"  {label}[{i}]:")
                    for ch in changes:
                        print(f"    - {ch}")
                    slug_changed += 1

        if slug_changed == 0:
            print("  无变更")
        total_changed_cases += slug_changed

    # 写回
    BUNDLE_PATH.write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n=== 总结 ===")
    print(f"共修改 {total_changed_cases} 个用例")
    print(f"已写回 {BUNDLE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
