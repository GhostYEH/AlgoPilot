"""
OJ 测试用例正确性验证脚本
为每道题实现正确的 Python 解法，运行所有测试用例，验证 expected 值是否正确。
"""
import json
import sys
from pathlib import Path
from typing import Any, Optional

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

from oj_test_data import TEST_DEFINITIONS
from oj_test_data_extra import EXTRA_TEST_DEFINITIONS
from oj_test_data_hidden import HIDDEN_SUPPLEMENT
from oj_test_data_samples import SAMPLE_OVERRIDES

# ─── 辅助函数 ───

def list_to_tree(arr):
    """LeetCode 层序数组 → 二叉树"""
    if not arr:
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

def tree_to_list(root):
    """二叉树 → LeetCode 层序数组"""
    if not root:
        return []
    result = []
    queue = [root]
    while queue:
        node = queue.pop(0)
        if node is None:
            result.append(None)
        else:
            result.append(node["val"])
            queue.append(node["left"])
            queue.append(node["right"])
    # 去掉末尾 None
    while result and result[-1] is None:
        result.pop()
    return result

def list_to_linked(arr):
    """数组 → 链表（带 cycle 检测用）"""
    if not arr:
        return None, []
    nodes = [{"val": v, "next": None} for v in arr]
    for i in range(len(nodes) - 1):
        nodes[i]["next"] = nodes[i + 1]
    return nodes[0], nodes

def linked_to_list(head):
    """链表 → 数组"""
    result = []
    seen = set()
    cur = head
    while cur and id(cur) not in seen:
        seen.add(id(cur))
        result.append(cur["val"])
        cur = cur.get("next")
    return result

def normalize_nested_list(lst):
    """对嵌套列表排序（用于无序比较）"""
    if not lst:
        return lst
    if isinstance(lst[0], list):
        return sorted([sorted(inner) if isinstance(inner, list) else inner for inner in lst])
    return sorted(lst)

# ─── 题目解法 ───

SOLUTIONS = {}

# ── array ──

def _two_sum(nums, target):
    d = {}
    for i, n in enumerate(nums):
        if target - n in d:
            return [d[target - n], i]
        d[n] = i
SOLUTIONS["two-sum"] = lambda args: _two_sum(*args)

def _two_sum_ii(numbers, target):
    l, r = 0, len(numbers) - 1
    while l < r:
        s = numbers[l] + numbers[r]
        if s == target:
            return [l + 1, r + 1]
        elif s < target:
            l += 1
        else:
            r -= 1
SOLUTIONS["two-sum-ii-input-array-is-sorted"] = lambda args: _two_sum_ii(*args)

def _3sum(nums):
    nums.sort()
    res = []
    for i in range(len(nums) - 2):
        if i > 0 and nums[i] == nums[i-1]:
            continue
        l, r = i + 1, len(nums) - 1
        while l < r:
            s = nums[i] + nums[l] + nums[r]
            if s == 0:
                res.append([nums[i], nums[l], nums[r]])
                while l < r and nums[l] == nums[l+1]: l += 1
                while l < r and nums[r] == nums[r-1]: r -= 1
                l += 1; r -= 1
            elif s < 0:
                l += 1
            else:
                r -= 1
    return res
SOLUTIONS["3sum"] = lambda args: _3sum(*args)

def _4sum(nums, target):
    nums.sort()
    res = []
    n = len(nums)
    for i in range(n - 3):
        if i > 0 and nums[i] == nums[i-1]: continue
        for j in range(i+1, n - 2):
            if j > i+1 and nums[j] == nums[j-1]: continue
            l, r = j + 1, n - 1
            while l < r:
                s = nums[i] + nums[j] + nums[l] + nums[r]
                if s == target:
                    res.append([nums[i], nums[j], nums[l], nums[r]])
                    while l < r and nums[l] == nums[l+1]: l += 1
                    while l < r and nums[r] == nums[r-1]: r -= 1
                    l += 1; r -= 1
                elif s < target:
                    l += 1
                else:
                    r -= 1
    return res
SOLUTIONS["4sum"] = lambda args: _4sum(*args)

def _4sum_ii(A, B, C, D):
    from collections import Counter
    ab = Counter(a + b for a in A for b in B)
    return sum(ab[-(c + d)] for c in C for d in D)
SOLUTIONS["4sum-ii"] = lambda args: _4sum_ii(*args)

def _remove_element(nums, val):
    k = 0
    for i in range(len(nums)):
        if nums[i] != val:
            nums[k] = nums[i]
            k += 1
    return k
SOLUTIONS["remove-element"] = lambda args: _remove_element(*args)

def _remove_duplicates(nums):
    if not nums: return 0
    k = 1
    for i in range(1, len(nums)):
        if nums[i] != nums[k-1]:
            nums[k] = nums[i]
            k += 1
    return k
SOLUTIONS["remove-duplicates-from-sorted-array"] = lambda args: _remove_duplicates(*args)

def _search_insert(nums, target):
    l, r = 0, len(nums)
    while l < r:
        m = (l + r) // 2
        if nums[m] < target:
            l = m + 1
        else:
            r = m
    return l
SOLUTIONS["search-insert-position"] = lambda args: _search_insert(*args)

def _find_first_and_last(nums, target):
    def find_left():
        l, r = 0, len(nums)
        while l < r:
            m = (l + r) // 2
            if nums[m] < target: l = m + 1
            else: r = m
        return l
    def find_right():
        l, r = 0, len(nums)
        while l < r:
            m = (l + r) // 2
            if nums[m] <= target: l = m + 1
            else: r = m
        return l - 1
    left = find_left()
    if left >= len(nums) or nums[left] != target:
        return [-1, -1]
    return [left, find_right()]
SOLUTIONS["find-first-and-last-position-of-element-in-sorted-array"] = lambda args: _find_first_and_last(*args)

def _squares_sorted(nums):
    return sorted(x * x for x in nums)
SOLUTIONS["squares-of-a-sorted-array"] = lambda args: _squares_sorted(*args)

def _move_zeroes(nums):
    k = 0
    for i in range(len(nums)):
        if nums[i] != 0:
            nums[k] = nums[i]
            k += 1
    for i in range(k, len(nums)):
        nums[i] = 0
    return nums
