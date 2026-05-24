"""公开样例升级：替换过于简单的 samples（由 build_oj_data.py 覆盖写入 tests_bundle）。"""

from __future__ import annotations

from typing import Any

SAMPLE_OVERRIDES: dict[str, list[dict[str, Any]]] = {
    # --- TEST_DEFINITIONS ---
    "two-sum": [
        {"args": [[1, 5, 3, 7, 9], 12], "expected": [1, 4]},
    ],
    "valid-anagram": [
        {"args": ["listen", "silent"], "expected": True},
    ],
    "happy-number": [
        {"args": [967], "expected": True},
    ],
    "binary-search": [
        {"args": [[1, 3, 5, 7, 9, 11, 13, 15, 17, 19], 12], "expected": 5},
    ],
    "remove-element": [
        {"args": [[0, 1, 2, 2, 3, 0, 4, 2], 2], "expected": 5},
    ],
    "remove-duplicates-from-sorted-array": [
        {"args": [[0, 0, 1, 1, 1, 2, 2, 3, 3, 4]], "expected": 5},
    ],
    "move-zeroes": [
        {
            "args": [[0, 0, 1, 2, 3, 0, 4, 5, 0]],
            "expected": [1, 2, 3, 4, 5, 0, 0, 0, 0],
            "in_place_arg": 0,
        },
    ],
    "reverse-string": [
        {
            "args": [["p", "r", "o", "g", "r", "a", "m", "m", "i", "n", "g"]],
            "expected": ["g", "n", "i", "m", "m", "a", "r", "g", "o", "r", "p"],
            "in_place_arg": 0,
        },
    ],
    "ti-huan-kong-ge-lcof": [
        {"args": ["The moon is beautiful."], "expected": "The%20moon%20is%20beautiful."},
    ],
    "replace-space-lcof": [
        {"args": ["The moon is beautiful."], "expected": "The%20moon%20is%20beautiful."},
    ],
    "backspace-string-compare": [
        {"args": ["bxj#tw", "a#b#c#d#"], "expected": True},
    ],
    "fibonacci-number": [
        {"args": [10], "expected": 55},
    ],
    "coin-change": [
        {"args": [[2, 5, 10, 1], 27], "expected": 4},
    ],
    "implement-queue-using-stacks": [
        {
            "stdin": "8\npush 1\npush 2\npush 3\npop\npeek\npush 4\npop\nempty\n",
            "stdout": "1\n2\n4\nfalse\n",
        },
    ],
    "implement-stack-using-queues": [
        {
            "stdin": "7\npush 1\npush 2\npush 3\npop\ntop\npop\nempty\n",
            "stdout": "3\n2\nfalse\n",
        },
    ],
    "valid-parentheses": [
        {"args": ["{[()()]}"], "expected": True},
        {"args": ["([)]"], "expected": False},
    ],
    "next-greater-element-i": [
        {"args": [[1, 3, 5, 2, 4], [5, 4, 2, 1, 3]], "expected": [-1, 5, -1, 3, -1]},
    ],
    "maximum-depth-of-binary-tree": [
        {"args": [[1, 2, 3, 4, None, None, 5, 6, None, None, None, None, None, 7]], "expected": 4},
    ],
    "invert-binary-tree": [
        {"args": [[1, 2, 3, 4, 5, 6, 7]], "expected": [1, 3, 2, 7, 6, 5, 4]},
    ],
    "symmetric-tree": [
        {"args": [[1, 2, 2, 3, 4, 4, 3, 5, 6, 6, 5]], "expected": True},
    ],
    "linked-list-cycle": [
        {"args": [[1, 2, 3, 4, 5, 6, 7, 8]], "expected": False},
    ],
    "linked-list-cycle-ii": [
        {"args": [[1, 2, 3, 4, 5, 6]], "expected": None},
    ],
    "best-time-to-buy-and-sell-stock": [
        {"args": [[2, 4, 1, 7, 11, 9, 13, 15, 14, 12]], "expected": 14},
    ],
    "combinations": [
        {
            "args": [5, 3],
            "expected": [[1, 2, 3], [1, 2, 4], [1, 2, 5], [1, 3, 4], [1, 3, 5], [1, 4, 5], [2, 3, 4], [2, 3, 5], [2, 4, 5], [3, 4, 5]],
        },
    ],
    "3sum": [
        {"args": [[-2, 0, 1, 1, 2]], "expected": [[-2, 0, 2], [-2, 1, 1]]},
    ],
    "minimum-size-subarray-sum": [
        {"args": [15, [1, 2, 3, 4, 5]], "expected": 5},
    ],
    "ransom-note": [
        {"args": ["aa", "aab"], "expected": True},
    ],
    "intersection-of-two-arrays": [
        {"args": [[4, 9, 5], [9, 4, 9, 8, 4]], "expected": [9, 4]},
    ],
    "search-insert-position": [
        {"args": [[1, 3, 5, 6], 0], "expected": 0},
    ],
    "sqrtx": [
        {"args": [2147483647], "expected": 46340},
    ],
    "evaluate-reverse-polish-notation": [
        {"args": [["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"]], "expected": 22},
    ],
    "top-k-frequent-elements": [
        {"args": [[4, 4, 4, 6, 6, 7, 8, 8, 8], 2], "expected": [4, 8]},
    ],
    "assign-cookies": [
        {"args": [[10, 9, 8, 7], [5, 6, 7, 8]], "expected": 2},
    ],
    "remove-linked-list-elements": [
        {"args": [[1, 2, 6, 3, 4, 5, 6, 6, 7, 6], 6], "expected": [1, 2, 3, 4, 5, 7]},
    ],
    "middle-of-the-linked-list": [
        {"args": [[1, 2, 3, 4, 5, 6]], "expected": [4, 5, 6]},
    ],
    "same-tree": [
        {"args": [[1, 2, 3, 4, 5], [1, 2, 3, 4, None]], "expected": False},
    ],
    "validate-binary-search-tree": [
        {"args": [[5, 1, 4, None, None, 3, 6]], "expected": False},
    ],
    "4sum-ii": [
        {"args": [[0, 1, -1], [0, -1, 2], [-1, 2, -2], [-2, 0, 1]], "expected": 11},
    ],
    "spiral-matrix-ii": [
        {"args": [4], "expected": [[1, 2, 3, 4], [12, 13, 14, 5], [11, 16, 15, 6], [10, 9, 8, 7]]},
    ],
    "remove-all-adjacent-duplicates-in-string": [
        {"args": ["aabbbaca"], "expected": "ca"},
    ],
    "fruit-into-baskets": [
        {"args": [[3, 3, 3, 1, 2, 1, 1, 2, 3, 3, 2]], "expected": 5},
    ],
    "gas-station": [
        {"args": [[5, 1, 2, 3, 4], [4, 4, 1, 5, 1]], "expected": 4},
    ],
    # --- EXTRA_TEST_DEFINITIONS ---
    "4sum": [
        {
            "args": [[1, 0, -1, 0, -2, 2, 3, -3], 0],
            "expected": [
                [-3, -2, 2, 3],
                [-3, -1, 1, 3],
                [-3, 0, 0, 3],
                [-3, 0, 1, 2],
                [-2, -1, 0, 3],
                [-2, -1, 1, 2],
                [-2, 0, 0, 2],
                [-1, 0, 0, 1],
            ],
        },
    ],
    "remove-nth-node-from-end-of-list": [
        {"args": [[1, 2, 3, 4, 5, 6, 7, 8], 3], "expected": [1, 2, 3, 4, 5, 6, 8]},
    ],
    "swap-nodes-in-pairs": [
        {"args": [[1, 2, 3, 4, 5, 6]], "expected": [2, 1, 4, 3, 6, 5]},
    ],
    "jump-game-ii": [
        {"args": [[1, 1, 1, 1, 1]], "expected": 4},
    ],
    "permutations-ii": [
        {"args": [[1, 1, 2, 2]], "expected": [[1, 1, 2, 2], [1, 2, 1, 2], [1, 2, 2, 1], [2, 1, 1, 2], [2, 1, 2, 1], [2, 2, 1, 1]]},
    ],
    "spiral-matrix": [
        {"args": [[[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]], "expected": [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7]},
    ],
    "length-of-last-word": [
        {"args": ["   fly me   to   the moon  "], "expected": 4},
    ],
    "reverse-linked-list-ii": [
        {"args": [[1, 2, 3, 4, 5, 6, 7], 2, 5], "expected": [1, 5, 4, 3, 2, 6, 7]},
    ],
    "binary-tree-inorder-traversal": [
        {"args": [[1, None, 2, 3, 4, None, 5, 6]], "expected": [1, 3, 5, 2, 6, 4]},
    ],
    "construct-binary-tree-from-preorder-and-inorder-traversal": [
        {"args": [[3, 9, 20, 15, 7, 8], [9, 3, 15, 20, 7, 8]], "expected": [3, 9, 20, None, None, 15, 7, None, None, None, 8]},
    ],
    "construct-binary-tree-from-inorder-and-postorder-traversal": [
        {"args": [[9, 3, 15, 20, 7, 8], [9, 15, 7, 8, 20, 3]], "expected": [3, 9, 20, None, None, 15, 7, None, None, None, 8]},
    ],
    "binary-tree-level-order-traversal-ii": [
        {"args": [[1, 2, 3, 4, 5, 6, 7]], "expected": [[4, 5, 6, 7], [2, 3], [1]]},
    ],
    "convert-sorted-array-to-binary-search-tree": [
        {"args": [[-10, -3, 0, 5, 9, 12, 15]], "expected": [5, -3, 12, -10, 0, 9, 15]},
    ],
    "minimum-depth-of-binary-tree": [
        {"args": [[1, 2, 3, 4, None, None, 5]], "expected": 2},
    ],
    "best-time-to-buy-and-sell-stock-ii": [
        {"args": [[1, 2, 3, 4, 5, 6, 7, 8, 9]], "expected": 8},
    ],
    "binary-tree-preorder-traversal": [
        {"args": [[1, None, 2, 3, 4, None, 5, 6]], "expected": [1, 2, 3, 5, 4, 6]},
    ],
    "binary-tree-postorder-traversal": [
        {"args": [[1, None, 2, 3, 4, None, 5, 6]], "expected": [5, 3, 6, 4, 2, 1]},
    ],
    "reverse-words-in-a-string": [
        {"args": ["  a good   example  "], "expected": "example good a"},
    ],
    "two-sum-ii-input-array-is-sorted": [
        {"args": [[1, 2, 3, 4, 4, 9, 56, 90], 8], "expected": [4, 5]},
    ],
    "reverse-words-in-a-string-ii": [
        {"args": ["  a good   example  "], "expected": "example good a"},
    ],
    "binary-tree-right-side-view": [
        {"args": [[1, 2, 3, 4, 5, None, 6, 7, None, None, None, None, None, None, 8]], "expected": [1, 3, 6, 7, 8]},
    ],
    "shortest-palindrome": [
        {"args": ["abababab"], "expected": "babababab"},
    ],
    "count-complete-tree-nodes": [
        {"args": [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]], "expected": 10},
    ],
    "palindrome-linked-list": [
        {"args": [[1, 2, 3, 2, 1]], "expected": True},
    ],
    "lowest-common-ancestor-of-a-binary-search-tree": [
        {"args": [[6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 0, 4], "expected": 2},
    ],
    "lowest-common-ancestor-of-a-binary-tree": [
        {"args": [[3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 6, 4], "expected": 5},
    ],
    "delete-node-in-a-linked-list": [
        {"args": [[1, 2, 3, 4, 5, 6], 3], "expected": [1, 2, 4, 5, 6]},
    ],
    "binary-tree-paths": [
        {"args": [[1, 2, 3, 4, 5, None, 6]], "expected": ["1->2->4", "1->2->5", "1->3->6"]},
    ],
    "reverse-vowels-of-a-string": [
        {"args": ["leetcode"], "expected": "leotcede"},
    ],
    "intersection-of-two-arrays-ii": [
        {"args": [[4, 9, 5], [9, 4, 9, 8, 4]], "expected": [4, 9, 9]},
    ],
    "valid-perfect-square": [
        {"args": [808201], "expected": True},
    ],
    "sum-of-left-leaves": [
        {"args": [[1, 2, 3, 4, 5, 6, 7]], "expected": 10},
    ],
    "add-strings": [
        {"args": ["456", "77"], "expected": "533"},
    ],
    "delete-node-in-a-bst": [
        {"args": [[5, 3, 6, 2, 4, None, 7], 7], "expected": [5, 3, 6, 2, 4]},
    ],
    "minimum-number-of-arrows-to-burst-balloons": [
        {"args": [[[1, 2], [2, 3], [3, 4], [4, 5]]], "expected": 2},
    ],
    "repeated-substring-pattern": [
        {"args": ["abcabcabcabc"], "expected": True},
    ],
    "find-mode-in-binary-search-tree": [
        {"args": [[1, 1, 2, 2, 2, 2]], "expected": [2]},
    ],
    "next-greater-element-ii": [
        {"args": [[3, 8, 4, 1, 2]], "expected": [8, -1, 8, 2, 3]},
    ],
    "find-bottom-left-tree-value": [
        {"args": [[1, 2, 3, 4, None, 5, 6, 7]], "expected": 7},
    ],
    "coin-change-ii": [
        {"args": [10, [1, 2, 5]], "expected": 10},
    ],
    "minimum-absolute-difference-in-bst": [
        {"args": [[1, 0, 48, None, None, 12, 49]], "expected": 1},
    ],
    "reverse-string-ii": [
        {"args": ["abcdefgh", 3], "expected": "cbadefhg"},
    ],
    "subtree-of-another-tree": [
        {"args": [[3, 4, 5, 1, 2, None, None, None, None, 0], [4, 1, 2]], "expected": False},
    ],
    "average-of-levels-in-binary-tree": [
        {"args": [[1, 2, 3, 4, 5, 6, 7]], "expected": [1.0, 2.5, 5.5]},
    ],
    "search-in-a-binary-search-tree": [
        {"args": [[5, 3, 6, 2, 4, None, 7], 6], "expected": [6, 7]},
    ],
    "insert-into-a-binary-search-tree": [
        {"args": [[4, 2, 7, 1, 3], 10], "expected": [4, 2, 7, 1, 3, None, 10]},
    ],
    "design-linked-list": [
        {
            "stdin": "9\naddAtHead 1\naddAtTail 3\naddAtIndex 1 2\nget 1\naddAtIndex 0 4\nget 0\nget 3\ndeleteAtIndex 2\nget 2\n",
            "stdout": "2\n4\n3\n2\n",
        },
    ],
    "rotate-string": [
        {"args": ["abcdefgabcdefg", "defgabcdefgabc"], "expected": True},
    ],
    "longest-happy-prefix": [
        {"args": ["ababab"], "expected": "abab"},
    ],
}
