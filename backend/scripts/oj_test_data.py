"""OJ 测例与题目配置（由 build_oj_data.py 写入 tests_bundle.json）。"""

from __future__ import annotations

from typing import Any

from services.oj.stdio_io import ensure_stdio_fields

STDIO_STARTER_PY = (
    "import sys\n\n\n"
    "def main():\n"
    "    # 洛谷风格：从标准输入读入，向标准输出写出答案\n"
    "    # data = sys.stdin.read().split()\n"
    "    pass\n\n\n"
    "if __name__ == '__main__':\n"
    "    main()\n"
)

STDIO_STARTER_CPP = (
    "#include <bits/stdc++.h>\n"
    "using namespace std;\n\n"
    "int main() {\n"
    "    ios::sync_with_stdio(false);\n"
    "    cin.tie(nullptr);\n"
    "    // 洛谷风格：cin 读入，cout 输出\n"
    "    return 0;\n"
    "}\n"
)


def _cpp_type(val: Any, *, list_node: bool = False) -> str:
    if list_node:
        return "ListNode*"
    if isinstance(val, list):
        if not val:
            return "vector<int>"
        if all(isinstance(x, int) for x in val):
            return "vector<int>"
        if all(isinstance(x, str) for x in val):
            return "vector<string>"
        if all(isinstance(x, list) for x in val) and all(
            isinstance(y, int) for row in val for y in row
        ):
            return "vector<vector<int>>"
    if isinstance(val, int):
        return "int"
    if isinstance(val, str):
        return "string"
    if isinstance(val, bool):
        return "bool"
    return "auto"


def _cpp_return_type(expected: Any, *, needs_list_node: bool) -> str:
    if needs_list_node:
        return "ListNode*"
    if expected is None:
        return "void"
    if isinstance(expected, bool):
        return "bool"
    if isinstance(expected, int):
        return "int"
    if isinstance(expected, str):
        return "string"
    if isinstance(expected, list):
        if not expected:
            return "vector<int>"
        if all(isinstance(x, int) for x in expected):
            return "vector<int>"
        if all(isinstance(x, list) for x in expected):
            return "vector<vector<int>>"
    return "void"


def _cpp_list_node_prelude(*, needs_list_node: bool) -> str:
    """链表题由评测器注入 ListNode 定义，模板中不再重复声明。"""
    if needs_list_node:
        return ""
    return (
        "struct ListNode {\n"
        "    int val;\n"
        "    ListNode* next;\n"
        "    ListNode(int x) : val(x), next(nullptr) {}\n"
        "};\n\n"
    )


def _cpp_starter(
    method: str,
    samples: list[dict[str, Any]],
    *,
    list_arg_indices: list[int] | None,
    needs_list_node: bool,
) -> str:
    list_idx = set(list_arg_indices or [])
    list_prelude = _cpp_list_node_prelude(needs_list_node=needs_list_node)
    if not samples:
        return (
            "#include <bits/stdc++.h>\nusing namespace std;\n\n"
            + list_prelude
            + "class Solution {\npublic:\n"
            f"    void {method}() {{}}\n}};\n"
        )
    args = samples[0]["args"]
    expected = samples[0].get("expected")
    ret = _cpp_return_type(expected, needs_list_node=needs_list_node)
    if (
        len(args) == 1
        and isinstance(args[0], dict)
        and "a" in args[0]
        and "b" in args[0]
    ):
        return (
            "#include <bits/stdc++.h>\n"
            "using namespace std;\n\n"
            + list_prelude
            + "class Solution {\n"
            "public:\n"
            f"    ListNode* {method}(ListNode* headA, ListNode* headB) {{\n"
            "        return nullptr;\n"
            "    }\n"
            "};\n"
        )
    param_names = ("nums", "target", "s", "t", "head", "root", "a", "b", "c")
    params: list[str] = []
    for i, arg in enumerate(args):
        t = _cpp_type(arg, list_node=i in list_idx)
        name = param_names[i] if i < len(param_names) else f"arg{i}"
        if t.startswith("vector"):
            params.append(f"const {t}& {name}")
        elif t == "string":
            params.append(f"const string& {name}")
        else:
            params.append(f"{t} {name}")
    sig = ", ".join(params)
    if ret == "void":
        body = ""
    elif ret == "ListNode*":
        body = "return nullptr;"
    elif ret.startswith("vector"):
        body = f"return {ret}{{}};"
    elif ret == "bool":
        body = "return false;"
    elif ret == "int":
        body = "return 0;"
    elif ret == "string":
        body = 'return "";'
    else:
        body = ""
    return (
        "#include <bits/stdc++.h>\n"
        "using namespace std;\n\n"
        + list_prelude
        + "class Solution {\n"
        "public:\n"
        f"    {ret} {method}({sig}) {{\n"
        f"        {body}\n"
        "    }\n"
        "};\n"
    )