SOLUTIONS["move-zeroes"] = lambda args: _move_zeroes(*args)

def _sort_colors(nums):
    from collections import Counter
    c = Counter(nums)
    i = 0
    for v in [0, 1, 2]:
        for _ in range(c[v]):
            nums[i] = v; i += 1
    return nums
SOLUTIONS["sort-colors"] = lambda args: _sort_colors(*args)

def _minimum_size_subarray_sum(target, nums):
    l = 0
    s = 0
    res = float('inf')
    for r in range(len(nums)):
        s += nums[r]
        while s >= target:
            res = min(res, r - l + 1)
            s -= nums[l]
            l += 1
    return res if res != float('inf') else 0
SOLUTIONS["minimum-size-subarray-sum"] = lambda args: _minimum_size_subarray_sum(*args)

def _length_of_last_word(s):
    return len(s.strip().split()[-1])
SOLUTIONS["length-of-last-word"] = lambda args: _length_of_last_word(*args)

def _add_strings(num1, num2):
    i, j, carry = len(num1) - 1, len(num2) - 1, 0
    res = []
    while i >= 0 or j >= 0 or carry:
        d1 = int(num1[i]) if i >= 0 else 0
        d2 = int(num2[j]) if j >= 0 else 0
        s = d1 + d2 + carry
        res.append(str(s % 10))
        carry = s // 10
        i -= 1; j -= 1
    return ''.join(reversed(res))
SOLUTIONS["add-strings"] = lambda args: _add_strings(*args)

# ── binary search ──

def _binary_search(nums, target):
    l, r = 0, len(nums) - 1
    while l <= r:
        m = (l + r) // 2
        if nums[m] == target: return m
        elif nums[m] < target: l = m + 1
        else: r = m - 1
    return -1
SOLUTIONS["binary-search"] = lambda args: _binary_search(*args)

def _sqrtx(x):
    if x <= 1: return x
    l, r = 1, x
    while l <= r:
        m = (l + r) // 2
        if m * m <= x < (m+1)*(m+1): return m
        elif m * m < x: l = m + 1
        else: r = m - 1
    return r
SOLUTIONS["sqrtx"] = lambda args: _sqrtx(*args)

def _valid_perfect_square(num):
    if num < 2: return True
    l, r = 2, num // 2
    while l <= r:
        m = (l + r) // 2
        sq = m * m
        if sq == num: return True
        elif sq < num: l = m + 1
        else: r = m - 1
    return False
SOLUTIONS["valid-perfect-square"] = lambda args: _valid_perfect_square(*args)

# ── linked list ──

def _reverse_linked_list(arr):
    # 输入是数组表示链表，输出也是数组
    return arr[::-1]
SOLUTIONS["reverse-linked-list"] = lambda args: _reverse_linked_list(*args)

def _reverse_linked_list_ii(arr, left, right):
    # 1-indexed
    a = arr[:]
    a[left-1:right] = a[left-1:right][::-1]
    return a
SOLUTIONS["reverse-linked-list-ii"] = lambda args: _reverse_linked_list_ii(*args)

def _swap_nodes_in_pairs(arr):
    res = arr[:]
    for i in range(0, len(res) - 1, 2):
        res[i], res[i+1] = res[i+1], res[i]
    return res
SOLUTIONS["swap-nodes-in-pairs"] = lambda args: _swap_nodes_in_pairs(*args)

def _reverse_nodes_in_k_group(arr, k):
    res = []
    for i in range(0, len(arr), k):
        group = arr[i:i+k]
        if len(group) == k:
            res.extend(group[::-1])
        else:
            res.extend(group)
    return res
SOLUTIONS["reverse-nodes-in-k-group"] = lambda args: _reverse_nodes_in_k_group(*args)

def _remove_nth_from_end(arr, n):
    idx = len(arr) - n
    return arr[:idx] + arr[idx+1:]
SOLUTIONS["remove-nth-node-from-end-of-list"] = lambda args: _remove_nth_from_end(*args)

def _delete_node_in_linked_list(arr, node_val):
    # 删除值为 node_val 的节点的下一个节点
    idx = arr.index(node_val)
    if idx + 1 < len(arr):
        return arr[:idx+1] + arr[idx+2:]
    return arr[:]
SOLUTIONS["delete-node-in-a-linked-list"] = lambda args: _delete_node_in_linked_list(*args)

def _remove_linked_list_elements(arr, val):
    return [x for x in arr if x != val]
SOLUTIONS["remove-linked-list-elements"] = lambda args: _remove_linked_list_elements(*args)

def _linked_list_cycle(arr, pos):
    return pos >= 0
SOLUTIONS["linked-list-cycle"] = lambda args: _linked_list_cycle(*args)

def _linked_list_cycle_ii(arr, pos):
    if pos < 0: return -1
    return pos
SOLUTIONS["linked-list-cycle-ii"] = lambda args: _linked_list_cycle_ii(*args)

def _intersection_of_two_linked_lists(listA, listB, skipA, skipB):
    # 简化：返回交点的值或 None
    # 实际测试用例格式需要检查
    return None  # 需要特殊处理
SOLUTIONS["intersection-of-two-linked-lists"] = lambda args: _intersection_of_two_linked_lists(*args)

def _palindrome_linked_list(arr):
    return arr == arr[::-1]
SOLUTIONS["palindrome-linked-list"] = lambda args: _palindrome_linked_list(*args)

def _middle_of_linked_list(arr):
    mid = len(arr) // 2
    return arr[mid:]
SOLUTIONS["middle-of-the-linked-list"] = lambda args: _middle_of_linked_list(*args)

def _design_linked_list(ops):
    # 需要特殊处理
    return ops
SOLUTIONS["design-linked-list"] = lambda args: _design_linked_list(*args)

# ── binary tree ──

def _preorder(arr):
    root = list_to_tree(arr)
    res = []
    def dfs(n):
        if not n: return
        res.append(n["val"])
        dfs(n["left"])
        dfs(n["right"])
    dfs(root)
    return res
SOLUTIONS["binary-tree-preorder-traversal"] = lambda args: _preorder(*args)

