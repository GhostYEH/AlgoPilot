"""补充课程中尚未配置测例的 OJ 题目（由 build_oj_data.py 合并进 tests_bundle）。"""

from __future__ import annotations

from typing import Any

from oj_test_data import _p, _stdio

EXTRA_TEST_DEFINITIONS: dict[str, dict[str, Any]] = {
  "4sum": _p(
    "fourSum",
    difficulty="medium",
    samples=[{"args": [[1, 0, -1, 0, -2, 2], 0], "expected": [[-2, -1, 1, 2], [-2, 0, 0, 2], [-1, 0, 0, 1]]}],
    order_insensitive=True,
  ),
  "remove-nth-node-from-end-of-list": _p(
    "removeNthFromEnd",
    difficulty="medium",
    list_arg_indices=[0],
    needs_list_node=True,
    samples=[{"args": [[1, 2, 3, 4, 5], 2], "expected": [1, 2, 3, 5]}],
  ),
  "swap-nodes-in-pairs": _p(
    "swapPairs",
    difficulty="medium",
    list_arg_indices=[0],
    needs_list_node=True,
    samples=[{"args": [[1, 2, 3, 4]], "expected": [2, 1, 4, 3]}],
  ),
  "reverse-nodes-in-k-group": _p(
    "reverseKGroup",
    difficulty="hard",
    list_arg_indices=[0],
    needs_list_node=True,
    samples=[{"args": [[1, 2, 3, 4, 5], 2], "expected": [2, 1, 4, 3, 5]}],
  ),
  "find-first-and-last-position-of-element-in-sorted-array": _p(
    "searchRange",
    difficulty="medium",
    samples=[{"args": [[5, 7, 7, 8, 8, 10], 8], "expected": [3, 4]}],
    hidden=[{"args": [[5, 7, 7, 8, 8, 10], 6], "expected": [-1, -1]}],
  ),
  "sudoku-solver": _p(
    "solveSudoku",
    difficulty="hard",
    description="9×9 数独：输入 9 行，每行 9 个数字（0 表示空格）；输出填好后的 9 行。",
    samples=[
      {
        "args": [
          [
            [5, 3, 0, 0, 7, 0, 0, 0, 0],
            [6, 0, 0, 1, 9, 5, 0, 0, 0],
            [0, 9, 8, 0, 0, 0, 0, 6, 0],
            [8, 0, 0, 0, 6, 0, 0, 0, 3],
            [4, 0, 0, 8, 0, 3, 0, 0, 1],
            [7, 0, 0, 0, 2, 0, 0, 0, 6],
            [0, 6, 0, 0, 0, 0, 2, 8, 0],
            [0, 0, 0, 4, 1, 9, 0, 0, 5],
            [0, 0, 0, 0, 8, 0, 0, 7, 9],
          ]
        ],
        "expected": [
          [5, 3, 4, 6, 7, 8, 9, 1, 2],
          [6, 7, 2, 1, 9, 5, 3, 4, 8],
          [1, 9, 8, 3, 4, 2, 5, 6, 7],
          [8, 5, 9, 7, 6, 1, 4, 2, 3],
          [4, 2, 6, 8, 5, 3, 7, 9, 1],
          [7, 1, 3, 9, 2, 4, 8, 5, 6],
          [9, 6, 1, 5, 3, 7, 2, 8, 4],
          [2, 8, 7, 4, 1, 9, 6, 3, 5],
          [3, 4, 5, 2, 8, 6, 1, 7, 9],
        ],
        "in_place_arg": 0,
      }
    ],
  ),
  "jump-game-ii": _p(
    "jump",
    difficulty="medium",
    samples=[{"args": [[2, 3, 1, 1, 4]], "expected": 2}],
  ),
  "permutations-ii": _p(
    "permute",
    difficulty="medium",
    samples=[{"args": [[1, 1, 2]], "expected": [[1, 1, 2], [1, 2, 1], [2, 1, 1]]}],
    order_insensitive=True,
  ),
  "group-anagrams": _p(
    "groupAnagrams",
    difficulty="medium",
    samples=[
      {
        "args": [["eat", "tea", "tan", "ate", "nat", "bat"]],
        "expected": [["bat"], ["nat", "tan"], ["ate", "eat", "tea"]],
      }
    ],
    order_insensitive=True,
  ),
  "n-queens": _p(
    "solveNQueens",
    difficulty="hard",
    samples=[{"args": [4], "expected": [
      [".Q..", "...Q", "Q...", "..Q."],
      ["..Q.", "Q...", "...Q", ".Q.."],
    ]}],
    order_insensitive=True,
  ),
  "spiral-matrix": _p(
    "spiralOrder",
    difficulty="medium",
    samples=[{"args": [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]], "expected": [1, 2, 3, 6, 9, 8, 7, 4, 5]}],
  ),
  "length-of-last-word": _p(
    "lengthOfLastWord",
    difficulty="easy",
    samples=[{"args": ["   fly me   to   the moon  "], "expected": 4}],
    hidden=[{"args": ["luffy is still joyboy"], "expected": 6}],
  ),
  "minimum-window-substring": _p(
    "minWindow",
    difficulty="hard",
    samples=[{"args": ["ADOBECODEBANC", "ABC"], "expected": "BANC"}],
  ),
  "reverse-linked-list-ii": _p(
    "reverseBetween",
    difficulty="medium",
    list_arg_indices=[0],
    needs_list_node=True,
    samples=[{"args": [[1, 2, 3, 4, 5], 2, 4], "expected": [1, 4, 3, 2, 5]}],
  ),
  "binary-tree-inorder-traversal": _p(
    "inorderTraversal",
    difficulty="easy",
    tree_arg_indices=[0],
    samples=[{"args": [[1, None, 2, 3]], "expected": [1, 3, 2]}],
  ),
  "construct-binary-tree-from-preorder-and-inorder-traversal": _p(
    "buildTree",
    difficulty="medium",
    tree_arg_indices=[0],
    samples=[{"args": [[3, 9, 20, 15, 7], [9, 3, 15, 20, 7]], "expected": [3, 9, 20, None, None, 15, 7]}],
  ),
  "construct-binary-tree-from-inorder-and-postorder-traversal": _p(
    "buildTree",
    difficulty="medium",
    tree_arg_indices=[0],
    samples=[{"args": [[9, 3, 15, 20, 7], [9, 15, 7, 20, 3]], "expected": [3, 9, 20, None, None, 15, 7]}],
  ),
  "binary-tree-level-order-traversal-ii": _p(
    "levelOrderBottom",
    difficulty="medium",
    tree_arg_indices=[0],
    samples=[{"args": [[3, 9, 20, None, None, 15, 7]], "expected": [[15, 7], [9, 20], [3]]}],
  ),
  "convert-sorted-array-to-binary-search-tree": _p(
    "sortedArrayToBST",
    difficulty="easy",
    tree_arg_indices=[0],
    samples=[{"args": [[-10, -3, 0, 5, 9]], "expected": [0, -3, 9, -10, None, 5]}],
  ),
  "balanced-binary-tree": _p(
    "isBalanced",
    difficulty="easy",
    tree_arg_indices=[0],
    samples=[{"args": [[3, 9, 20, None, None, 15, 7]], "expected": True}],
    hidden=[{"args": [[1, 2, 2, 3, 3, None, None, 4, 4]], "expected": False}],
  ),
  "minimum-depth-of-binary-tree": _p(
    "minDepth",
    difficulty="easy",
    tree_arg_indices=[0],
    samples=[{"args": [[3, 9, 20, None, None, 15, 7]], "expected": 2}],
  ),
  "path-sum-ii": _p(
    "pathSum",
    difficulty="medium",
    tree_arg_indices=[0],
    samples=[{"args": [[5, 4, 8, 11, None, 13, 4, 7, 2, None, None, 5, 1], 22], "expected": [[5, 4, 11], [5, 8, 4, 5]]}],
    order_insensitive=True,
  ),
  "best-time-to-buy-and-sell-stock-ii": _p(
    "maxProfit",
    difficulty="medium",
    samples=[{"args": [[7, 1, 5, 3, 6, 4]], "expected": 7}],
  ),
  "binary-tree-preorder-traversal": _p(
    "preorderTraversal",
    difficulty="easy",
    tree_arg_indices=[0],
    samples=[{"args": [[1, None, 2, 3]], "expected": [1, 2, 3]}],
  ),
  "binary-tree-postorder-traversal": _p(
    "postorderTraversal",
    difficulty="easy",
    tree_arg_indices=[0],
    samples=[{"args": [[1, None, 2, 3]], "expected": [3, 2, 1]}],
  ),
  "reverse-words-in-a-string": _p(
    "reverseWords",
    difficulty="medium",
    samples=[{"args": ["the sky is blue"], "expected": "blue is sky the"}],
  ),
  "two-sum-ii-input-array-is-sorted": _p(
    "twoSum",
    difficulty="medium",
    samples=[{"args": [[2, 7, 11, 15], 9], "expected": [1, 2]}],
  ),
  "reverse-words-in-a-string-ii": _p(
    "reverseWords",
    difficulty="medium",
    samples=[{"args": ["the sky is blue"], "expected": "blue is sky the"}],
  ),
  "rotate-array": _p(
    "rotate",
    difficulty="medium",
    samples=[{"args": [[1, 2, 3, 4, 5, 6, 7], 3], "expected": [5, 6, 7, 1, 2, 3, 4], "in_place_arg": 0}],
  ),
  "binary-tree-right-side-view": _p(
    "rightSideView",
    difficulty="medium",
    tree_arg_indices=[0],
    samples=[{"args": [[1, 2, 3, None, 5, None, 4]], "expected": [1, 3, 4]}],
  ),
  "shortest-palindrome": _p(
    "shortestPalindrome",
    difficulty="hard",
    samples=[{"args": ["aacecaaa"], "expected": "aaacecaaa"}],
  ),
  "count-complete-tree-nodes": _p(
    "countNodes",
    difficulty="medium",
    tree_arg_indices=[0],
    samples=[{"args": [[1, 2, 3, 4, 5, 6]], "expected": 6}],
  ),
  "palindrome-linked-list": _p(
    "isPalindrome",
    difficulty="easy",
    list_arg_indices=[0],
    needs_list_node=True,
    samples=[{"args": [[1, 2, 2, 1]], "expected": True}],
    hidden=[{"args": [[1, 2]], "expected": False}],
  ),
  "lowest-common-ancestor-of-a-binary-search-tree": _p(
    "lowestCommonAncestor",
    difficulty="medium",
    tree_arg_indices=[0],
    samples=[{"args": [[6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 2, 8], "expected": 6}],
  ),
  "lowest-common-ancestor-of-a-binary-tree": _p(
    "lowestCommonAncestor",
    difficulty="medium",
    tree_arg_indices=[0],
    samples=[{"args": [[3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 5, 1], "expected": 3}],
  ),
  "delete-node-in-a-linked-list": _p(
    "deleteNode",
    difficulty="medium",
    list_arg_indices=[0],
    needs_list_node=True,
    description="删除给定结点（不含头结点）；输出删除后的链表序列。",
    samples=[{"args": [[4, 5, 1, 9], 5], "expected": [4, 1, 9]}],
  ),
  "binary-tree-paths": _p(
    "binaryTreePaths",
    difficulty="easy",
    tree_arg_indices=[0],
    samples=[{"args": [[1, 2, 3, None, 5]], "expected": ["1->2->5", "1->3"]}],
    order_insensitive=True,
  ),
  "reverse-vowels-of-a-string": _p(
    "reverseVowels",
    difficulty="easy",
    samples=[{"args": ["hello"], "expected": "holle"}],
  ),
  "intersection-of-two-arrays-ii": _p(
    "intersect",
    difficulty="easy",
    samples=[{"args": [[1, 2, 2, 1], [2, 2]], "expected": [2, 2]}],
    order_insensitive=True,
  ),
  "valid-perfect-square": _p(
    "isPerfectSquare",
    difficulty="easy",
    samples=[{"args": [16], "expected": True}],
    hidden=[{"args": [14], "expected": False}],
  ),
  "sum-of-left-leaves": _p(
    "sumOfLeftLeaves",
    difficulty="easy",
    tree_arg_indices=[0],
    samples=[{"args": [[3, 9, 20, None, None, 15, 7]], "expected": 24}],
  ),
  "add-strings": _p(
    "addStrings",
    difficulty="easy",
    samples=[{"args": ["11", "123"], "expected": "134"}],
  ),
  "partition-equal-subset-sum": _p(
    "canPartition",
    difficulty="medium",
    samples=[{"args": [[1, 5, 11, 5]], "expected": True}],
    hidden=[{"args": [[1, 2, 3, 5]], "expected": False}],
  ),
  "delete-node-in-a-bst": _p(
    "deleteNode",
    difficulty="medium",
    tree_arg_indices=[0],
    samples=[{"args": [[5, 3, 6, 2, 4, None, 7], 3], "expected": [5, 4, 6, 2, None, None, 7]}],
  ),
  "minimum-number-of-arrows-to-burst-balloons": _p(
    "findMinArrowShots",
    difficulty="medium",
    samples=[{"args": [[[10, 16], [2, 8], [1, 6], [7, 12]]], "expected": 2}],
  ),
  "repeated-substring-pattern": _p(
    "repeatedSubstringPattern",
    difficulty="easy",
    samples=[{"args": ["abab"], "expected": True}],
    hidden=[{"args": ["aba"], "expected": False}],
  ),
  "find-mode-in-binary-search-tree": _p(
    "findMode",
    difficulty="easy",
    tree_arg_indices=[0],
    samples=[{"args": [[1, None, 2, 2]], "expected": [2]}],
    order_insensitive=True,
  ),
  "next-greater-element-ii": _p(
    "nextGreaterElements",
    difficulty="medium",
    samples=[{"args": [[1, 2, 1]], "expected": [2, -1, 2]}],
  ),
  "find-bottom-left-tree-value": _p(
    "findBottomLeftValue",
    difficulty="medium",
    tree_arg_indices=[0],
    samples=[{"args": [[2, 1, 3]], "expected": 1}],
  ),
  "coin-change-ii": _p(
    "change",
    difficulty="medium",
    samples=[{"args": [5, [1, 2, 5]], "expected": 4}],
  ),
  "minimum-absolute-difference-in-bst": _p(
    "getMinimumDifference",
    difficulty="easy",
    tree_arg_indices=[0],
    samples=[{"args": [[4, 2, 6, 1, 3]], "expected": 1}],
  ),
  "convert-bst-to-greater-tree": _p(
    "convertBST",
    difficulty="medium",
    tree_arg_indices=[0],
    samples=[{"args": [[4, 1, 6, 0, 2, 5, 7, None, None, None, 3]], "expected": [7, 7, 6, 6, 2, 5, 7, None, None, None, 3]}],
  ),
  "reverse-string-ii": _p(
    "reverseStr",
    difficulty="easy",
    samples=[{"args": ["abcdefg", 2], "expected": "bacdfeg"}],
  ),
  "subtree-of-another-tree": _p(
    "isSubtree",
    difficulty="easy",
    tree_arg_indices=[0, 1],
    samples=[{"args": [[3, 4, 5, 1, 2], [4, 1, 2]], "expected": True}],
  ),
  "merge-two-binary-trees": _p(
    "mergeTrees",
    difficulty="easy",
    tree_arg_indices=[0, 1],
    samples=[{"args": [[1, 3, 2, 5], [2, 1, 3, None, 4, None, 7]], "expected": [3, 4, 5, 5, 4, None, 7]}],
  ),
  "average-of-levels-in-binary-tree": _p(
    "averageOfLevels",
    difficulty="easy",
    tree_arg_indices=[0],
    samples=[{"args": [[3, 9, 20, None, None, 15, 7]], "expected": [3.0, 14.5, 11.0]}],
  ),
  "maximum-binary-tree": _p(
    "constructMaximumBinaryTree",
    difficulty="medium",
    tree_arg_indices=[0],
    samples=[{"args": [[3, 2, 1, 6, 0, 5]], "expected": [6, 3, 5, None, 2, 0, None, None, 1]}],
  ),
  "trim-a-binary-search-tree": _p(
    "trimBST",
    difficulty="medium",
    tree_arg_indices=[0],
    samples=[{"args": [[1, 0, 2], 1, 2], "expected": [1, None, 2]}],
  ),
  "search-in-a-binary-search-tree": _p(
    "searchBST",
    difficulty="easy",
    tree_arg_indices=[0],
    samples=[{"args": [[4, 2, 7, 1, 3], 2], "expected": [2, 1, 3]}],
  ),
  "insert-into-a-binary-search-tree": _p(
    "insertIntoBST",
    difficulty="medium",
    tree_arg_indices=[0],
    samples=[{"args": [[4, 2, 7, 1, 3], 5], "expected": [4, 2, 7, 1, 3, 5]}],
  ),
  "design-linked-list": _stdio(
    difficulty="medium",
    description=(
      "## 设计链表（707）\n\n"
      "从标准输入读操作序列，输出每次有返回值的操作结果。\n\n"
      "**输入**：`n` 后 `n` 行：`init`、`addAtHead val`、`addAtTail val`、`addAtIndex index val`、"
      "`get index`、`deleteAtIndex index`。\n\n"
      "**输出**：`get` 输出整数；非法下标输出 -1。"
    ),
    samples=[
      {
        "stdin": "5\naddAtHead 1\naddAtTail 3\naddAtIndex 1 2\nget 1\ndeleteAtIndex 1\n",
        "stdout": "2\n",
      }
    ],
    hidden=[
      {
        "stdin": "4\naddAtHead 1\naddAtHead 2\nget 0\ndeleteAtIndex 0\n",
        "stdout": "2\n",
      }
    ],
  ),
  "course-schedule": _stdio(
    difficulty="medium",
    tags=["graph", "topological-sort", "indegree"],
    description=(
      "## 课程表\n\n"
      "给定课程数 `n` 和 `m` 条先修关系，每条关系 `a b` 表示学习课程 `a` 前必须先学习课程 `b`。"
      "请判断是否可以完成所有课程。\n\n"
      "**输入**：第一行 `n m`，随后 `m` 行每行两个整数 `a b`。\n\n"
      "**输出**：可以完成输出 `true`，否则输出 `false`。"
    ),
    samples=[
      {"stdin": "2 1\n1 0\n", "stdout": "true\n"},
    ],
    hidden=[
      {"stdin": "2 2\n1 0\n0 1\n", "stdout": "false\n"},
      {"stdin": "1 0\n", "stdout": "true\n"},
      {"stdin": "3 2\n1 0\n2 1\n", "stdout": "true\n"},
      {"stdin": "3 3\n1 0\n2 1\n0 2\n", "stdout": "false\n"},
      {"stdin": "4 2\n1 0\n3 2\n", "stdout": "true\n"},
      {"stdin": "4 1\n2 2\n", "stdout": "false\n"},
      {"stdin": "4 4\n1 0\n2 0\n3 1\n3 2\n", "stdout": "true\n"},
      {"stdin": "5 4\n1 0\n2 1\n3 2\n1 3\n", "stdout": "false\n"},
      {"stdin": "6 6\n1 0\n2 0\n3 1\n3 2\n4 3\n5 4\n", "stdout": "true\n"},
    ],
  ),
  "number-of-islands": _stdio(
    difficulty="medium",
    tags=["graph", "bfs", "dfs", "grid"],
    description=(
      "## 岛屿数量\n\n"
      "给定由 `0` 和 `1` 组成的网格，`1` 表示陆地。上下左右相邻的陆地属于同一座岛屿，"
      "请输出岛屿数量。\n\n"
      "**输入**：第一行 `rows cols`，随后 `rows` 行为长度为 `cols` 的 01 字符串。\n\n"
      "**输出**：一个整数，表示岛屿数量。"
    ),
    samples=[
      {"stdin": "4 5\n11110\n11010\n11000\n00000\n", "stdout": "1\n"},
    ],
    hidden=[
      {"stdin": "1 1\n1\n", "stdout": "1\n"},
      {"stdin": "1 1\n0\n", "stdout": "0\n"},
      {"stdin": "4 5\n11000\n11000\n00100\n00011\n", "stdout": "3\n"},
      {"stdin": "3 3\n100\n010\n001\n", "stdout": "3\n"},
      {"stdin": "2 4\n1111\n1111\n", "stdout": "1\n"},
      {"stdin": "3 3\n111\n101\n111\n", "stdout": "1\n"},
      {"stdin": "2 3\n101\n010\n", "stdout": "3\n"},
      {"stdin": "4 4\n1100\n0100\n0011\n0011\n", "stdout": "2\n"},
      {"stdin": "1 5\n10101\n", "stdout": "3\n"},
    ],
  ),
  "rotting-oranges": _stdio(
    difficulty="medium",
    tags=["graph", "bfs", "multi-source-bfs", "grid"],
    description=(
      "## 腐烂的橘子\n\n"
      "网格中 `0` 表示空格，`1` 表示新鲜橘子，`2` 表示腐烂橘子。每分钟腐烂橘子会使"
      "上下左右相邻的新鲜橘子腐烂。输出所有橘子腐烂所需的最少分钟数；无法全部腐烂输出 `-1`。\n\n"
      "**输入**：第一行 `rows cols`，随后 `rows` 行每行 `cols` 个整数。\n\n"
      "**输出**：最少分钟数或 `-1`。"
    ),
    samples=[
      {"stdin": "3 3\n2 1 1\n1 1 0\n0 1 1\n", "stdout": "4\n"},
    ],
    hidden=[
      {"stdin": "3 3\n2 1 1\n0 1 1\n1 0 1\n", "stdout": "-1\n"},
      {"stdin": "1 2\n0 2\n", "stdout": "0\n"},
      {"stdin": "1 1\n1\n", "stdout": "-1\n"},
      {"stdin": "1 1\n2\n", "stdout": "0\n"},
      {"stdin": "1 2\n2 1\n", "stdout": "1\n"},
      {"stdin": "3 3\n2 1 2\n1 1 1\n2 1 2\n", "stdout": "2\n"},
      {"stdin": "2 3\n0 0 0\n0 0 0\n", "stdout": "0\n"},
      {"stdin": "2 2\n2 0\n0 1\n", "stdout": "-1\n"},
      {"stdin": "3 4\n2 1 1 0\n1 1 0 1\n0 1 1 2\n", "stdout": "2\n"},
    ],
  ),
  "rotate-string": _p(
    "rotateString",
    difficulty="easy",
    samples=[{"args": ["abcde", "cdeab"], "expected": True}],
    hidden=[{"args": ["abcde", "abced"], "expected": False}],
  ),
  "longest-happy-prefix": _p(
    "longestPrefix",
    difficulty="hard",
    samples=[{"args": ["level"], "expected": "l"}],
    hidden=[{"args": ["ababab"], "expected": "abab"}],
  ),
}
