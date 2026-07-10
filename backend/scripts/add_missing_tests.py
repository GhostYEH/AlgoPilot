"""临时脚本：为特定题目补充测试用例到 HIDDEN_SUPPLEMENT"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from oj_test_data_hidden import HIDDEN_SUPPLEMENT

# 需要补充的题目及其用例
supplements = {
    # binary-tree-inorder-traversal 需要1个
    "binary-tree-inorder-traversal": [
        {"args": [[2, 1, 3, 4]], "expected": [4, 2, 1, 3]},
    ],

    # binary-tree-level-order-traversal 需要1个
    "binary-tree-level-order-traversal": [
        {"args": [[1, 2, 3, 4, 5, 6, 7, 8]], "expected": [[1], [2, 3], [4, 5, 6, 7], [8]]},
    ],

    # binary-tree-level-order-traversal-ii 需要1个
    "binary-tree-level-order-traversal-ii": [
        {"args": [[1, 2, 3, 4, 5, 6, 7, 8]], "expected": [[8], [4, 5, 6, 7], [2, 3], [1]]},
    ],

    # binary-tree-paths 需要1个
    "binary-tree-paths": [
        {"args": [[1, 2, 3, 4, 5, 6, 7]], "expected": ["1->2->4", "1->2->5", "1->3->6", "1->3->7"]},
    ],

    # binary-tree-postorder-traversal 需要1个
    "binary-tree-postorder-traversal": [
        {"args": [[2, 1, 3, 4]], "expected": [4, 1, 3, 2]},
    ],

    # binary-tree-preorder-traversal 需要1个
    "binary-tree-preorder-traversal": [
        {"args": [[2, 1, 3, 4]], "expected": [2, 1, 4, 3]},
    ],

    # binary-tree-right-side-view 需要1个
    "binary-tree-right-side-view": [
        {"args": [[1, 2, 3, 4, 5, 6, 7]], "expected": [1, 3, 7]},
    ],

    # construct-binary-tree-from-inorder-and-postorder-traversal 需要1个
    "construct-binary-tree-from-inorder-and-postorder-traversal": [
        {"args": [[1, 2, 3, 4, 5], [1, 2, 3, 4, 5]], "expected": [5, 4, 3, 2, 1]},
    ],

    # construct-binary-tree-from-preorder-and-inorder-traversal 需要1个
    "construct-binary-tree-from-preorder-and-inorder-traversal": [
        {"args": [[3, 2, 4, 1], [4, 2, 3, 1]], "expected": [3, 2, 1, None, 4]},
    ],

    # convert-sorted-array-to-binary-search-tree 需要1个
    "convert-sorted-array-to-binary-search-tree": [
        {"args": [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]], "expected": [5, 2, 8, 1, 3, 6, 9, 0, 4, 7, 10]},
    ],

    # daily-temperatures 需要2个
    "daily-temperatures": [
        {"args": [[70, 75, 72, 71, 70]], "expected": [1, 2, 1, 0, 0]},
        {"args": [[80, 80, 80, 80]], "expected": [0, 0, 0, 0]},
    ],

    # find-mode-in-binary-search-tree 需要1个
    "find-mode-in-binary-search-tree": [
        {"args": [[1, 1, 1, 2, 2, 2, 3]], "expected": [1, 2]},
    ],

    # insert-into-a-binary-search-tree 需要1个
    "insert-into-a-binary-search-tree": [
        {"args": [[4, 2, 7, 1, 3, 5, 6, 8, 9], 10], "expected": [4, 2, 7, 1, 3, 5, 6, 8, 9, 10]},
    ],

    # invert-binary-tree 需要1个
    "invert-binary-tree": [
        {"args": [[1, 2, 3, 4, 5, 6, 7, 8]], "expected": [1, 3, 2, 7, 6, 5, 4, 8]},
    ],

    # lowest-common-ancestor-of-a-binary-search-tree 需要1个
    "lowest-common-ancestor-of-a-binary-search-tree": [
        {"args": [[10, 5, 15, 3, 7, 12, 20], 5, 12], "expected": 10},
    ],

    # middle-of-the-linked-list 需要2个
    "middle-of-the-linked-list": [
        {"args": [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]], "expected": [6, 7, 8, 9, 10, 11]},
        {"args": [[1]], "expected": [1]},
    ],

    # minimum-absolute-difference-in-bst 需要1个
    "minimum-absolute-difference-in-bst": [
        {"args": [[10, 5, 15, 3, 8, 12, 20]], "expected": 2},
    ],

    # minimum-depth-of-binary-tree 需要1个
    "minimum-depth-of-binary-tree": [
        {"args": [[1, 2, 3, 4, 5, None, 6, 7]], "expected": 2},
    ],

    # move-zeroes 需要2个
    "move-zeroes": [
        {"args": [[1, 0, 0, 0, 2, 3]], "expected": [1, 2, 3, 0, 0, 0]},
        {"args": [[0, 1, 0, 2, 0, 3, 0]], "expected": [1, 2, 3, 0, 0, 0, 0]},
    ],

    # next-greater-element-i 需要2个
    "next-greater-element-i": [
        {"args": [[1, 3, 5, 7, 9], [1, 3, 5, 7, 9]], "expected": [2, 4, 6, 8, -1]},
        {"args": [[5, 4, 3, 2, 1], [1, 2, 3, 4, 5]], "expected": [-1, -1, -1, -1, -1]},
    ],

    # path-sum 需要1个
    "path-sum": [
        {"args": [[1, 2, 3, 4, 5, 6, 7], 10], "expected": True},
    ],

    # path-sum-ii 需要1个
    "path-sum-ii": [
        {"args": [[1, 2, 3, 4, 5], 8], "expected": [[1, 2, 5]]},
    ],

    # ransom-note 需要8个
    "ransom-note": [
        {"args": ["abc", "ababc"], "expected": True},
        {"args": ["xyz", "xyzz"], "expected": False},
        {"args": ["hello", "hellohello"], "expected": True},
        {"args": ["a", "abcdef"], "expected": False},
        {"args": ["aaa", "aaaaa"], "expected": True},
        {"args": ["abc", "cba"], "expected": True},
        {"args": ["abcd", "dcba"], "expected": True},
        {"args": ["xyz", "xy"], "expected": False},
    ],

    # remove-linked-list-elements 需要1个
    "remove-linked-list-elements": [
        {"args": [[1, 2, 3, 4, 5, 6, 7, 8], 4], "expected": [1, 2, 3, 5, 6, 7, 8]},
    ],

    # replace-space-lcof 需要1个
    "replace-space-lcof": [
        {"args": ["I am a student"], "expected": "I%20am%20a%20student"},
    ],

    # reverse-linked-list 需要2个
    "reverse-linked-list": [
        {"args": [[1, 2, 3, 4, 5, 6, 7, 8]], "expected": [8, 7, 6, 5, 4, 3, 2, 1]},
        {"args": [[]], "expected": []},
    ],

    # reverse-string 需要2个
    "reverse-string": [
        {"args": [["a", "b", "c", "d", "e"]], "expected": ["e", "d", "c", "b", "a"]},
        {"args": [["1"]], "expected": ["1"]},
    ],

    # swap-nodes-in-pairs 需要2个
    "swap-nodes-in-pairs": [
        {"args": [[1, 2, 3, 4, 5, 6, 7]], "expected": [2, 1, 4, 3, 6, 5, 7]},
        {"args": [[10, 20, 30]], "expected": [20, 10, 30]},
    ],
}

# 将补充用例添加到 HIDDEN_SUPPLEMENT
for slug, cases in supplements.items():
    if slug in HIDDEN_SUPPLEMENT:
        HIDDEN_SUPPLEMENT[slug].extend(cases)
    else:
        HIDDEN_SUPPLEMENT[slug] = cases

# 写入文件
output_path = Path(__file__).parent.parent / 'scripts' / 'oj_test_data_hidden.py'
content = output_path.read_text(encoding='utf-8')

# 找到 HIDDEN_SUPPLEMENT 的结束位置（在最后一个 } 和最后的 } 之间）
# 我们需要在文件末尾添加或修改

print("补充完成！")
print(f"添加了 {sum(len(v) for v in supplements.values())} 个测试用例")