def _inorder(arr):
    root = list_to_tree(arr)
    res = []
    def dfs(n):
        if not n: return
        dfs(n["left"])
        res.append(n["val"])
        dfs(n["right"])
    dfs(root)
    return res
SOLUTIONS["binary-tree-inorder-traversal"] = lambda args: _inorder(*args)

def _postorder(arr):
    root = list_to_tree(arr)
    res = []
    def dfs(n):
        if not n: return
        dfs(n["left"])
        dfs(n["right"])
        res.append(n["val"])
    dfs(root)
    return res
SOLUTIONS["binary-tree-postorder-traversal"] = lambda args: _postorder(*args)

def _level_order(arr):
    root = list_to_tree(arr)
    if not root: return []
    res = []
    q = [root]
    while q:
        level = []
        nq = []
        for n in q:
            level.append(n["val"])
            if n["left"]: nq.append(n["left"])
            if n["right"]: nq.append(n["right"])
        res.append(level)
        q = nq
    return res
SOLUTIONS["binary-tree-level-order-traversal"] = lambda args: _level_order(*args)

def _level_order_bottom(arr):
    return _level_order(arr)[::-1]
SOLUTIONS["binary-tree-level-order-traversal-ii"] = lambda args: _level_order_bottom(*args)

def _right_side_view(arr):
    root = list_to_tree(arr)
    if not root: return []
    res = []
    q = [root]
    while q:
        res.append(q[-1]["val"])
        nq = []
        for n in q:
            if n["left"]: nq.append(n["left"])
            if n["right"]: nq.append(n["right"])
        q = nq
    return res
SOLUTIONS["binary-tree-right-side-view"] = lambda args: _right_side_view(*args)

def _inverted(arr):
    root = list_to_tree(arr)
    def invert(n):
        if not n: return None
        n["left"], n["right"] = invert(n["right"]), invert(n["left"])
        return n
    invert(root)
    return tree_to_list(root)
SOLUTIONS["invert-binary-tree"] = lambda args: _inverted(*args)

def _symmetric(arr):
    root = list_to_tree(arr)
    def is_sym(a, b):
        if not a and not b: return True
        if not a or not b: return False
        return a["val"] == b["val"] and is_sym(a["left"], b["right"]) and is_sym(a["right"], b["left"])
    if not root: return True
    return is_sym(root["left"], root["right"])
SOLUTIONS["symmetric-tree"] = lambda args: _symmetric(*args)

def _max_depth(arr):
    root = list_to_tree(arr)
    def depth(n):
        if not n: return 0
        return 1 + max(depth(n["left"]), depth(n["right"]))
    return depth(root)
SOLUTIONS["maximum-depth-of-binary-tree"] = lambda args: _max_depth(*args)

def _min_depth(arr):
    root = list_to_tree(arr)
    def depth(n):
        if not n: return 0
        if not n["left"]: return 1 + depth(n["right"])
        if not n["right"]: return 1 + depth(n["left"])
        return 1 + min(depth(n["left"]), depth(n["right"]))
    return depth(root)
SOLUTIONS["minimum-depth-of-binary-tree"] = lambda args: _min_depth(*args)

def _same_tree(p, q):
    t1 = list_to_tree(p)
    t2 = list_to_tree(q)
    def same(a, b):
        if not a and not b: return True
        if not a or not b: return False
        return a["val"] == b["val"] and same(a["left"], b["left"]) and same(a["right"], b["right"])
    return same(t1, t2)
SOLUTIONS["same-tree"] = lambda args: _same_tree(*args)

def _path_sum(arr, target):
    root = list_to_tree(arr)
    def has(n, t):
        if not n: return False
        if not n["left"] and not n["right"]:
            return n["val"] == t
        return has(n["left"], t - n["val"]) or has(n["right"], t - n["val"])
    return has(root, target)
SOLUTIONS["path-sum"] = lambda args: _path_sum(*args)

def _path_sum_ii(arr, target):
    root = list_to_tree(arr)
    res = []
    def dfs(n, t, path):
        if not n: return
        path.append(n["val"])
        if not n["left"] and not n["right"] and n["val"] == t:
            res.append(list(path))
        dfs(n["left"], t - n["val"], path)
        dfs(n["right"], t - n["val"], path)
        path.pop()
    dfs(root, target, [])
    return res
SOLUTIONS["path-sum-ii"] = lambda args: _path_sum_ii(*args)

def _binary_tree_paths(arr):
    root = list_to_tree(arr)
    res = []
    def dfs(n, path):
        if not n: return
        path.append(str(n["val"]))
        if not n["left"] and not n["right"]:
            res.append("->".join(path))
        dfs(n["left"], path)
        dfs(n["right"], path)
        path.pop()
    dfs(root, [])
    return res
SOLUTIONS["binary-tree-paths"] = lambda args: _binary_tree_paths(*args)

def _count_complete_tree_nodes(arr):
    return len([x for x in arr if x is not None])
SOLUTIONS["count-complete-tree-nodes"] = lambda args: _count_complete_tree_nodes(*args)

def _balanced(arr):
    root = list_to_tree(arr)
    def check(n):
        if not n: return 0
        l = check(n["left"])
        r = check(n["right"])
        if l == -1 or r == -1 or abs(l - r) > 1: return -1
        return 1 + max(l, r)
    return check(root) != -1
SOLUTIONS["balanced-binary-tree"] = lambda args: _balanced(*args)

def _average_of_levels(arr):
    root = list_to_tree(arr)
    if not root: return []
    res = []
    q = [root]
    while q:
        level_sum = sum(n["val"] for n in q)
        res.append(level_sum / len(q))
        nq = []
        for n in q:
            if n["left"]: nq.append(n["left"])
            if n["right"]: nq.append(n["right"])
        q = nq
    return res
SOLUTIONS["average-of-levels-in-binary-tree"] = lambda args: _average_of_levels(*args)

def _merge_two_trees(p, q):
    t1 = list_to_tree(p)
    t2 = list_to_tree(q)
    def merge(a, b):
        if not a: return b
        if not b: return a
        a["val"] += b["val"]
        a["left"] = merge(a["left"], b["left"])
        a["right"] = merge(a["right"], b["right"])
        return a
    r = merge(t1, t2)
    return tree_to_list(r)
