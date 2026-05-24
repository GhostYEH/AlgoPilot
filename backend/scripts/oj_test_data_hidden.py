"""为缺 hidden 测例的题目补充隐藏用例（由 build_oj_data.py 合并进 tests_bundle）。"""

from __future__ import annotations

from typing import Any

HIDDEN_SUPPLEMENT: dict[str, list[dict[str, Any]]] = {
    "3sum": [
        {"args": [[0, 0, 0]], "expected": [[0, 0, 0]]},
        {"args": [[1, 2, -2, -1]], "expected": []},
    ],
    "4sum": [
        {"args": [[2, 2, 2, 2, 2], 8], "expected": [[2, 2, 2, 2]]},
    ],
    "4sum-ii": [
        {"args": [[0], [0], [0], [0]], "expected": 1},
    ],
    "add-strings": [
        {"args": ["0", "0"], "expected": "0"},
        {"args": ["999", "1"], "expected": "1000"},
    ],
    "assign-cookies": [
        {"args": [[1, 2], [1, 2, 3]], "expected": 2},
        {"args": [[1, 1, 1], [10]], "expected": 0},
    ],
    "average-of-levels-in-binary-tree": [
        {"args": [[1]], "expected": [1.0]},
        {"args": [[1, 2, 3]], "expected": [2.0, 2.5]},
    ],
    "best-time-to-buy-and-sell-stock": [
        {"args": [[7, 6, 4, 3, 1]], "expected": 0},
        {"args": [[2, 4, 1]], "expected": 2},
    ],
    "best-time-to-buy-and-sell-stock-ii": [
        {"args": [[1, 2, 3, 4, 5]], "expected": 4},
        {"args": [[7, 6, 4, 3, 1]], "expected": 0},
    ],
    "binary-tree-inorder-traversal": [
        {"args": [[1]], "expected": [1]},
        {"args": [[2, 3, None, 1]], "expected": [3, 2, 1]},
    ],
    "binary-tree-level-order-traversal": [
        {"args": [[1, 2]], "expected": [[1], [2]]},
        {"args": [[1]], "expected": [[1]]},
    ],
    "binary-tree-level-order-traversal-ii": [
        {"args": [[1, 2]], "expected": [[2], [1]]},
        {"args": [[1]], "expected": [[1]]},
    ],
    "binary-tree-paths": [
        {"args": [[1]], "expected": ["1"]},
        {"args": [[1, 2, 3, None, 5]], "expected": ["1->2->5", "1->3"]},
    ],
    "binary-tree-postorder-traversal": [
        {"args": [[1]], "expected": [1]},
        {"args": [[1, 2, 3]], "expected": [3, 2, 1]},
    ],
    "binary-tree-preorder-traversal": [
        {"args": [[1]], "expected": [1]},
        {"args": [[1, 2, 3]], "expected": [1, 2, 3]},
    ],
    "binary-tree-right-side-view": [
        {"args": [[1, None, 3]], "expected": [1, 3]},
        {"args": [[1, 2, 3, 4]], "expected": [1, 3, 4]},
    ],
    "coin-change-ii": [
        {"args": [3, [2]], "expected": 0},
        {"args": [10, [5]], "expected": 1},
    ],
    "combinations": [
        {"args": [1, 1], "expected": [[1]]},
        {"args": [4, 3], "expected": [[1, 2, 3], [1, 2, 4], [1, 3, 4], [2, 3, 4]]},
    ],
    "construct-binary-tree-from-inorder-and-postorder-traversal": [
        {"args": [[2, 1], [2, 1]], "expected": [1, 2]},
        {"args": [[1], [1]], "expected": [1]},
    ],
    "construct-binary-tree-from-preorder-and-inorder-traversal": [
        {"args": [[1, 2], [2, 1]], "expected": [1, 2]},
        {"args": [[1], [1]], "expected": [1]},
    ],
    "convert-bst-to-greater-tree": [
        {"args": [[1, None, 2]], "expected": [3, None, 2]},
        {"args": [[0, None, 1]], "expected": [1, None, 1]},
    ],
    "convert-sorted-array-to-binary-search-tree": [
        {"args": [[1, 2, 3]], "expected": [2, 1, 3]},
        {"args": [[1]], "expected": [1]},
    ],
    "count-complete-tree-nodes": [
        {"args": [[1]], "expected": 1},
        {"args": [[1, 2, 3, 4, 5, 6, 7]], "expected": 7},
    ],
    "daily-temperatures": [
        {"args": [[30, 40, 50, 60]], "expected": [1, 1, 1, 0]},
        {"args": [[55, 38, 53, 81]], "expected": [3, 1, 1, 0]},
    ],
    "delete-node-in-a-bst": [
        {"args": [[5, 3, 6, 2, 4, None, 7], 3], "expected": [5, 4, 6, 2, None, None, 7]},
    ],
    "delete-node-in-a-linked-list": [
        {"args": [[4, 5, 1, 9], 1], "expected": [4, 5, 9]},
        {"args": [[1, 2, 3, 4], 3], "expected": [1, 2, 4]},
    ],
    "evaluate-reverse-polish-notation": [
        {"args": [["4"]], "expected": 4},
        {"args": [["18"]], "expected": 18},
    ],
    "find-bottom-left-tree-value": [
        {"args": [[1, 2, 3, 4, None, 5, 6, None, None, None, 7]], "expected": 7},
        {"args": [[1]], "expected": 1},
    ],
    "find-mode-in-binary-search-tree": [
        {"args": [[1, None, 2, 2]], "expected": [2]},
        {"args": [[1, 1, 2, 2, 2]], "expected": [2]},
    ],
    "fruit-into-baskets": [
        {"args": [[1, 2, 3, 2, 2]], "expected": 3},
        {"args": [[3, 3, 3, 1, 2, 1, 1, 2, 3, 3, 2]], "expected": 5},
    ],
    "gas-station": [
        {"args": [[2, 3, 4], [3, 4, 5]], "expected": -1},
        {"args": [[5, 1, 2, 3, 4], [4, 4, 1, 5, 1]], "expected": 4},
    ],
    "group-anagrams": [
        {"args": [["a"]], "expected": [["a"]]},
        {"args": [["abc", "bca", "cab"]], "expected": [["abc", "bca", "cab"]]},
    ],
    "insert-into-a-binary-search-tree": [
        {"args": [[4, 2, 7, 1, 3], 10], "expected": [4, 2, 7, 1, 3, None, 10]},
        {"args": [[5, 3, 6, 2, 4, None, 7], 8], "expected": [5, 3, 6, 2, 4, None, 7, None, None, None, None, None, 8]},
    ],
    "intersection-of-two-arrays": [
        {"args": [[1, 2, 2, 1], [2, 2]], "expected": [2]},
    ],
    "intersection-of-two-arrays-ii": [
        {"args": [[1, 2, 2, 1], [2, 2]], "expected": [2, 2]},
    ],
    "invert-binary-tree": [
        {"args": [[1, 2, 3, 4, 5]], "expected": [1, 3, 2, 5, 4]},
        {"args": [[1]], "expected": [1]},
    ],
    "jump-game-ii": [
        {"args": [[2, 1]], "expected": 1},
        {"args": [[1, 1, 1, 1]], "expected": 3},
    ],
    "largest-rectangle-in-histogram": [
        {"args": [[1, 1]], "expected": 2},
        {"args": [[2, 4]], "expected": 4},
    ],
    "linked-list-cycle": [
        {"args": [[1]], "expected": False},
        {"args": [[1, 2]], "expected": False},
    ],
    "longest-increasing-subsequence": [
        {"args": [[10, 9, 2, 5, 3, 7, 101, 18]], "expected": 4},
        {"args": [[0, 1, 0, 3, 2, 3]], "expected": 4},
    ],
    "lowest-common-ancestor-of-a-binary-search-tree": [
        {"args": [[6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 2, 8], "expected": 6},
        {"args": [[2, 1], 2, 1], "expected": 2},
    ],
    "lowest-common-ancestor-of-a-binary-tree": [
        {"args": [[3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 5, 1], "expected": 3},
        {"args": [[1, 2, 3, 4, 5], 4, 5], "expected": 4},
    ],
    "maximum-binary-tree": [
        {"args": [[1]], "expected": [1]},
        {"args": [[3, 2, 1, 6, 0, 5]], "expected": [6, 3, 5, None, 2, 0, None, None, None, 1]},
    ],
    "maximum-depth-of-binary-tree": [
        {"args": [[1, None, 2]], "expected": 2},
        {"args": [[1]], "expected": 1},
    ],
    "merge-two-binary-trees": [
        {"args": [[1], [2]], "expected": [3]},
        {"args": [[1, 2], [3, 4]], "expected": [4, 4, 2]},
    ],
    "middle-of-the-linked-list": [
        {"args": [[1, 2, 3, 4, 5, 6]], "expected": [4, 5, 6]},
        {"args": [[1]], "expected": [1]},
    ],
    "minimum-absolute-difference-in-bst": [
        {"args": [[1, 0, 48, None, None, 12, 49]], "expected": 1},
        {"args": [[1, None, 3]], "expected": 2},
    ],
    "minimum-depth-of-binary-tree": [
        {"args": [[1, 2]], "expected": 2},
        {"args": [[1, None, 2, 3]], "expected": 2},
    ],
    "minimum-number-of-arrows-to-burst-balloons": [
        {"args": [[[1, 2], [3, 4], [5, 6], [7, 8]]], "expected": 4},
        {"args": [[[10, 16], [2, 8], [1, 6], [7, 12]]], "expected": 2},
    ],
    "minimum-size-subarray-sum": [
        {"args": [4, [1, 4, 4]], "expected": 1},
        {"args": [11, [1, 1, 1, 1, 1, 1, 1, 1]], "expected": 0},
    ],
    "minimum-window-substring": [
        {"args": ["a", "a"], "expected": "a"},
        {"args": ["a", "aa"], "expected": ""},
    ],
    "move-zeroes": [
        {"args": [[1]], "expected": [1], "in_place_arg": 0},
        {"args": [[0, 0, 1]], "expected": [1, 0, 0], "in_place_arg": 0},
    ],
    "n-queens": [
        {"args": [1], "expected": [["Q"]]},
        {"args": [2], "expected": []},
    ],
    "next-greater-element-i": [
        {"args": [[2, 4], [1, 2, 3, 4]], "expected": [3, -1]},
        {"args": [[1, 3, 5, 2], [1, 3, 5, 2]], "expected": [3, 5, -1, -1]},
    ],
    "next-greater-element-ii": [
        {"args": [[3, 8, 4, 1, 2]], "expected": [8, -1, 8, 3, 4]},
        {"args": [[1, 2, 3]], "expected": [2, 3, -1]},
    ],
    "non-overlapping-intervals": [
        {"args": [[[1, 2], [1, 2], [1, 2]]], "expected": 2},
        {"args": [[[1, 2], [2, 3]]], "expected": 0},
    ],
    "palindrome-partitioning": [
        {"args": ["a"], "expected": [["a"]]},
        {"args": ["aaa"], "expected": [["a", "a", "a"], ["a", "aa"], ["aaa"]]},
    ],
    "path-sum": [
        {"args": [[1, 2, 3], 3], "expected": True},
        {"args": [[1, 2], 1], "expected": False},
    ],
    "path-sum-ii": [
        {"args": [[1, 2, 5], 8], "expected": [[1, 2, 5]]},
        {"args": [[1, 2, 3, 4, 5], 10], "expected": []},
    ],
    "permutations": [
        {"args": [[1]], "expected": [[1]]},
        {"args": [[0, 1]], "expected": [[0, 1], [1, 0]]},
    ],
    "permutations-ii": [
        {"args": [[1, 2, 3]], "expected": [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]},
        {"args": [[1]], "expected": [[1]]},
    ],
    "remove-all-adjacent-duplicates-in-string": [
        {"args": ["azxxzy"], "expected": "ay"},
        {"args": ["aababaab"], "expected": "ba"},
    ],
    "remove-linked-list-elements": [
        {"args": [[1, 2, 3, 4], 1], "expected": [2, 3, 4]},
        {"args": [[7, 7, 7, 7], 7], "expected": []},
    ],
    "remove-nth-node-from-end-of-list": [
        {"args": [[1], 1], "expected": []},
        {"args": [[1, 2], 1], "expected": [1]},
    ],
    "replace-space-lcof": [
        {"args": ["  hello world  "], "expected": "%20%20hello%20world%20%20"},
    ],
    "reverse-linked-list": [
        {"args": [[1, 2]], "expected": [2, 1]},
        {"args": [[1]], "expected": [1]},
    ],
    "reverse-linked-list-ii": [
        {"args": [[1, 2, 3, 4, 5], 1, 1], "expected": [1, 2, 3, 4, 5]},
        {"args": [[5], 1, 1], "expected": [5]},
    ],
    "reverse-nodes-in-k-group": [
        {"args": [[1, 2, 3, 4, 5], 1], "expected": [1, 2, 3, 4, 5]},
        {"args": [[1, 2, 3, 4], 2], "expected": [2, 1, 4, 3]},
    ],
    "reverse-string": [
        {"args": [["H", "a", "n", "n", "a", "h"]], "expected": ["h", "a", "n", "n", "a", "H"], "in_place_arg": 0},
        {"args": [["A", " ", "m", "a", "n"]], "expected": ["n", "a", "m", " ", "A"], "in_place_arg": 0},
    ],
    "reverse-string-ii": [
        {"args": ["abcd", 2], "expected": "bacd"},
        {"args": ["abcdefg", 8], "expected": "gfedcba"},
    ],
    "reverse-vowels-of-a-string": [
        {"args": ["leetcode"], "expected": "leotcede"},
        {"args": ["a"], "expected": "a"},
    ],
    "reverse-words-in-a-string": [
        {"args": ["  hello world  "], "expected": "world hello"},
        {"args": ["a good   example"], "expected": "example good a"},
    ],
    "reverse-words-in-a-string-ii": [
        {"args": ["  hello world  "], "expected": "world hello"},
        {"args": ["a"], "expected": "a"},
    ],
    "rotate-array": [
        {"args": [[1, 2, 3, 4, 5, 6, 7], 0], "expected": [1, 2, 3, 4, 5, 6, 7], "in_place_arg": 0},
        {"args": [[-1, -100, 3, 99], 2], "expected": [3, 99, -1, -100], "in_place_arg": 0},
    ],
    "same-tree": [
        {"args": [[1], [1]], "expected": True},
        {"args": [[1, 2], [1, None, 2]], "expected": False},
    ],
    "search-in-a-binary-search-tree": [
        {"args": [[4, 2, 7, 1, 3], 5], "expected": []},
        {"args": [[4, 2, 7, 1, 3], 1], "expected": [1]},
    ],
    "shortest-palindrome": [
        {"args": ["a"], "expected": "a"},
        {"args": ["ab"], "expected": "bab"},
    ],
    "sliding-window-maximum": [
        {"args": [[1], 1], "expected": [1]},
        {"args": [[9, 10, 9, 7, 4, 8, 6, 0, 1, 5], 4], "expected": [10, 10, 9, 8, 8, 8, 8, 5]},
    ],
    "spiral-matrix": [
        {"args": [[[1, 2, 3, 4]]], "expected": [1, 2, 3, 4]},
        {"args": [[[1], [2], [3]]], "expected": [1, 2, 3]},
    ],
    "spiral-matrix-ii": [
        {"args": [1], "expected": [[1]]},
        {"args": [2], "expected": [[1, 2], [4, 3]]},
    ],
    "squares-of-a-sorted-array": [
        {"args": [[-7, -3, 2, 3, 11]], "expected": [4, 9, 9, 49, 121]},
        {"args": [[-5, -3, -2, -1]], "expected": [1, 4, 9, 25]},
    ],
    "subsets": [
        {"args": [[1]], "expected": [[], [1]]},
        {"args": [[0]], "expected": [[], [0]]},
    ],
    "subtree-of-another-tree": [
        {"args": [[1], [2]], "expected": False},
        {"args": [[1, 2, 3], [2, 3]], "expected": True},
    ],
    "sudoku-solver": [
        {
            "args": [
                [
                    [8, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 3, 0, 2, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0],
                ]
            ],
            "expected": [
                [8, 1, 2, 3, 4, 5, 6, 7, 9],
                [4, 6, 3, 7, 2, 9, 1, 5, 8],
                [5, 7, 9, 1, 6, 8, 2, 3, 4],
                [1, 2, 4, 5, 3, 6, 8, 9, 7],
                [3, 5, 6, 8, 9, 7, 4, 1, 2],
                [7, 9, 8, 2, 1, 4, 3, 6, 5],
                [2, 3, 5, 4, 7, 1, 9, 8, 6],
                [6, 4, 7, 9, 8, 3, 5, 2, 1],
                [9, 8, 1, 6, 5, 2, 7, 4, 3],
            ],
            "in_place_arg": 0,
        },
    ],
    "sum-of-left-leaves": [
        {"args": [[1, None, 2, 3, 4]], "expected": 3},
        {"args": [[1, 2, 3, 4, 5]], "expected": 4},
    ],
    "swap-nodes-in-pairs": [
        {"args": [[1]], "expected": [1]},
        {"args": [[1, 2, 3]], "expected": [2, 1, 3]},
    ],
    "top-k-frequent-elements": [
        {"args": [[1], 1], "expected": [1]},
        {"args": [[1, 1, 1, 2, 2, 3], 1], "expected": [1]},
    ],
    "trapping-rain-water": [
        {"args": [[4, 2, 3]], "expected": 1},
        {"args": [[1, 0, 2, 1, 3, 2, 1, 2, 1]], "expected": 2},
    ],
    "trim-a-binary-search-tree": [
        {"args": [[3, 1, 4, None, 2], 2, 3], "expected": [3, 2]},
        {"args": [[1], 1, 2], "expected": [1]},
    ],
    "two-sum-ii-input-array-is-sorted": [
        {"args": [[2, 3, 4], 6], "expected": [1, 3]},
        {"args": [[1, 2], 3], "expected": [1, 2]},
    ],
}