def _needs_leetcode_judge(
    *,
    samples: list[dict[str, Any]],
    hidden: list[dict[str, Any]] | None,
    list_arg_indices: list[int] | None,
    tree_arg_indices: list[int] | None,
    needs_list_node: bool,
) -> bool:
    """全站统一洛谷 stdio 判题，不再使用力扣 class Solution 包装。"""
    _ = (samples, hidden, list_arg_indices, tree_arg_indices, needs_list_node)
    return False


def _stdio(
    *,
    samples: list[dict[str, Any]],
    hidden: list[dict[str, Any]] | None = None,
    difficulty: str = "medium",
    description: str = "",
    order_insensitive: bool = False,
) -> dict[str, Any]:
    """洛谷风格：测例直接给出 stdin/stdout，完整 main 程序判题。"""
    desc = description or "按洛谷格式编写完整程序，使用标准输入/输出（cin/cout 或 input/print）。"
    return {
        "difficulty": difficulty,
        "description": desc,
        "judge_mode": "stdio",
        "entry": {"mode": "stdio"},
        "starter_code": {"python": STDIO_STARTER_PY, "cpp": STDIO_STARTER_CPP},
        "samples": samples,
        "hidden": hidden or [],
        "order_insensitive": order_insensitive,
    }


def _p(
    method: str,
    *,
    samples: list[dict[str, Any]],
    hidden: list[dict[str, Any]] | None = None,
    difficulty: str = "medium",
    description: str = "",
    order_insensitive: bool = False,
    list_arg_indices: list[int] | None = None,
    tree_arg_indices: list[int] | None = None,
    needs_list_node: bool = False,
) -> dict[str, Any]:
    hidden = hidden or []

    if not _needs_leetcode_judge(
        samples=samples,
        hidden=hidden,
        list_arg_indices=list_arg_indices,
        tree_arg_indices=tree_arg_indices,
        needs_list_node=needs_list_node,
    ):
        std_samples = [ensure_stdio_fields(c) for c in samples]
        std_hidden = [ensure_stdio_fields(c) for c in hidden]
        desc = description or "按洛谷格式编写完整程序，使用标准输入/输出（cin/cout 或 input/print）。"
        if tree_arg_indices or list_arg_indices or needs_list_node:
            desc += (
                "\n\n**输入约定**：整数序列先给个数再跟数值；二叉树层序用 `null` 表示空结点；"
                "相交链表依次给出 `a` 长度与 `a` 结点、`b` 长度与 `b` 结点、公共后缀长度与结点值。"
            )
        return {
            "difficulty": difficulty,
            "description": desc,
            "judge_mode": "stdio",
            "entry": {"mode": "stdio"},
            "starter_code": {"python": STDIO_STARTER_PY, "cpp": STDIO_STARTER_CPP},
            "samples": std_samples,
            "hidden": std_hidden,
            "order_insensitive": order_insensitive,
        }

    entry: dict[str, Any] = {"class": "Solution", "method": method}
    if list_arg_indices:
        entry["list_arg_indices"] = list_arg_indices
    if tree_arg_indices:
        entry["tree_arg_indices"] = tree_arg_indices
    if needs_list_node:
        entry["needs_list_node"] = True
    starter_py = (
        "from typing import List, Optional\n\n\n"
        f"class Solution:\n"
        f"    def {method}(self, *args, **kwargs):\n"
        "        pass\n"
    )
    starter_cpp = _cpp_starter(
        method,
        samples,
        list_arg_indices=list_arg_indices,
        needs_list_node=needs_list_node,
    )
    return {
        "difficulty": difficulty,
        "description": description,
        "judge_mode": "leetcode",
        "entry": entry,
        "starter_code": {"python": starter_py, "cpp": starter_cpp},
        "samples": samples,
        "hidden": hidden,
        "order_insensitive": order_insensitive,
    }