SOLUTIONS["merge-two-binary-trees"] = lambda args: _merge_two_trees(*args)

def _sum_of_left_leaves(arr):
    root = list_to_tree(arr)
    def dfs(n, is_left):
        if not n: return 0
        if not n["left"] and not n["right"] and is_left:
            return n["val"]
        return dfs(n["left"], True) + dfs(n["right"], False)
    return dfs(root, False)
SOLUTIONS["sum-of-left-leaves"] = lambda args: _sum_of_left_leaves(*args)

def _find_bottom_left(arr):
    root = list_to_tree(arr)
    if not root: return 0
    q = [root]
    leftmost = root["val"]
    while q:
        leftmost = q[0]["val"]
        nq = []
        for n in q:
            if n["left"]: nq.append(n["left"])
            if n["right"]: nq.append(n["right"])
        q = nq
    return leftmost
SOLUTIONS["find-bottom-left-tree-value"] = lambda args: _find_bottom_left(*args)

def _maximum_binary_tree(nums):
    def build(arr):
        if not arr: return None
        mx = max(arr)
        idx = arr.index(mx)
        node = {"val": mx, "left": build(arr[:idx]), "right": build(arr[idx+1:])}
        return node
    return tree_to_list(build(nums))
SOLUTIONS["maximum-binary-tree"] = lambda args: _maximum_binary_tree(*args)

def _validate_bst(arr):
    root = list_to_tree(arr)
    def check(n, lo, hi):
        if not n: return True
        if n["val"] <= lo or n["val"] >= hi: return False
        return check(n["left"], lo, n["val"]) and check(n["right"], n["val"], hi)
    return check(root, float('-inf'), float('inf'))
SOLUTIONS["validate-binary-search-tree"] = lambda args: _validate_bst(*args)

def _search_bst(arr, val):
    root = list_to_tree(arr)
    def search(n, v):
        if not n: return None
        if n["val"] == v: return n
        if v < n["val"]: return search(n["left"], v)
        return search(n["right"], v)
    r = search(root, val)
    return tree_to_list(r) if r else []
SOLUTIONS["search-in-a-binary-search-tree"] = lambda args: _search_bst(*args)

def _insert_bst(arr, val):
    root = list_to_tree(arr)
    def insert(n, v):
        if not n: return {"val": v, "left": None, "right": None}
        if v < n["val"]:
            n["left"] = insert(n["left"], v)
        else:
            n["right"] = insert(n["right"], v)
        return n
    r = insert(root, val)
    return tree_to_list(r)
SOLUTIONS["insert-into-a-binary-search-tree"] = lambda args: _insert_bst(*args)

def _delete_bst(arr, key):
    root = list_to_tree(arr)
    def find_min(n):
        while n["left"]: n = n["left"]
        return n
    def delete(n, k):
        if not n: return None
        if k < n["val"]:
            n["left"] = delete(n["left"], k)
        elif k > n["val"]:
            n["right"] = delete(n["right"], k)
        else:
            if not n["left"]: return n["right"]
            if not n["right"]: return n["left"]
            succ = find_min(n["right"])
            n["val"] = succ["val"]
            n["right"] = delete(n["right"], succ["val"])
        return n
    r = delete(root, key)
    return tree_to_list(r) if r else []
SOLUTIONS["delete-node-in-a-bst"] = lambda args: _delete_bst(*args)

def _convert_bst_greater(arr):
    root = list_to_tree(arr)
    total = [0]
    def reverse_inorder(n):
        if not n: return
        reverse_inorder(n["right"])
        total[0] += n["val"]
        n["val"] = total[0]
        reverse_inorder(n["left"])
    reverse_inorder(root)
    return tree_to_list(root)
SOLUTIONS["convert-bst-to-greater-tree"] = lambda args: _convert_bst_greater(*args)

def _sorted_array_to_bst(nums):
    def build(l, r):
        if l > r: return None
        m = (l + r) // 2
        return {"val": nums[m], "left": build(l, m-1), "right": build(m+1, r)}
    return tree_to_list(build(0, len(nums)-1))
SOLUTIONS["convert-sorted-array-to-binary-search-tree"] = lambda args: _sorted_array_to_bst(*args)

def _trim_bst(arr, low, high):
    root = list_to_tree(arr)
    def trim(n, lo, hi):
        if not n: return None
        if n["val"] < lo: return trim(n["right"], lo, hi)
        if n["val"] > hi: return trim(n["left"], lo, hi)
        n["left"] = trim(n["left"], lo, hi)
        n["right"] = trim(n["right"], lo, hi)
        return n
    r = trim(root, low, high)
    return tree_to_list(r) if r else []
SOLUTIONS["trim-a-binary-search-tree"] = lambda args: _trim_bst(*args)

def _lca_bst(arr, p, q):
    root = list_to_tree(arr)
    def lca(n, p, q):
        if not n: return None
        if p < n["val"] and q < n["val"]: return lca(n["left"], p, q)
        if p > n["val"] and q > n["val"]: return lca(n["right"], p, q)
        return n["val"]
    return lca(root, p, q)
SOLUTIONS["lowest-common-ancestor-of-a-binary-search-tree"] = lambda args: _lca_bst(*args)

def _lca_bt(arr, p, q):
    root = list_to_tree(arr)
    def lca(n, p, q):
        if not n: return None
        if n["val"] == p or n["val"] == q: return n["val"]
        l = lca(n["left"], p, q)
        r = lca(n["right"], p, q)
        if l and r: return n["val"]
        return l or r
    return lca(root, p, q)
SOLUTIONS["lowest-common-ancestor-of-a-binary-tree"] = lambda args: _lca_bt(*args)

def _find_mode(arr):
    from collections import Counter
    root = list_to_tree(arr)
    vals = []
    def inorder(n):
        if not n: return
        inorder(n["left"])
        vals.append(n["val"])
        inorder(n["right"])
    inorder(root)
    if not vals: return []
    c = Counter(vals)
    mx = max(c.values())
    return sorted([k for k, v in c.items() if v == mx])
SOLUTIONS["find-mode-in-binary-search-tree"] = lambda args: _find_mode(*args)

def _min_abs_diff_bst(arr):
    root = list_to_tree(arr)
    vals = []
    def inorder(n):
        if not n: return
        inorder(n["left"])
        vals.append(n["val"])
        inorder(n["right"])
    inorder(root)
    return min(vals[i+1] - vals[i] for i in range(len(vals)-1))
SOLUTIONS["minimum-absolute-difference-in-bst"] = lambda args: _min_abs_diff_bst(*args)

def _construct_from_pre_in(preorder, inorder):
    def build(pre, ino):
        if not pre: return None
        root_val = pre[0]
        idx = ino.index(root_val)
        left = build(pre[1:idx+1], ino[:idx])
        right = build(pre[idx+1:], ino[idx+1:])
        return {"val": root_val, "left": left, "right": right}
    return tree_to_list(build(preorder, inorder))
SOLUTIONS["construct-binary-tree-from-preorder-and-inorder-traversal"] = lambda args: _construct_from_pre_in(*args)

def _construct_from_in_post(inorder, postorder):
    def build(ino, post):
        if not post: return None
        root_val = post[-1]
        idx = ino.index(root_val)
        left = build(ino[:idx], post[:idx])
        right = build(ino[idx+1:], post[idx:idx+1] if idx+1 <= len(ino) else post[idx:])
        # fix: right subtree
        right = build(ino[idx+1:], post[idx:-1])
        return {"val": root_val, "left": left, "right": right}
    return tree_to_list(build(inorder, postorder))
SOLUTIONS["construct-binary-tree-from-inorder-and-postorder-traversal"] = lambda args: _construct_from_in_post(*args)

def _subtree(s, t):
    def is_same(a, b):
        if not a and not b: return True
        if not a or not b: return False
        return a["val"] == b["val"] and is_same(a["left"], b["left"]) and is_same(a["right"], b["right"])
    def check(n, sub):
        if not n: return False
        return is_same(n, sub) or check(n["left"], sub) or check(n["right"], sub)
    return check(list_to_tree(s), list_to_tree(t))
SOLUTIONS["subtree-of-another-tree"] = lambda args: _subtree(*args)

# ── stack / queue ──

def _valid_parentheses(s):
    stack = []
    mp = {')': '(', ']': '[', '}': '{'}
    for c in s:
        if c in '([{':
            stack.append(c)
        else:
            if not stack or stack[-1] != mp[c]:
                return False
            stack.pop()
    return not stack
SOLUTIONS["valid-parentheses"] = lambda args: _valid_parentheses(*args)

def _implement_stack_queues(ops):
    return ops  # 需要特殊处理
SOLUTIONS["implement-stack-using-queues"] = lambda args: _implement_stack_queues(*args)

def _implement_queue_stacks(ops):
    return ops  # 需要特殊处理
SOLUTIONS["implement-queue-using-stacks"] = lambda args: _implement_queue_stacks(*args)

def _evaluate_rpn(tokens):
    stack = []
    for t in tokens:
        if t in '+-*/':
            b, a = stack.pop(), stack.pop()
            if t == '+': stack.append(a + b)
            elif t == '-': stack.append(a - b)
            elif t == '*': stack.append(a * b)
            else: stack.append(int(a / b))
        else:
            stack.append(int(t))
    return stack[0]
SOLUTIONS["evaluate-reverse-polish-notation"] = lambda args: _evaluate_rpn(*args)

def _backspace_compare(s, t):
    def process(s):
        stack = []
        for c in s:
            if c == '#':
                if stack: stack.pop()
            else:
                stack.append(c)
        return ''.join(stack)
    return process(s) == process(t)
SOLUTIONS["backspace-string-compare"] = lambda args: _backspace_compare(*args)

def _remove_adjacent_duplicates(s):
    stack = []
    for c in s:
        if stack and stack[-1] == c:
            stack.pop()
        else:
            stack.append(c)
    return ''.join(stack)
SOLUTIONS["remove-all-adjacent-duplicates-in-string"] = lambda args: _remove_adjacent_duplicates(*args)

# ── string ──

def _reverse_string(s):
    return s[::-1]
SOLUTIONS["reverse-string"] = lambda args: _reverse_string(*args)

def _reverse_string_ii(s, k):
    res = list(s)
    for i in range(0, len(s), 2*k):
        res[i:i+k] = res[i:i+k][::-1]
    return ''.join(res)
SOLUTIONS["reverse-string-ii"] = lambda args: _reverse_string_ii(*args)

def _reverse_vowels(s):
    vowels = set('aeiouAEIOU')
    s = list(s)
    l, r = 0, len(s) - 1
    while l < r:
        while l < r and s[l] not in vowels: l += 1
        while l < r and s[r] not in vowels: r -= 1
        s[l], s[r] = s[r], s[l]
        l += 1; r -= 1
    return ''.join(s)
SOLUTIONS["reverse-vowels-of-a-string"] = lambda args: _reverse_vowels(*args)

def _reverse_words(s):
    return ' '.join(s.split()[::-1])
SOLUTIONS["reverse-words-in-a-string"] = lambda args: _reverse_words(*args)

def _reverse_words_ii(s):
    # 每个单词内部反转
    return ' '.join(w[::-1] for w in s.split(' '))
SOLUTIONS["reverse-words-in-a-string-ii"] = lambda args: _reverse_words_ii(*args)

def _rotate_array(nums, k):
    k = k % len(nums)
    return nums[-k:] + nums[:-k]
SOLUTIONS["rotate-array"] = lambda args: _rotate_array(*args)

def _rotate_string(s, goal):
    return len(s) == len(goal) and goal in s + s
SOLUTIONS["rotate-string"] = lambda args: _rotate_string(*args)

def _valid_anagram(s, t):
    from collections import Counter
    return Counter(s) == Counter(t)
SOLUTIONS["valid-anagram"] = lambda args: _valid_anagram(*args)

def _ransom_note(ransom, magazine):
    from collections import Counter
    mc = Counter(magazine)
    for c in ransom:
        if mc[c] <= 0: return False
        mc[c] -= 1
    return True
SOLUTIONS["ransom-note"] = lambda args: _ransom_note(*args)