TEST_DEFINITIONS: dict[str, dict[str, Any]] = {
    "two-sum": _p(
        "twoSum",
        difficulty="easy",
        description="给定整数数组 nums 与 target，返回两数之和等于 target 的两个下标。",
        samples=[{"args": [[2, 7, 11, 15], 9], "expected": [0, 1]}],
        hidden=[
            {"args": [[3, 3], 6], "expected": [0, 1]},
            {"args": [[2, 5, 5, 11], 10], "expected": [0, 2]},
        ],
        order_insensitive=True,
    ),
    "valid-anagram": _p(
        "isAnagram",
        difficulty="easy",
        samples=[{"args": ["anagram", "nagaram"], "expected": True}],
        hidden=[{"args": ["rat", "car"], "expected": False}],
    ),
    "happy-number": _p(
        "isHappy",
        difficulty="easy",
        samples=[{"args": [19], "expected": True}],
        hidden=[{"args": [2], "expected": False}],
    ),
    "binary-search": _p(
        "search",
        difficulty="easy",
        samples=[{"args": [[-1, 0, 3, 5, 9, 12], 9], "expected": 4}],
        hidden=[{"args": [[-1, 0, 3, 5, 9, 12], 2], "expected": -1}],
    ),
    "remove-element": _p(
        "removeElement",
        difficulty="easy",
        samples=[{"args": [[0, 1, 2, 2, 3, 0, 4, 2], 2], "expected": 5}],
        hidden=[{"args": [[3, 2, 2, 3], 3], "expected": 2}],
    ),
    "remove-duplicates-from-sorted-array": _p(
        "removeDuplicates",
        difficulty="easy",
        samples=[{"args": [[0, 0, 1, 1, 1, 2, 2, 3, 3, 4]], "expected": 5}],
        hidden=[{"args": [[1, 1, 2]], "expected": 2}],
    ),
    "move-zeroes": _p(
        "moveZeroes",
        difficulty="easy",
        samples=[
            {
                "args": [[0, 1, 0, 3, 12]],
                "expected": [1, 3, 12, 0, 0],
                "in_place_arg": 0,
            }
        ],
    ),
    "reverse-string": _p(
        "reverseString",
        difficulty="easy",
        samples=[
            {
                "args": [["h", "e", "l", "l", "o"]],
                "expected": ["o", "l", "l", "e", "h"],
                "in_place_arg": 0,
            }
        ],
    ),
    "ti-huan-kong-ge-lcof": _p(
        "replaceSpace",
        difficulty="easy",
        description="剑指 Offer 05：将字符串中的空格替换为 `%20`。",
        samples=[{"args": ["We are happy."], "expected": "We%20are%20happy."}],
        hidden=[{"args": ["  hello world  "], "expected": "%20%20hello%20world%20%20"}],
    ),
    "replace-space-lcof": _p(
        "replaceSpace",
        difficulty="easy",
        description="剑指 Offer 05：将字符串中的空格替换为 `%20`。",
        samples=[{"args": ["We are happy."], "expected": "We%20are%20happy."}],
    ),
    "backspace-string-compare": _p(
        "backspaceCompare",
        difficulty="easy",
        samples=[{"args": ["ab#c", "ad#c"], "expected": True}],
        hidden=[{"args": ["ab##", "c#d#"], "expected": True}],
    ),
    "climbing-stairs": _p(
        "climbStairs",
        difficulty="easy",
        samples=[{"args": [2], "expected": 2}, {"args": [3], "expected": 3}],
        hidden=[{"args": [5], "expected": 8}],
    ),
    "fibonacci-number": _p(
        "fib",
        difficulty="easy",
        samples=[{"args": [10], "expected": 55}],
        hidden=[{"args": [4], "expected": 3}],
    ),
    "coin-change": _p(
        "coinChange",
        difficulty="medium",
        samples=[{"args": [[1, 2, 5], 11], "expected": 3}],
        hidden=[{"args": [[2], 3], "expected": -1}],
    ),
    "longest-increasing-subsequence": _p(
        "lengthOfLIS",
        difficulty="medium",
        samples=[{"args": [[10, 9, 2, 5, 3, 7, 101, 18]], "expected": 4}],
    ),
    "implement-queue-using-stacks": _stdio(
        difficulty="easy",
        description=(
            "## 用栈实现队列（232）\n\n"
            "请按洛谷格式编写完整程序，从标准输入读入操作序列，向标准输出写出每次有返回值的操作结果。\n\n"
            "**输入**：第一行整数 `n`；接下来 `n` 行，每行一条操作：`push x`、`pop`、`peek`、`empty`。\n\n"
            "**输出**：`pop` / `peek` 各输出一行整数；`empty` 输出 `true` 或 `false`（小写）。"
        ),
        samples=[
            {
                "stdin": "5\npush 1\npush 2\npop\npeek\nempty\n",
                "stdout": "1\n2\nfalse\n",
            }
        ],
        hidden=[
            {
                "stdin": "4\npush 1\npop\npush 2\npeek\n",
                "stdout": "1\n2\n",
            }
        ],
    ),
    "implement-stack-using-queues": _stdio(
        difficulty="easy",
        description=(
            "## 用队列实现栈（225）\n\n"
            "请按洛谷格式编写完整程序，从标准输入读入操作序列，向标准输出写出每次有返回值的操作结果。\n\n"
            "**输入**：第一行整数 `n`；接下来 `n` 行，每行一条操作：`push x`、`pop`、`top`、`empty`。\n\n"
            "**输出**：`pop` / `top` 各输出一行整数；`empty` 输出 `true` 或 `false`（小写）。"
        ),
        samples=[
            {
                "stdin": "5\npush 1\npush 2\npop\ntop\nempty\n",
                "stdout": "2\n1\nfalse\n",
            }
        ],
        hidden=[
            {
                "stdin": "3\npush 1\npush 2\npop\n",
                "stdout": "2\n",
            }
        ],
    ),
    "valid-parentheses": _p(
        "isValid",
        difficulty="easy",
        samples=[{"args": ["()"], "expected": True}, {"args": ["()[]{}"], "expected": True}],
        hidden=[{"args": ["(]"], "expected": False}],
    ),
    "daily-temperatures": _p(
        "dailyTemperatures",
        difficulty="medium",
        samples=[
            {
                "args": [[73, 74, 75, 71, 69, 72, 76, 73]],
                "expected": [1, 1, 4, 2, 1, 1, 0, 0],
            }
        ],
    ),
    "next-greater-element-i": _p(
        "nextGreaterElement",
        difficulty="easy",
        samples=[{"args": [[4, 1, 2], [1, 3, 4, 2]], "expected": [-1, 3, -1]}],
    ),
    "maximum-depth-of-binary-tree": _p(
        "maxDepth",
        difficulty="easy",
        tree_arg_indices=[0],
        samples=[{"args": [[3, 9, 20, None, None, 15, 7]], "expected": 3}],
    ),
    "invert-binary-tree": _p(
        "invertTree",
        difficulty="easy",
        tree_arg_indices=[0],
        samples=[{"args": [[4, 2, 7, 1, 3, 6, 9]], "expected": [4, 7, 2, 9, 6, 3, 1]}],
    ),
    "symmetric-tree": _p(
        "isSymmetric",
        difficulty="easy",
        tree_arg_indices=[0],
        samples=[{"args": [[1, 2, 2, 3, 4, 4, 3]], "expected": True}],
        hidden=[{"args": [[1, 2, 2, None, None, None, 3]], "expected": False}],
    ),
    "reverse-linked-list": _p(
        "reverseList",
        difficulty="easy",
        list_arg_indices=[0],
        needs_list_node=True,
        samples=[{"args": [[1, 2, 3, 4, 5]], "expected": [5, 4, 3, 2, 1]}],
    ),
    "linked-list-cycle": _p(
        "hasCycle",
        difficulty="easy",
        list_arg_indices=[0],
        needs_list_node=True,
        samples=[{"args": [[3, 2, 0, -4]], "expected": False}],
    ),
    "linked-list-cycle-ii": _p(
        "detectCycle",
        difficulty="medium",
        list_arg_indices=[0],
        needs_list_node=True,
        description="给定链表头，返回环入口节点；无环返回 null。判题输出为入口下标对应的值列表或 null。",
        samples=[{"args": [[3, 2, 0, -4]], "expected": None}],
        hidden=[{"args": [[1, 2]], "expected": None}],
    ),
    "intersection-of-two-linked-lists": _p(
        "getIntersectionNode",
        difficulty="easy",
        needs_list_node=True,
        description="给定两条链表头，返回相交结点；不相交返回 null。测例用 a/b/common 表示前缀与共用后缀。",
        samples=[
            {
                "args": [{"a": [4, 1], "b": [5, 6, 1], "common": [8, 4, 5]}],
                "expected": [8, 4, 5],
            },
        ],
        hidden=[
            {"args": [{"a": [2, 6, 4], "b": [1, 5], "common": []}], "expected": None},
            {"args": [{"a": [], "b": [], "common": []}], "expected": None},
        ],
    ),
    "best-time-to-buy-and-sell-stock": _p(
        "maxProfit",
        difficulty="easy",
        samples=[{"args": [[7, 1, 5, 3, 6, 4]], "expected": 5}],
    ),
    "jump-game": _p(
        "canJump",
        difficulty="medium",
        samples=[{"args": [[2, 3, 1, 1, 4]], "expected": True}],
        hidden=[{"args": [[3, 2, 1, 0, 4]], "expected": False}],
    ),
    "permutations": _p(
        "permute",
        difficulty="medium",
        samples=[
            {
                "args": [[1, 2, 3]],
                "expected": [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]],
            }
        ],
        order_insensitive=True,
    ),
    "combinations": _p(
        "combine",
        difficulty="medium",
        samples=[
            {
                "args": [4, 2],
                "expected": [[1, 2], [1, 3], [1, 4], [2, 3], [2, 4], [3, 4]],
            }
        ],
        order_insensitive=True,
    ),
    "3sum": _p(
        "threeSum",
        difficulty="medium",
        samples=[{"args": [[-1, 0, 1, 2, -1, -4]], "expected": [[-1, -1, 2], [-1, 0, 1]]}],
        order_insensitive=True,
    ),
    "squares-of-a-sorted-array": _p(
        "sortedSquares",
        difficulty="easy",
        samples=[{"args": [[-4, -1, 0, 3, 10]], "expected": [0, 1, 9, 16, 100]}],
    ),
    "minimum-size-subarray-sum": _p(
        "minSubArrayLen",
        difficulty="medium",
        samples=[{"args": [7, [2, 3, 1, 2, 4, 3]], "expected": 2}],
    ),
    "trapping-rain-water": _p(
        "trap",
        difficulty="hard",
        samples=[{"args": [[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]], "expected": 6}],
    ),
    "ransom-note": _p(
        "canConstruct",
        difficulty="easy",
        samples=[{"args": ["aa", "aab"], "expected": True}],
        hidden=[{"args": ["a", "b"], "expected": False}],
    ),
    "intersection-of-two-arrays": _p(
        "intersection",
        difficulty="easy",
        samples=[{"args": [[1, 2, 2, 1], [2, 2]], "expected": [2]}],
        order_insensitive=True,
    ),
    "search-insert-position": _p(
        "searchInsert",
        difficulty="easy",
        samples=[{"args": [[1, 3, 5, 6], 5], "expected": 2}],
        hidden=[{"args": [[1, 3, 5, 6], 2], "expected": 1}],
    ),
    "sqrtx": _p(
        "mySqrt",
        difficulty="easy",
        samples=[{"args": [4], "expected": 2}],
        hidden=[{"args": [8], "expected": 2}],
    ),
    "evaluate-reverse-polish-notation": _p(
        "evalRPN",
        difficulty="medium",
        samples=[{"args": [["2", "1", "+", "3", "*"]], "expected": 9}],
    ),
    "top-k-frequent-elements": _p(
        "topKFrequent",
        difficulty="medium",
        samples=[{"args": [[1, 1, 1, 2, 2, 3], 2], "expected": [1, 2]}],
        order_insensitive=True,
    ),
    "path-sum": _p(
        "hasPathSum",
        difficulty="easy",
        tree_arg_indices=[0],
        samples=[
            {
                "args": [[5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, 1], 22],
                "expected": True,
            }
        ],
    ),
    "subsets": _p(
        "subsets",
        difficulty="medium",
        samples=[{"args": [[1, 2, 3]], "expected": [[], [1], [2], [1, 2], [3], [1, 3], [2, 3], [1, 2, 3]]}],
        order_insensitive=True,
    ),
    "assign-cookies": _p(
        "findContentChildren",
        difficulty="easy",
        samples=[{"args": [[1, 2, 3], [1, 1]], "expected": 1}],
    ),
    "non-overlapping-intervals": _p(
        "eraseOverlapIntervals",
        difficulty="medium",
        samples=[{"args": [[[1, 2], [2, 3], [3, 4], [1, 3]]], "expected": 1}],
    ),
    "palindrome-partitioning": _p(
        "partition",
        difficulty="medium",
        samples=[{"args": ["aab"], "expected": [["a", "a", "b"], ["aa", "b"]]}],
        order_insensitive=True,
    ),
    "remove-linked-list-elements": _p(
        "removeElements",
        difficulty="easy",
        list_arg_indices=[0],
        needs_list_node=True,
        samples=[{"args": [[1, 2, 6, 3, 4, 5, 6], 6], "expected": [1, 2, 3, 4, 5]}],
    ),
    "middle-of-the-linked-list": _p(
        "middleNode",
        difficulty="easy",
        list_arg_indices=[0],
        needs_list_node=True,
        samples=[{"args": [[1, 2, 3, 4, 5]], "expected": [3, 4, 5]}],
    ),
    "binary-tree-level-order-traversal": _p(
        "levelOrder",
        difficulty="medium",
        tree_arg_indices=[0],
        samples=[{"args": [[3, 9, 20, None, None, 15, 7]], "expected": [[3], [9, 20], [15, 7]]}],
    ),
    "same-tree": _p(
        "isSameTree",
        difficulty="easy",
        tree_arg_indices=[0, 1],
        samples=[{"args": [[1, 2, 3], [1, 2, 3]], "expected": True}],
    ),
    "validate-binary-search-tree": _p(
        "isValidBST",
        difficulty="medium",
        tree_arg_indices=[0],
        samples=[{"args": [[2, 1, 3]], "expected": True}],
        hidden=[{"args": [[5, 1, 4, None, None, 3, 6]], "expected": False}],
    ),
    "4sum-ii": _p(
        "fourSumCount",
        difficulty="medium",
        samples=[{"args": [[1, 2], [-2, -1], [-1, 2], [0, 2]], "expected": 2}],
    ),
    "spiral-matrix-ii": _p(
        "generateMatrix",
        difficulty="medium",
        samples=[{"args": [3], "expected": [[1, 2, 3], [8, 9, 4], [7, 6, 5]]}],
    ),
    "largest-rectangle-in-histogram": _p(
        "largestRectangleArea",
        difficulty="hard",
        samples=[{"args": [[2, 1, 5, 6, 2, 3]], "expected": 10}],
    ),
    "remove-all-adjacent-duplicates-in-string": _p(
        "removeDuplicates",
        difficulty="easy",
        samples=[{"args": ["abbaca"], "expected": "ca"}],
    ),
    "sliding-window-maximum": _p(
        "maxSlidingWindow",
        difficulty="hard",
        samples=[{"args": [[1, 3, -1, -3, 5, 3, 6, 7], 3], "expected": [3, 3, 5, 5, 6, 7]}],
    ),
    "fruit-into-baskets": _p(
        "totalFruit",
        difficulty="medium",
        samples=[{"args": [[1, 2, 1]], "expected": 3}],
    ),
    "gas-station": _p(
        "canCompleteCircuit",
        difficulty="medium",
        samples=[{"args": [[1, 2, 3, 4, 5], [3, 4, 5, 1, 2]], "expected": 3}],
    ),
}