def _group_anagrams(strs):
    from collections import defaultdict
    groups = defaultdict(list)
    for s in strs:
        groups[''.join(sorted(s))].append(s)
    return [sorted(g) for g in sorted(groups.values(), key=lambda x: x[0])]
SOLUTIONS["group-anagrams"] = lambda args: _group_anagrams(*args)

def _longest_happy_prefix(s):
    n = len(s)
    lps = [0] * n
    for i in range(1, n):
        j = lps[i-1]
        while j > 0 and s[i] != s[j]:
            j = lps[j-1]
        if s[i] == s[j]:
            j += 1
        lps[i] = j
    return s[:lps[-1]]
SOLUTIONS["longest-happy-prefix"] = lambda args: _longest_happy_prefix(*args)

def _shortest_palindrome(s):
    if not s: return ""
    rev = s[::-1]
    combined = s + '#' + rev
    n = len(combined)
    lps = [0] * n
    for i in range(1, n):
        j = lps[i-1]
        while j > 0 and combined[i] != combined[j]:
            j = lps[j-1]
        if combined[i] == combined[j]:
            j += 1
        lps[i] = j
    return rev[:len(s) - lps[-1]] + s
SOLUTIONS["shortest-palindrome"] = lambda args: _shortest_palindrome(*args)

def _replace_space(s):
    return s.replace(' ', '%20')
SOLUTIONS["replace-space-lcof"] = lambda args: _replace_space(*args)

def _repeated_substring_pattern(s):
    return s in (s + s)[1:-1]
SOLUTIONS["repeated-substring-pattern"] = lambda args: _repeated_substring_pattern(*args)

# ── hash table ──

def _happy_number(n):
    seen = set()
    while n != 1 and n not in seen:
        seen.add(n)
        n = sum(int(d)**2 for d in str(n))
    return n == 1
SOLUTIONS["happy-number"] = lambda args: _happy_number(*args)

def _intersection(nums1, nums2):
    return sorted(list(set(nums1) & set(nums2)))
SOLUTIONS["intersection-of-two-arrays"] = lambda args: _intersection(*args)

def _intersection_ii(nums1, nums2):
    from collections import Counter
    c1, c2 = Counter(nums1), Counter(nums2)
    res = []
    for k in c1:
        for _ in range(min(c1[k], c2[k])):
            res.append(k)
    return res
SOLUTIONS["intersection-of-two-arrays-ii"] = lambda args: _intersection_ii(*args)

def _top_k_frequent(nums, k):
    from collections import Counter
    c = Counter(nums)
    return [x for x, _ in c.most_common(k)]
SOLUTIONS["top-k-frequent-elements"] = lambda args: _top_k_frequent(*args)

# ── greedy ──

def _assign_cookies(g, s):
    g.sort(); s.sort()
    i = j = 0
    while i < len(g) and j < len(s):
        if s[j] >= g[i]: i += 1
        j += 1
    return i
SOLUTIONS["assign-cookies"] = lambda args: _assign_cookies(*args)

def _best_time_buy_sell(prices):
    profit = 0
    for i in range(1, len(prices)):
        if prices[i] > prices[i-1]:
            profit += prices[i] - prices[i-1]
    return profit
SOLUTIONS["best-time-to-buy-and-sell-stock-ii"] = lambda args: _best_time_buy_sell(*args)

def _best_time_buy_sell_i(prices):
    mn = float('inf')
    profit = 0
    for p in prices:
        mn = min(mn, p)
        profit = max(profit, p - mn)
    return profit
SOLUTIONS["best-time-to-buy-and-sell-stock"] = lambda args: _best_time_buy_sell_i(*args)

def _jump_game(nums):
    far = 0
    for i, n in enumerate(nums):
        if i > far: return False
        far = max(far, i + n)
    return True
SOLUTIONS["jump-game"] = lambda args: _jump_game(*args)

def _jump_game_ii(nums):
    jumps = far = end = 0
    for i in range(len(nums) - 1):
        far = max(far, i + nums[i])
        if i == end:
            jumps += 1
            end = far
    return jumps
SOLUTIONS["jump-game-ii"] = lambda args: _jump_game_ii(*args)

def _gas_station(gas, cost):
    if sum(gas) < sum(cost): return -1
    total = start = 0
    for i in range(len(gas)):
        total += gas[i] - cost[i]
        if total < 0:
            total = 0
            start = i + 1
    return start
SOLUTIONS["gas-station"] = lambda args: _gas_station(*args)

def _non_overlapping_intervals(intervals):
    if not intervals: return 0
    intervals.sort(key=lambda x: x[1])
    count = 0
    end = intervals[0][1]
    for i in range(1, len(intervals)):
        if intervals[i][0] < end:
            count += 1
        else:
            end = intervals[i][1]
    return count
SOLUTIONS["non-overlapping-intervals"] = lambda args: _non_overlapping_intervals(*args)

def _min_arrows(points):
    if not points: return 0
    points.sort(key=lambda x: x[1])
    arrows = 1
    end = points[0][1]
    for i in range(1, len(points)):
        if points[i][0] > end:
            arrows += 1
            end = points[i][1]
    return arrows
SOLUTIONS["minimum-number-of-arrows-to-burst-balloons"] = lambda args: _min_arrows(*args)

# ── dp ──

def _climbing_stairs(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a
SOLUTIONS["climbing-stairs"] = lambda args: _climbing_stairs(*args)

def _fibonacci(n):
    if n <= 1: return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
SOLUTIONS["fibonacci-number"] = lambda args: _fibonacci(*args)

def _coin_change(coins, amount):
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    for a in range(1, amount + 1):
        for c in coins:
            if c <= a:
                dp[a] = min(dp[a], dp[a - c] + 1)
    return dp[amount] if dp[amount] != float('inf') else -1
SOLUTIONS["coin-change"] = lambda args: _coin_change(*args)

def _coin_change_ii(amount, coins):
    dp = [0] * (amount + 1)
    dp[0] = 1
    for c in coins:
        for a in range(c, amount + 1):
            dp[a] += dp[a - c]
    return dp[amount]
SOLUTIONS["coin-change-ii"] = lambda args: _coin_change_ii(*args)

def _longest_increasing(nums):
    dp = [1] * len(nums)
    for i in range(1, len(nums)):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp) if dp else 0
SOLUTIONS["longest-increasing-subsequence"] = lambda args: _longest_increasing(*args)

def _partition_equal_subset(nums):
    s = sum(nums)
    if s % 2: return False
    target = s // 2
    dp = [False] * (target + 1)
    dp[0] = True
    for n in nums:
        for j in range(target, n - 1, -1):
            dp[j] = dp[j] or dp[j - n]
    return dp[target]
SOLUTIONS["partition-equal-subset-sum"] = lambda args: _partition_equal_subset(*args)

# ── backtracking ──

def _subsets(nums):
    res = [[]]
    for n in nums:
        res += [r + [n] for r in res]
    return sorted(res)
SOLUTIONS["subsets"] = lambda args: _subsets(*args)

def _combinations(n, k):
    from itertools import combinations
    return [list(c) for c in combinations(range(1, n+1), k)]
SOLUTIONS["combinations"] = lambda args: _combinations(*args)

def _permutations(nums):
    from itertools import permutations
    return [list(p) for p in permutations(nums)]
SOLUTIONS["permutations"] = lambda args: _permutations(*args)

def _permutations_ii(nums):
    from itertools import permutations
    return [list(p) for p in set(permutations(nums))]
SOLUTIONS["permutations-ii"] = lambda args: _permutations_ii(*args)

def _n_queens(n):
    def solve(row, cols, diag1, diag2):
        if row == n:
            return 1
        count = 0
        for col in range(n):
            if col in cols or row - col in diag1 or row + col in diag2:
                continue
            count += solve(row + 1, cols | {col}, diag1 | {row - col}, diag2 | {row + col})
        return count
    return solve(0, set(), set(), set())
SOLUTIONS["n-queens"] = lambda args: _n_queens(*args)

def _palindrome_partitioning(s):
    res = []
    def dfs(start, path):
        if start == len(s):
            res.append(list(path))
            return
        for end in range(start + 1, len(s) + 1):
            sub = s[start:end]
            if sub == sub[::-1]:
                path.append(sub)
                dfs(end, path)
                path.pop()
    dfs(0, [])
    return res
SOLUTIONS["palindrome-partitioning"] = lambda args: _palindrome_partitioning(*args)

# ── monotonic stack ──

def _daily_temperatures(temps):
    n = len(temps)
    res = [0] * n
    stack = []
    for i in range(n):
        while stack and temps[i] > temps[stack[-1]]:
            j = stack.pop()
            res[j] = i - j
        stack.append(i)
    return res
SOLUTIONS["daily-temperatures"] = lambda args: _daily_temperatures(*args)

def _next_greater_i(nums1, nums2):
    ng = {}
    stack = []
    for n in nums2:
        while stack and n > stack[-1]:
            ng[stack.pop()] = n
        stack.append(n)
    return [ng.get(n, -1) for n in nums1]
SOLUTIONS["next-greater-element-i"] = lambda args: _next_greater_i(*args)

def _next_greater_ii(nums):
    n = len(nums)
    res = [-1] * n
    stack = []
    for i in range(2 * n):
        while stack and nums[i % n] > nums[stack[-1]]:
            res[stack.pop()] = nums[i % n]
        if i < n:
            stack.append(i)
    return res
SOLUTIONS["next-greater-element-ii"] = lambda args: _next_greater_ii(*args)

def _largest_rectangle(heights):
    stack = []
    res = 0
    for i, h in enumerate(heights + [0]):
        while stack and h < heights[stack[-1]]:
            height = heights[stack.pop()]
            width = i if not stack else i - stack[-1] - 1
            res = max(res, height * width)
        stack.append(i)
    return res
SOLUTIONS["largest-rectangle-in-histogram"] = lambda args: _largest_rectangle(*args)

def _sliding_window_max(nums, k):
    from collections import deque
    dq = deque()
    res = []
    for i, n in enumerate(nums):
        while dq and nums[dq[-1]] < n:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - k:
            dq.popleft()
        if i >= k - 1:
            res.append(nums[dq[0]])
    return res
SOLUTIONS["sliding-window-maximum"] = lambda args: _sliding_window_max(*args)

# ── two pointers ──

def _fruit_into_baskets(fruits):
    from collections import Counter
    count = Counter()
    l = 0
    res = 0
    for r in range(len(fruits)):
        count[fruits[r]] += 1
        while len(count) > 2:
            count[fruits[l]] -= 1
            if count[fruits[l]] == 0:
                del count[fruits[l]]
            l += 1
        res = max(res, r - l + 1)
    return res
SOLUTIONS["fruit-into-baskets"] = lambda args: _fruit_into_baskets(*args)

# ── graph ──

def _spiral_matrix(matrix):
    if not matrix: return []
    res = []
    t, b, l, r = 0, len(matrix) - 1, 0, len(matrix[0]) - 1
    while t <= b and l <= r:
        for j in range(l, r + 1): res.append(matrix[t][j])
        t += 1
        for i in range(t, b + 1): res.append(matrix[i][r])
        r -= 1
        if t <= b:
            for j in range(r, l - 1, -1): res.append(matrix[b][j])
            b -= 1
        if l <= r:
            for i in range(b, t - 1, -1): res.append(matrix[i][l])
            l += 1
    return res
SOLUTIONS["spiral-matrix"] = lambda args: _spiral_matrix(*args)

def _spiral_matrix_ii(n):
    res = [[0]*n for _ in range(n)]
    t, b, l, r = 0, n-1, 0, n-1
    num = 1
    while t <= b and l <= r:
        for j in range(l, r+1): res[t][j] = num; num += 1
        t += 1
        for i in range(t, b+1): res[i][r] = num; num += 1
        r -= 1
        for j in range(r, l-1, -1): res[b][j] = num; num += 1
        b -= 1
        for i in range(b, t-1, -1): res[i][l] = num; num += 1
        l += 1
    return res
SOLUTIONS["spiral-matrix-ii"] = lambda args: _spiral_matrix_ii(*args)

# ── trapping rain water ──

def _trapping_rain_water(height):
    l, r = 0, len(height) - 1
    l_max = r_max = 0
    water = 0
    while l < r:
        if height[l] < height[r]:
            if height[l] >= l_max: l_max = height[l]
            else: water += l_max - height[l]
            l += 1
        else:
            if height[r] >= r_max: r_max = height[r]
            else: water += r_max - height[r]
            r -= 1
    return water
SOLUTIONS["trapping-rain-water"] = lambda args: _trapping_rain_water(*args)

# ── minimum window substring ──

def _min_window_substring(s, t):
    from collections import Counter
    need = Counter(t)
    missing = len(t)
    l = 0
    start = 0
    end = float('inf')
    for r, c in enumerate(s):
        if need[c] > 0: missing -= 1
        need[c] -= 1
        if missing == 0:
            while l < r and need[s[l]] < 0:
                need[s[l]] += 1
                l += 1
            if r - l < end - start:
                start, end = l, r
            need[s[l]] += 1
            missing += 1
            l += 1
    return s[start:end+1] if end != float('inf') else ""
SOLUTIONS["minimum-window-substring"] = lambda args: _min_window_substring(*args)

# ── sorting ──

def _sorting_basic_output(arr):
    return sorted(arr)
SOLUTIONS["sorting-basic-output"] = lambda args: _sorting_basic_output(*args)

def _sorting_inversion_count(arr):
    def merge_count(arr):
        if len(arr) <= 1: return arr, 0
        mid = len(arr) // 2
        left, lc = merge_count(arr[:mid])
        right, rc = merge_count(arr[mid:])
        merged = []
        i = j = 0
        inv = lc + rc
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                merged.append(left[i]); i += 1
            else:
                merged.append(right[j]); j += 1
                inv += len(left) - i
        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged, inv
    _, count = merge_count(arr)
    return count
SOLUTIONS["sorting-inversion-count"] = lambda args: _sorting_inversion_count(*args)

def _sorting_kth_largest(arr, k):
    return sorted(arr, reverse=True)[k-1]
SOLUTIONS["sorting-kth-largest"] = lambda args: _sorting_kth_largest(*args)

# ── sudoku solver (特殊处理) ──

def _sudoku_solver(board):
    # 验证数独解的正确性
    def is_valid(board):
        for i in range(9):
            row = [x for x in board[i] if x != 0]
            col = [board[j][i] for j in range(9) if board[j][i] != 0]
            if len(row) != len(set(row)) or len(col) != len(set(col)):
                return False
        for bi in range(3):
            for bj in range(3):
                block = [board[bi*3+i][bj*3+j] for i in range(3) for j in range(3) if board[bi*3+i][bj*3+j] != 0]
                if len(block) != len(set(block)):
                    return False
        return True
    return is_valid(board)
SOLUTIONS["sudoku-solver"] = lambda args: _sudoku_solver(*args)


# ─── 验证逻辑 ───

def compare_result(expected, actual, slug=""):
    """比较 expected 和 actual，处理特殊情况"""
    # 处理 None
    if expected is None and actual is None:
        return True
    if expected is None or actual is None:
        return False

    # 处理浮点数
    if isinstance(expected, float) or isinstance(actual, float):
        return abs(expected - actual) < 1e-5

    # 处理列表
    if isinstance(expected, list) and isinstance(actual, list):
        if not expected and not actual:
            return True
        # 嵌套列表（如 level order）
        if expected and isinstance(expected[0], list):
            if len(expected) != len(actual):
                return False
            # 对于某些题目，内部列表需要排序比较
            order_insensitive_slugs = {
                "group-anagrams", "palindrome-partitioning", "subsets",
                "permutations", "permutations-ii", "combinations",
                "path-sum-ii", "binary-tree-paths",
            }
            if slug in order_insensitive_slugs:
                try:
                    return sorted(sorted(e) if isinstance(e, list) else [e] for e in expected) == \
                           sorted(sorted(a) if isinstance(a, list) else [a] for a in actual)
                except:
                    pass
            return expected == actual

        # 简单列表
        return expected == actual

    # 处理布尔值
    if isinstance(expected, bool) or isinstance(actual, bool):
        return bool(expected) == bool(actual)

    return expected == actual


def verify_all():
    """验证所有测试用例"""
    # 合并所有测试定义
    ALL = {**TEST_DEFINITIONS, **EXTRA_TEST_DEFINITIONS}

    # 应用 sample overrides
    for slug, override in SAMPLE_OVERRIDES.items():
        if slug in ALL:
            ALL[slug]["samples"] = override

    # 应用 hidden supplement
    for slug, extra in HIDDEN_SUPPLEMENT.items():
        if slug in ALL:
            hidden = list(ALL[slug].get("hidden") or [])
            hidden.extend(extra)
            ALL[slug]["hidden"] = hidden

    errors = []
    verified = 0
    skipped = 0

    for slug, cfg in sorted(ALL.items()):
        if slug not in SOLUTIONS:
            skipped += 1
            continue

        solver = SOLUTIONS[slug]
        all_cases = list(cfg.get("samples") or []) + list(cfg.get("hidden") or [])

        for i, case in enumerate(all_cases):
            args = case.get("args", [])
            expected = case.get("expected")

            try:
                actual = solver(args)
                if not compare_result(expected, actual, slug):
                    errors.append({
                        "slug": slug,
                        "case_idx": i,
                        "args": str(args)[:100],
                        "expected": expected,
                        "actual": actual,
                    })
            except Exception as e:
                errors.append({
                    "slug": slug,
                    "case_idx": i,
                    "args": str(args)[:100],
                    "expected": expected,
                    "actual": f"ERROR: {e}",
                })

            verified += 1

    print(f"验证完成: {verified} 个用例, {len(errors)} 个错误, {skipped} 个跳过")

    if errors:
        print("\n=== 错误详情 ===")
        for e in errors:
            print(f"\n{e['slug']} case[{e['case_idx']}]:")
            print(f"  args: {e['args']}")
            print(f"  expected: {e['expected']}")
            print(f"  actual: {e['actual']}")
    else:
        print("\n所有测试用例验证通过！")

    return errors


if __name__ == "__main__":
    errors = verify_all()
    sys.exit(1 if errors else 0)
