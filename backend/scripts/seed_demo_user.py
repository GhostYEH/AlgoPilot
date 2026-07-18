"""添加 demo 用户及展示用学习数据。

用法：在 backend/ 目录下执行
    python -m scripts.seed_demo_user
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# 确保能 import backend 包
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from core.database import Base, SessionLocal, engine
from models.db_models import (
    GeneratedResource,
    LearningEventLog,
    LearningPathPlan,
    LearningProgress,
    OjSubmission,
    StudentLearningMemory,
    StudentProfile,
    User,
)
from utils.security import hash_password

# ── 学习进度 payload（各模块小节完成状态） ──────────────────────────────

# 数组模块：全部完成
_ARRAY_SECTIONS = {
    "theory": True, "binary-search": True, "remove-element": True,
    "sorted-squares": True, "min-subarray": True, "spiral": True, "summary": True,
}

# 链表模块：大部分完成
_LINKED_LIST_SECTIONS = {
    "theory": True, "remove-elements": True, "design-list": True,
    "reverse": True, "swap-pairs": True, "remove-nth-from-end": True,
    "intersection": True, "cycle": False, "summary": False,
}

# 哈希表模块：完成一半
_HASH_TABLE_SECTIONS = {
    "theory": True, "valid-anagram": True, "intersection": True,
    "happy-number": True, "two-sum": True, "four-sum-ii": False,
    "ransom-note": False, "three-sum": False, "four-sum": False, "summary": False,
}

# 字符串模块：完成一半
_STRING_SECTIONS = {
    "theory": True, "reverse-string": True, "reverse-string-ii": True,
    "replace-space": True, "reverse-words": False, "left-rotate": False,
    "kmp": False, "repeated-substring": False, "summary": False,
}

# 双指针模块：完成部分
_TWO_POINTERS_SECTIONS = {
    "theory": True, "remove-element": True, "reverse-string": True,
    "replace-space": False, "reverse-words": False, "reverse-list": False,
    "remove-nth-from-end": False, "intersection": False, "cycle": False,
    "three-sum": False, "four-sum": False, "summary": False,
}

# 栈与队列模块：完成大部分
_STACK_QUEUE_SECTIONS = {
    "theory": True, "queue-by-stacks": True, "stack-by-queues": True,
    "valid-parentheses": True, "remove-adjacent": True, "eval-rpn": True,
    "sliding-window-max": True, "top-k-frequent": False, "summary": False,
}

# 排序模块：完成部分
_SORTING_SECTIONS = {
    "concepts": True, "basic": True, "merge": True,
    "quick": False, "heap": False, "trace": False, "practice": False, "summary": False,
}

# 二叉树模块：完成前半部分
_BINARY_TREE_SECTIONS = {
    "theory": True, "traversal-recursive": True, "traversal-iterative": True,
    "unified-traversal": True, "level-order": True, "invert-tree": True,
    "checkpoint-1": True, "symmetric-tree": True, "max-depth": True,
    "min-depth": False, "count-nodes": False, "balanced-tree": False,
    "all-paths": False, "checkpoint-2": False, "sum-left-leaves": False,
    "find-bottom-left": False, "path-sum": False, "build-tree-in-post": False,
    "maximum-binary-tree": False, "checkpoint-3": False, "merge-trees": False,
    "bst-search": False, "validate-bst": False, "bst-min-diff": False,
    "bst-modes": False, "lowest-common-ancestor": False, "checkpoint-4": False,
    "bst-lca": False, "bst-insert": False, "bst-delete": False,
    "bst-trim": False, "sorted-array-to-bst": False, "bst-to-greater-sum": False,
    "summary": False,
}

# 回溯模块：刚开始
_BACKTRACKING_SECTIONS = {
    "theory": True, "combinations": False, "permutations": False,
    "subsets": False, "n-queens": False, "sudoku": False,
    "palindrome-partition": False, "summary": False,
}

# 贪心模块：刚开始
_GREEDY_SECTIONS = {
    "theory": True, "assign-cookies": False, "non-overlapping-intervals": False,
    "jump-game": False, "gas-station": False, "stock-greedy": False, "summary": False,
}

# 动态规划模块：刚开始
_DP_SECTIONS = {
    "theory": True, "five-steps": False, "climbing-stairs": False,
    "knapsack-01": False, "unbounded-knapsack": False, "coin-change": False,
    "lis": False, "summary": False,
}

# 单调栈模块：未开始
_MONOTONIC_STACK_SECTIONS = {
    "theory": False, "daily-temperatures": False, "next-greater": False,
    "largest-rectangle": False, "trapping-rain": False, "summary": False,
}

# 图论模块：未开始
_GRAPH_SECTIONS = {
    "theory": False, "representation": False, "bfs": False,
    "dfs": False, "pitfalls": False, "practice": False, "summary": False,
}

LEARNING_PROGRESS_PAYLOAD = {
    "alp-array-section-done-v1": _ARRAY_SECTIONS,
    "alp-linked-list-section-done-v1": _LINKED_LIST_SECTIONS,
    "alp-hash-table-section-done-v1": _HASH_TABLE_SECTIONS,
    "alp-string-section-done-v1": _STRING_SECTIONS,
    "alp-two-pointers-section-done-v1": _TWO_POINTERS_SECTIONS,
    "alp-stack-queue-section-done-v1": _STACK_QUEUE_SECTIONS,
    "alp-sorting-section-done-v1": _SORTING_SECTIONS,
    "alp-binary-tree-section-done-v5": _BINARY_TREE_SECTIONS,
    "alp-backtracking-section-done-v1": _BACKTRACKING_SECTIONS,
    "alp-greedy-section-done-v1": _GREEDY_SECTIONS,
    "alp-dp-section-done-v1": _DP_SECTIONS,
    "alp-monotonic-stack-section-done-v1": _MONOTONIC_STACK_SECTIONS,
    "alp-graph-section-done-v1": _GRAPH_SECTIONS,
}


# ── 游戏化练习进度（学习打卡热力图数据源） ──────────────────────────────

GAME_PROGRESS_PAYLOAD_KEY = "alp_game_progress_v1"
HOME_ACTIVITY_PAYLOAD_KEY = "alp-home-activity-v1"

# (days_ago, game_id, level_id, game_title, level_title, module_key)
# 37 条通关记录分布在近 10 周内，前疏后密，呈现真实学习节奏；
# 登录后经 applyRemoteProgressPayload 写入 localStorage，
# 「我的学习」热力图即可展示近 10 周活跃度。
_DEMO_GAME_SCHEDULE: list[tuple[int, str, str, str, str, str]] = [
    # 数组（第 1 周，最远）
    (67, "binary-search", "find", "夹逼寻宝", "找目标", "array"),
    (65, "binary-search", "lower", "夹逼寻宝", "第一个 ≥ x", "array"),
    (62, "binary-search", "rotated", "夹逼寻宝", "旋转最小值", "array"),
    # 链表（第 2 周）
    (60, "linked-list-repair", "reverse", "断链修理工", "反转链表", "linked-list"),
    (58, "linked-list-repair", "delete", "断链修理工", "删除结点", "linked-list"),
    (55, "linked-list-repair", "cycle", "断链修理工", "龟兔赛跑", "linked-list"),
    # 哈希表（第 3 周）
    (53, "hash-locker", "basic", "快递柜取件", "入桶", "hash-table"),
    (51, "hash-locker", "chain", "快递柜取件", "拉链法", "hash-table"),
    (48, "hash-locker", "rehash", "快递柜取件", "扩容", "hash-table"),
    # 字符串（第 4 周）
    (46, "palindrome", "palindrome", "回文消消乐", "验证回文", "string"),
    (44, "palindrome", "kmp-next", "回文消消乐", "next 填空", "string"),
    # 双指针
    (41, "two-pointers-race", "dedup", "双指针赛跑", "有序去重", "two-pointers"),
    (39, "two-pointers-race", "sum", "双指针赛跑", "三数之和", "two-pointers"),
    (37, "two-pointers-race", "cycle", "双指针赛跑", "环检测", "two-pointers"),
    # 栈与队列（第 5 周）
    (35, "canteen-stack-queue", "stack", "食堂出餐口", "栈关", "stack-queue"),
    (33, "canteen-stack-queue", "queue", "食堂出餐口", "队列关", "stack-queue"),
    (30, "canteen-stack-queue", "dual-stack", "食堂出餐口", "双栈", "stack-queue"),
    (28, "canteen-stack-queue", "paren", "食堂出餐口", "括号接龙", "stack-queue"),
    (26, "canteen-stack-queue", "deque", "食堂出餐口", "窗口", "stack-queue"),
    # 二叉树（第 6 周）
    (24, "tree-cave", "traverse", "树洞探险", "遍历关", "binary-tree"),
    (22, "tree-cave", "bst", "树洞探险", "BST 关", "binary-tree"),
    (20, "tree-cave", "path", "树洞探险", "路径和", "binary-tree"),
    # 回溯（第 7 周）
    (18, "backtrack-room", "n4", "密室排列", "4 皇后", "backtracking"),
    (16, "backtrack-room", "perm", "密室排列", "全排列", "backtracking"),
    # 贪心
    (14, "greedy-courier", "jump", "贪心快递员", "跳跃游戏", "greedy"),
    (12, "greedy-courier", "interval", "贪心快递员", "会议室", "greedy"),
    # 动态规划（第 8 周）
    (10, "knapsack-lite", "knapsack", "背包小偷 Lite", "0/1 背包", "dp"),
    (9, "knapsack-lite", "rob", "背包小偷 Lite", "打家劫舍", "dp"),
    (7, "knapsack-lite", "stairs", "背包小偷 Lite", "爬楼梯", "dp"),
    # 图论（第 9 周）
    (6, "graph-explorer", "representation", "图岛探路员", "建图关", "graph"),
    (5, "graph-explorer", "bfs", "图岛探路员", "最短层序", "graph"),
    (3, "graph-explorer", "dfs", "图岛探路员", "深搜回溯", "graph"),
    # 综合 + 单调栈（最近 1 周）
    (2, "algo-detective", "dfs-queue", "算法侦探", "结构误用", "_global"),
    (2, "algo-detective", "bst-inorder", "算法侦探", "BST 验证", "_global"),
    (1, "algo-detective", "dp-order", "算法侦探", "DP 填表", "_global"),
    (0, "monotonic-barrier", "temp", "地震挡板", "每日温度", "monotonic-stack"),
    (0, "monotonic-barrier", "rect", "地震挡板", "最大矩形", "monotonic-stack"),
]


def _build_demo_game_progress_payload(now: datetime) -> dict:
    """构造 demo 用户的游戏化练习进度（alp_game_progress_v1）。

    含 37 条通关历史，clearedAt 按上海时区对齐到正确的日历日，
    登录后经 applyRemoteProgressPayload 写入 localStorage，
    「我的学习」热力图即可展示近 10 周活跃度。
    """
    # 以上海时区（UTC+8）的"今天"为基准，避免 UTC 晚间导致日历日错位
    shanghai_today = (now + timedelta(hours=8)).date()

    cleared_levels: dict[str, list[str]] = {}
    history: list[dict] = []

    for idx, (days_ago, gid, lid, gtitle, ltitle, mkey) in enumerate(_DEMO_GAME_SCHEDULE):
        cleared_levels.setdefault(gid, [])
        if lid not in cleared_levels[gid]:
            cleared_levels[gid].append(lid)

        target_date = shanghai_today - timedelta(days=days_ago)
        # 04:00 UTC = 12:00 上海时间，落在目标日历日中段，避免跨日
        cleared_at_dt = datetime(
            target_date.year, target_date.month, target_date.day,
            4, idx % 50, 0, tzinfo=timezone.utc,
        )
        cleared_at_ms = int(cleared_at_dt.timestamp() * 1000)

        history.append({
            "gameId": gid,
            "levelId": lid,
            "gameTitle": gtitle,
            "levelTitle": ltitle,
            "moduleKey": mkey,
            "clearedAt": cleared_at_ms,
        })

    # 历史按时间倒序（最近在前），与前端 getGameHistory 约定一致
    history.sort(key=lambda r: r["clearedAt"], reverse=True)
    return {"clearedLevels": cleared_levels, "history": history}


def _build_demo_home_activity_payload(now: datetime) -> dict:
    """构造首页学习活跃度数据（alp-home-activity-v1）。

    生成近 12 周（84 天）的活动记录，保证：
    - 近 7 天每天都有访问记录（visits ≥ 1），近 3 天还有解题记录
    - 近 12 周内游戏通关日有 solves，非通关的平日也有少量 visits
    - 数据格式与前端 homeActivityLog.ts 的 Record<string, ActivityDay> 一致
    """
    shanghai_today = (now + timedelta(hours=8)).date()

    # 收集游戏通关日（用于派生 solves）
    game_days: dict[str, int] = {}
    for days_ago, _gid, _lid, _gt, _lt, _mk in _DEMO_GAME_SCHEDULE:
        d = (shanghai_today - timedelta(days=days_ago)).isoformat()
        game_days[d] = game_days.get(d, 0) + 1

    activity: dict[str, dict] = {}
    for i in range(83, -1, -1):  # 从 83 天前到今天
        d = (shanghai_today - timedelta(days=i)).isoformat()
        visits = 0
        solves = 0

        if i < 7:
            # 近 7 天：每天都有访问，近 3 天还有解题
            visits = 1 + (i % 3)  # 1~3 次
            if i < 3:
                solves = 1 + (i % 2)  # 1~2 题
        elif i < 14:
            # 近 2 周：隔天有访问
            if i % 2 == 0:
                visits = 1 + (i % 2)

        # 通关日补充 solves
        if d in game_days:
            solves = max(solves, game_days[d])
            visits = max(visits, 2)  # 通关日至少 2 次访问

        if visits > 0 or solves > 0:
            activity[d] = {"date": d, "visits": visits, "solves": solves}

    return activity


# ── 4 个子数据写入函数（被 _write_demo_learning_data 调用，幂等） ──


def _write_demo_path_plan(db, user: User, now) -> None:
    """写入 demo 学生的学习路径规划（linked-list 标记为巩固节点）。"""
    path_plan = LearningPathPlan(
        user_id=user.id,
        summary="数组已完成，链表反转掌握度偏低（32），建议先巩固链表三指针循环不变量再推进栈队列与二叉树",
        rationale="根据掌握度缓存，ch02-linear-list 仅 32 分（beginner），且存在 reverse-linked-list 的 WA 失败记忆。"
                  "按课程依赖关系，应先插入链表反转巩固节点，完成 Trace 动画与边界练习后再推进后续模块。",
        next_module_key="linked-list",
        ordered_keys=[
            "array", "linked-list", "hash-table", "string", "two-pointers",
            "stack-queue", "sorting", "binary-tree", "backtracking",
            "greedy", "dp", "monotonic-stack", "graph",
        ],
        steps=[
            {"module_key": "array", "rank": 1, "reason": "已完成，可复习巩固", "phase": "foundation", "prerequisites": [], "difficulty": "入门", "is_remediation": False},
            {"module_key": "linked-list", "rank": 2, "reason": "掌握度 32，插入巩固节点：链表反转三指针循环不变量", "phase": "foundation", "prerequisites": ["array"], "difficulty": "入门", "is_remediation": True},
            {"module_key": "hash-table", "rank": 3, "reason": "进行中，建议优先推进", "phase": "foundation", "prerequisites": ["array"], "difficulty": "标准", "is_remediation": False},
            {"module_key": "string", "rank": 4, "reason": "进行中，建议优先推进", "phase": "foundation", "prerequisites": ["array"], "difficulty": "标准", "is_remediation": False},
            {"module_key": "two-pointers", "rank": 5, "reason": "进行中，建议优先推进", "phase": "technique", "prerequisites": ["array", "linked-list", "hash-table"], "difficulty": "标准", "is_remediation": False},
            {"module_key": "stack-queue", "rank": 6, "reason": "已完成，可复习巩固", "phase": "technique", "prerequisites": ["array"], "difficulty": "标准", "is_remediation": False},
            {"module_key": "sorting", "rank": 7, "reason": "进行中，建议优先推进", "phase": "technique", "prerequisites": ["array", "two-pointers"], "difficulty": "标准", "is_remediation": False},
            {"module_key": "binary-tree", "rank": 8, "reason": "当前推荐模块", "phase": "tree", "prerequisites": ["linked-list", "stack-queue"], "difficulty": "进阶", "is_remediation": False},
            {"module_key": "backtracking", "rank": 9, "reason": "课程规划中", "phase": "tree", "prerequisites": ["binary-tree"], "difficulty": "进阶", "is_remediation": False},
            {"module_key": "greedy", "rank": 10, "reason": "课程规划中", "phase": "advanced", "prerequisites": ["binary-tree"], "difficulty": "进阶", "is_remediation": False},
            {"module_key": "dp", "rank": 11, "reason": "课程规划中", "phase": "advanced", "prerequisites": ["greedy", "backtracking"], "difficulty": "进阶", "is_remediation": False},
            {"module_key": "monotonic-stack", "rank": 12, "reason": "课程规划中", "phase": "advanced", "prerequisites": ["stack-queue"], "difficulty": "进阶", "is_remediation": False},
            {"module_key": "graph", "rank": 13, "reason": "课程规划中", "phase": "advanced", "prerequisites": ["stack-queue", "binary-tree"], "difficulty": "进阶", "is_remediation": False},
        ],
        progress_snapshot=LEARNING_PROGRESS_PAYLOAD,
    )
    db.add(path_plan)


def _write_demo_memories(db, user: User, now) -> None:
    """写入 demo 学生的学习记忆（含 reverse-linked-list WA 失败记忆，链表反转薄弱）。"""
    memories = [
        StudentLearningMemory(
            user_id=user.id,
            course_id="data_structures_algorithms",
            chapter_id="ch02-linear-list",
            skill_id="array-two-pointer",
            problem_slug="binary-search",
            event_type="oj_wrong_answer",
            observed_error_pattern="二分查找区间定义混乱，[L,R]和[L,R)混用导致死循环",
            trace_summary="mid计算后R=mid而非R=mid-1，区间不缩小导致死循环",
            failed_strategy="使用左闭右开区间但写成了R=mid-1",
            successful_hint="统一使用[L,R]闭区间，while(L<=R)，R=mid-1",
            mastery_delta=-1,
            evidence_json={"attempts": 3, "error_type": "boundary_condition_error"},
        ),
        # 关键记忆：链表反转 WA 失败（pointer_update_error），对应掌握度低
        StudentLearningMemory(
            user_id=user.id,
            course_id="data_structures_algorithms",
            chapter_id="ch02-linear-list",
            skill_id="linked-list-manipulation",
            problem_slug="reverse-linked-list",
            event_type="oj_submit_fail",
            observed_error_pattern="链表反转 next 保存顺序错误，先覆盖 curr.next 再保存导致断链",
            trace_summary="curr.next = prev 先执行，nxt = curr.next 取到已被改写的 prev，链表断链",
            failed_strategy="先 curr.next = prev，后 nxt = curr.next",
            successful_hint="应先 nxt = curr.next 保存后继，再 curr.next = prev，最后推进 prev/curr",
            mastery_delta=-1,
            evidence_json={
                "attempts": 2,
                "verdict": "WA",
                "error_type": "pointer_update_error",
                "module_key": "linked-list",
            },
        ),
        StudentLearningMemory(
            user_id=user.id,
            course_id="data_structures_algorithms",
            chapter_id="ch05-tree-binary-tree",
            skill_id="tree-traversal",
            problem_slug="binary-tree-inorder-traversal",
            event_type="oj_wrong_answer",
            observed_error_pattern="迭代中序遍历栈操作顺序错误，先访问了根节点",
            trace_summary="应先一路向左入栈，再弹出访问，而非先访问根再入栈",
            failed_strategy="混淆了前序和中序的迭代写法",
            successful_hint="记住中序迭代口诀：一路向左入栈，弹出即访问，转向右子树",
            mastery_delta=-1,
            evidence_json={"attempts": 2, "error_type": "state_transition_error"},
        ),
        StudentLearningMemory(
            user_id=user.id,
            course_id="data_structures_algorithms",
            chapter_id="ch05-tree-binary-tree",
            skill_id="tree-traversal",
            problem_slug="binary-tree-level-order-traversal",
            event_type="oj_accepted",
            observed_error_pattern="",
            trace_summary="使用队列BFS实现层序遍历，正确处理了每层节点数",
            failed_strategy="",
            successful_hint="用for循环控制当前层size，保证分层输出",
            mastery_delta=2,
            evidence_json={"attempts": 1, "time_ms": 620},
        ),
        StudentLearningMemory(
            user_id=user.id,
            course_id="data_structures_algorithms",
            chapter_id="ch03-stack-queue",
            skill_id="stack-application",
            problem_slug="valid-parentheses",
            event_type="oj_accepted",
            observed_error_pattern="",
            trace_summary="使用栈匹配括号，遇到右括号检查栈顶",
            failed_strategy="",
            successful_hint="用map存储右括号到左括号的映射",
            mastery_delta=2,
            evidence_json={"attempts": 1, "time_ms": 320},
        ),
        StudentLearningMemory(
            user_id=user.id,
            course_id="data_structures_algorithms",
            chapter_id="ch11-dynamic-programming",
            skill_id="dp-state-design",
            problem_slug="climbing-stairs",
            event_type="oj_wrong_answer",
            observed_error_pattern="未使用动态规划，直接递归导致超时",
            trace_summary="递归树深度过大，存在大量重复计算",
            failed_strategy="直接递归f(n)=f(n-1)+f(n-2)",
            successful_hint="使用dp数组自底向上填表，或记忆化递归",
            mastery_delta=-2,
            evidence_json={"attempts": 4, "error_type": "time_complexity_issue"},
        ),
    ]
    db.add_all(memories)


def _write_demo_events(db, user: User, now) -> None:
    """写入 demo 学生的学习事件日志（含 reverse-linked-list WA 事件）。"""
    events = [
        LearningEventLog(
            event_id="evt-demo-001",
            user_id=user.id,
            event_type="section_done",
            course_id="data_structures_algorithms",
            chapter_id="ch02-linear-list",
            skill_id="array-two-pointer",
            payload={"module_key": "array", "section_id": "theory"},
            handled_by=["progress_tracker"],
            status="done",
            agent_logs=[],
            handler_errors=[],
            created_at=now - timedelta(days=28),
        ),
        LearningEventLog(
            event_id="evt-demo-002",
            user_id=user.id,
            event_type="section_done",
            course_id="data_structures_algorithms",
            chapter_id="ch02-linear-list",
            skill_id="array-binary-search",
            payload={"module_key": "array", "section_id": "binary-search"},
            handled_by=["progress_tracker"],
            status="done",
            agent_logs=[],
            handler_errors=[],
            created_at=now - timedelta(days=27),
        ),
        LearningEventLog(
            event_id="evt-demo-003",
            user_id=user.id,
            event_type="oj_submit",
            course_id="data_structures_algorithms",
            chapter_id="ch02-linear-list",
            skill_id="array-two-pointer",
            payload={"module_key": "array", "problem_slug": "binary-search", "verdict": "WA", "attempts": 3},
            handled_by=["struggle_detector", "memory_service"],
            status="done",
            agent_logs=[{"agent": "struggle_detector", "action": "detected_boundary_error"}],
            handler_errors=[],
            created_at=now - timedelta(days=26),
        ),
        # 关键事件：reverse-linked-list WA，触发 struggle_detector 与 pointer_update_error 检测
        LearningEventLog(
            event_id="evt-demo-004",
            user_id=user.id,
            event_type="oj_submit",
            course_id="data_structures_algorithms",
            chapter_id="ch02-linear-list",
            skill_id="linked-list-manipulation",
            payload={"module_key": "linked-list", "problem_slug": "reverse-linked-list", "verdict": "WA", "attempts": 2},
            handled_by=["struggle_detector", "memory_service"],
            status="done",
            agent_logs=[{"agent": "struggle_detector", "action": "detected_pointer_update_error"}],
            handler_errors=[],
            created_at=now - timedelta(days=22),
        ),
        LearningEventLog(
            event_id="evt-demo-005",
            user_id=user.id,
            event_type="section_done",
            course_id="data_structures_algorithms",
            chapter_id="ch03-stack-queue",
            skill_id="stack-application",
            payload={"module_key": "stack-queue", "section_id": "valid-parentheses"},
            handled_by=["progress_tracker"],
            status="done",
            agent_logs=[],
            handler_errors=[],
            created_at=now - timedelta(days=18),
        ),
        LearningEventLog(
            event_id="evt-demo-006",
            user_id=user.id,
            event_type="section_done",
            course_id="data_structures_algorithms",
            chapter_id="ch05-tree-binary-tree",
            skill_id="tree-traversal",
            payload={"module_key": "binary-tree", "section_id": "traversal-recursive"},
            handled_by=["progress_tracker"],
            status="done",
            agent_logs=[],
            handler_errors=[],
            created_at=now - timedelta(days=8),
        ),
        LearningEventLog(
            event_id="evt-demo-007",
            user_id=user.id,
            event_type="oj_submit",
            course_id="data_structures_algorithms",
            chapter_id="ch05-tree-binary-tree",
            skill_id="tree-traversal",
            payload={"module_key": "binary-tree", "problem_slug": "binary-tree-inorder-traversal", "verdict": "WA", "attempts": 2},
            handled_by=["struggle_detector", "memory_service"],
            status="done",
            agent_logs=[{"agent": "struggle_detector", "action": "detected_state_transition_error"}],
            handler_errors=[],
            created_at=now - timedelta(days=7),
        ),
        LearningEventLog(
            event_id="evt-demo-008",
            user_id=user.id,
            event_type="oj_submit",
            course_id="data_structures_algorithms",
            chapter_id="ch05-tree-binary-tree",
            skill_id="tree-traversal",
            payload={"module_key": "binary-tree", "problem_slug": "binary-tree-level-order-traversal", "verdict": "AC", "attempts": 1},
            handled_by=["progress_tracker"],
            status="done",
            agent_logs=[],
            handler_errors=[],
            created_at=now - timedelta(days=5),
        ),
        LearningEventLog(
            event_id="evt-demo-009",
            user_id=user.id,
            event_type="section_done",
            course_id="data_structures_algorithms",
            chapter_id="ch11-dynamic-programming",
            skill_id="dp-state-design",
            payload={"module_key": "dp", "section_id": "theory"},
            handled_by=["progress_tracker"],
            status="done",
            agent_logs=[],
            handler_errors=[],
            created_at=now - timedelta(days=2),
        ),
        LearningEventLog(
            event_id="evt-demo-010",
            user_id=user.id,
            event_type="oj_submit",
            course_id="data_structures_algorithms",
            chapter_id="ch11-dynamic-programming",
            skill_id="dp-state-design",
            payload={"module_key": "dp", "problem_slug": "climbing-stairs", "verdict": "TLE", "attempts": 4},
            handled_by=["struggle_detector", "memory_service", "persona_agent"],
            status="done",
            agent_logs=[
                {"agent": "struggle_detector", "action": "detected_time_complexity_issue"},
                {"agent": "persona_agent", "action": "updated_grit_level"},
            ],
            handler_errors=[],
            created_at=now - timedelta(days=1),
        ),
    ]
    db.add_all(events)


def _write_demo_resources(db, user: User) -> None:
    """写入 demo 学生的已生成资源（讲义/思维导图/练习题/代码案例/拓展资料）。"""
    resources = [
        GeneratedResource(
            user_id=user.id,
            resource_type="mindmap",
            agent_name="resource_mindmap",
            title="数组核心知识思维导图",
            content="# 数组核心知识\n## 内存模型\n- 连续存储\n- 随机访问O(1)\n## 二分查找\n- 闭区间[L,R]\n- 开区间[L,R)\n## 双指针\n- 快慢指针\n- 相向指针",
            meta={"module_key": "array", "chapter_id": "ch02-linear-list"},
        ),
        GeneratedResource(
            user_id=user.id,
            resource_type="document",
            agent_name="resource_doc",
            title="二叉树遍历方法对比与易错点总结",
            content="# 二叉树遍历方法对比\n## 递归遍历\n- 前序：中左右\n- 中序：左中右\n- 后序：左右中\n## 迭代遍历\n- 使用栈模拟递归\n- 中序：一路向左入栈，弹出即访问\n## 层序遍历\n- 使用队列BFS\n- for循环控制每层size\n## 常见错误\n1. 混淆前序和中序迭代写法\n2. 忘记处理空节点\n3. 层序遍历未分层",
            meta={"module_key": "binary-tree", "chapter_id": "ch05-tree-binary-tree"},
        ),
        GeneratedResource(
            user_id=user.id,
            resource_type="exercises",
            agent_name="resource_exercise",
            title="栈与队列专项练习题集",
            content="1. 有效的括号（简单）- 栈匹配\n2. 用栈实现队列（简单）- 双栈\n3. 逆波兰表达式求值（中等）- 栈计算\n4. 滑动窗口最大值（困难）- 单调队列\n5. 前K个高频元素（中等）- 优先队列",
            meta={"module_key": "stack-queue", "chapter_id": "ch03-stack-queue"},
        ),
    ]
    db.add_all(resources)


# ── 主入口：刷新 / 写入 demo 学习数据 ──────────────────────────────


# 自动化测试生成的临时账号用户名前缀（参见 backend/tests/*.py 中的 uuid.uuid4().hex[:N] 模式）
_TEST_USERNAME_PREFIXES: tuple[str, ...] = (
    "evt_", "evtapi_", "eff_", "effapi_", "effcsv_",
    "mem_", "memuser_", "mst_", "mstapi_",
    "replan_", "hdr_", "struggle_", "ojt_",
    "loop_", "core_loop_", "persona_", "fb_",
    "gameuser_", "svc_",
)


def _is_test_username(username: str) -> bool:
    """判断用户名是否为自动化测试生成的临时账号。

    匹配规则：<prefix>_<hex>，其中 hex 为 6/8/10 位十六进制字符串
    （对应 tests 中 uuid.uuid4().hex[:6/8/10] 三种用法）。
    """
    for prefix in _TEST_USERNAME_PREFIXES:
        if not username.startswith(prefix):
            continue
        suffix = username[len(prefix):]
        if len(suffix) in (6, 8, 10) and all(c in "0123456789abcdef" for c in suffix):
            return True
    return False


def _purge_test_students(db) -> int:
    """删除所有自动化测试生成的学生账号（保留 demo / teacher_demo / 真实学生）。"""
    students = db.query(User).filter(User.role == "student").all()
    deleted = 0
    for student in students:
        if student.username == "demo":
            continue
        if _is_test_username(student.username):
            db.delete(student)
            deleted += 1
    db.commit()
    return deleted


def _refresh_demo_learning_data(db, user: User) -> None:
    """demo 用户已存在时，刷新其学习数据为"链表反转掌握较弱"的固定初始状态。

    幂等：每次调用都会把画像、路径、记忆、事件、资源重置为演示初始状态，
    确保端到端闭环演示不依赖历史脏数据。
    """
    user_id = user.id

    # 清理旧演示数据（保留用户行本身）
    for model in (StudentProfile, LearningProgress, LearningPathPlan):
        db.query(model).filter(model.user_id == user_id).delete(synchronize_session=False)
    db.query(StudentLearningMemory).filter(StudentLearningMemory.user_id == user_id).delete(synchronize_session=False)
    db.query(LearningEventLog).filter(LearningEventLog.user_id == user_id).delete(synchronize_session=False)
    db.query(GeneratedResource).filter(GeneratedResource.user_id == user_id).delete(synchronize_session=False)
    db.commit()

    now = datetime.now(timezone.utc)
    _write_demo_learning_data(db, user, now)
    print(f"已刷新 demo 用户（id={user_id}）的学习数据为链表反转薄弱初始状态。")


def _write_demo_learning_data(db, user: User, now) -> None:
    """写入 demo 学生的固定初始学习数据（链表反转掌握较弱）。

    包含：学习进度、六维画像、学习路径、记忆、事件日志、生成资源。
    幂等：可重复调用，由调用方负责清理旧数据。
    """
    # ── 1. 学习进度（含游戏化练习历史 + 首页活动数据，作为热力图数据源） ──
    progress = LearningProgress(
        user_id=user.id,
        payload={
            **LEARNING_PROGRESS_PAYLOAD,
            GAME_PROGRESS_PAYLOAD_KEY: _build_demo_game_progress_payload(now),
            HOME_ACTIVITY_PAYLOAD_KEY: _build_demo_home_activity_payload(now),
        },
    )
    db.add(progress)

    # ── 2. 学生画像（六维） ──
    # 注：该 demo 学生固定为"链表反转掌握较弱"，用于端到端闭环演示。
    # _mastery_cache 必须按 chapter_id 建立，值为 dict 且包含 mastery_score，
    # 与 MasteryService._save_report_cache 写入格式保持一致，
    # 否则教师看板 / 学习路径 / 资源推荐读不到掌握度。
    profile = StudentProfile(
        user_id=user.id,
        summary="计科算法初学者，数组模块掌握良好，但在链表反转等指针操作题上反复出错，"
                "next 指针保存顺序与循环不变量理解待巩固。",
        dimensions={
            "knowledge_base": "已完成数组、哈希表、栈队列模块；链表反转三指针写法仍不稳定",
            "cognitive_style": "视觉型学习者，偏好图解和 Trace 动画理解指针变化",
            "coding_ability": "能独立完成基础题，链表反转等需要保存 next 的题目易写出断链代码",
            "learning_goals": "系统掌握数据结构与算法，优先攻克链表反转类题目",
            "error_preference": "近期易错/待加强：链表反转、next 指针保存顺序、循环不变量",
            "grit_level": "遇到难题会反复尝试，但连续失败3次以上容易放弃",
            # 注：分值范围为 1-10，与后端 _clamp_score / PersonaProfileResponse 约定一致
            "_dimension_scores": {
                "knowledge_base": 6,
                "cognitive_style": 7,
                "coding_ability": 4,
                "learning_goals": 8,
                "error_preference": 4,
                "grit_level": 6,
            },
            "_confidence": {
                "knowledge_base": 0.8,
                "cognitive_style": 0.7,
                "coding_ability": 0.75,
                "learning_goals": 0.9,
                "error_preference": 0.85,
                "grit_level": 0.65,
            },
            # 掌握度缓存：按 chapter_id 建立，值为 dict 且含 mastery_score
            "_mastery_cache": {
                "ch02-linear-list": {
                    "mastery_score": 32,
                    "mastery_level": "beginner",
                    "chapter_title": "线性表（顺序表与链表）",
                    "chapter_id": "ch02-linear-list",
                    "note": "链表反转 next 保存顺序错误，断链",
                },
                "ch03-stack-queue": {
                    "mastery_score": 78,
                    "mastery_level": "competent",
                    "chapter_title": "栈与队列",
                    "chapter_id": "ch03-stack-queue",
                },
                "ch04-string": {
                    "mastery_score": 44,
                    "mastery_level": "improving",
                    "chapter_title": "字符串与双指针",
                    "chapter_id": "ch04-string",
                },
                "ch05-tree-binary-tree": {
                    "mastery_score": 27,
                    "mastery_level": "beginner",
                    "chapter_title": "树与二叉树遍历",
                    "chapter_id": "ch05-tree-binary-tree",
                },
            },
            "_evaluation_history": [
                {"ts": (now - timedelta(days=25)).isoformat(), "overall_score": 40},
                {"ts": (now - timedelta(days=18)).isoformat(), "overall_score": 52},
                {"ts": (now - timedelta(days=10)).isoformat(), "overall_score": 48},
                {"ts": (now - timedelta(days=3)).isoformat(), "overall_score": 45},
            ],
        },
        chat_history=[],
    )
    db.add(profile)

    # ── 3-6. 路径 / 记忆 / 事件 / 资源 ──
    _write_demo_path_plan(db, user, now)
    _write_demo_memories(db, user, now)
    _write_demo_events(db, user, now)
    _write_demo_resources(db, user)
    db.commit()


def seed() -> None:
    # 建表（如果尚未创建）
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 0. 清理自动化测试生成的脏学生账号（保留 demo / teacher_demo / 真实学生）
        purged = _purge_test_students(db)
        if purged:
            print(f"已清理 {purged} 个自动化测试生成的临时学生账号。")

        # 检查是否已存在 demo 用户
        existing = db.query(User).filter(User.username == "demo").first()
        if existing:
            print("用户 demo 已存在（id={}），刷新其学习数据为链表反转薄弱初始状态。".format(existing.id))
            # 测试账号：强制重置密码为 123456，避免历史残留密码导致一键登录失败
            existing.hashed_password = hash_password("123456")
            db.commit()
            _refresh_demo_learning_data(db, existing)
            seed_teacher_demo(db)
            # 创建 6 名演示学生（教师看板花名册演示用）
            print("\n开始写入 6 名演示学生（教师看板花名册演示用）：")
            seed_extra_students(db)
            print("\n全部演示数据写入完成。")
            return

        # ── 1. 创建用户 ──
        now = datetime.now(timezone.utc)
        user = User(
            username="demo",
            email="demo@alp-learning.example",
            hashed_password=hash_password("123456"),
            role="student",
            created_at=now - timedelta(days=30),
        )
        db.add(user)
        db.flush()  # 拿到 user.id
        print(f"用户 demo 创建成功，id={user.id}")

        # ── 2. 学习进度 + 画像 + 路径 + 记忆 + 事件 + 资源（一次写入） ──
        _write_demo_learning_data(db, user, now)

        print("demo 用户及学习数据已成功写入数据库！")
        print(f"  用户名: demo")
        print(f"  密码: 123456")
        print(f"  角色: student")
        print(f"  固定薄弱点: 链表反转（ch02-linear-list 掌握度 32）")
        print(f"  学习进度: 13个模块（数组完成，链表反转待巩固）")
        print(f"  学生画像: 六维画像已填充（_mastery_cache 按 chapter_id 存储）")
        print(f"  学习路径: 已规划（linked-list 标记为巩固节点）")
        print(f"  学习记忆: 6条（含 reverse-linked-list WA 失败记忆）")
        print(f"  事件日志: 10条")
        print(f"  生成资源: 3条")
        print(f"  游戏通关历史: 37条（近 10 周分布，登录后写入热力图）")

        seed_teacher_demo(db)
        # 创建 6 名演示学生（教师看板花名册演示用）
        print("\n开始写入 6 名演示学生（教师看板花名册演示用）：")
        seed_extra_students(db)
        print("\n全部演示数据写入完成。")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def seed_teacher_demo(db) -> None:
    """创建教师测试账号 teacher_demo / 123456（如已存在则重置密码）。"""
    teacher_existing = db.query(User).filter(User.username == "teacher_demo").first()
    if teacher_existing:
        # 测试账号：强制重置密码为 123456，避免历史残留密码导致一键登录失败
        teacher_existing.hashed_password = hash_password("123456")
        db.commit()
        print(f"用户 teacher_demo 已存在（id={teacher_existing.id}），已重置密码为 123456。")
        return
    teacher = User(
        username="teacher_demo",
        email="teacher_demo@alp-learning.example",
        hashed_password=hash_password("123456"),
        role="teacher",
        created_at=datetime.now(timezone.utc) - timedelta(days=60),
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    print(f"用户 teacher_demo 创建成功，id={teacher.id}")
    print(f"  用户名: teacher_demo")
    print(f"  密码: 123456")
    print(f"  角色: teacher")


# ── 教师看板演示学生：6 名真实化人设 ──────────────────────────────
#
# 与 demo 用户配套使用：教师端「学情管理」页需要多名学生形成花名册，
# 6 名学生覆盖不同掌握度区间与薄弱模块，便于演示弱项聚合、教学建议、
# OJ 学情分析等功能。每个学生均含画像 + 进度 + 记忆 + 事件 + 资源 + OJ 提交，
# 确保详情抽屉「分模块掌握度 / 最近学习记录」均有内容。

# 章节标题映射（与 demo 用户保持一致，供 _mastery_cache 使用）
_CHAPTER_TITLES = {
    "ch01-introduction-complexity": "入门与复杂度分析",
    "ch02-linear-list": "线性表（顺序表与链表）",
    "ch03-stack-queue": "栈与队列",
    "ch04-string": "字符串",
    "ch05-tree-binary-tree": "树与二叉树",
    "ch06-graph": "图",
    "ch07-search": "查找（哈希表）",
    "ch08-sorting": "排序",
    "ch09-recursion-divide-conquer": "递归与分治",
    "ch10-greedy": "贪心",
    "ch11-dynamic-programming": "动态规划",
    "ch12-backtracking": "回溯",
    "ch13-advanced": "高级结构（单调栈等）",
}


def _mastery_entry(chapter_id: str, score: int) -> dict:
    """构造 _mastery_cache 中的单条目。"""
    level = (
        "mastered" if score >= 80
        else "competent" if score >= 60
        else "improving" if score >= 40
        else "beginner"
    )
    return {
        "mastery_score": score,
        "mastery_level": level,
        "chapter_title": _CHAPTER_TITLES.get(chapter_id, chapter_id),
        "chapter_id": chapter_id,
    }


def _module_progress_payload(done_modules: dict[str, dict[str, bool]]) -> dict:
    """根据已完成的模块小节，构造 LearningProgress.payload（含 13 个模块）。

    done_modules: { module_key: { section_id: True/False, ... } }
    未列出的模块按"全 False"填充，确保前端进度统计一致。
    """
    payload: dict[str, dict[str, bool]] = {}
    # 默认全 False 的模块键（与 LEARNING_PROGRESS_PAYLOAD 保持一致）
    default_sections = {
        "alp-array-section-done-v1": _ARRAY_SECTIONS,
        "alp-linked-list-section-done-v1": _LINKED_LIST_SECTIONS,
        "alp-hash-table-section-done-v1": _HASH_TABLE_SECTIONS,
        "alp-string-section-done-v1": _STRING_SECTIONS,
        "alp-two-pointers-section-done-v1": _TWO_POINTERS_SECTIONS,
        "alp-stack-queue-section-done-v1": _STACK_QUEUE_SECTIONS,
        "alp-sorting-section-done-v1": _SORTING_SECTIONS,
        "alp-binary-tree-section-done-v1": _BINARY_TREE_SECTIONS,
        "alp-backtracking-section-done-v1": _BACKTRACKING_SECTIONS,
        "alp-greedy-section-done-v1": _GREEDY_SECTIONS,
        "alp-dp-section-done-v1": _DP_SECTIONS,
        "alp-monotonic-stack-section-done-v1": _MONOTONIC_STACK_SECTIONS,
        "alp-graph-section-done-v1": _GRAPH_SECTIONS,
    }
    module_to_key = {
        "array": "alp-array-section-done-v1",
        "linked-list": "alp-linked-list-section-done-v1",
        "hash-table": "alp-hash-table-section-done-v1",
        "string": "alp-string-section-done-v1",
        "two-pointers": "alp-two-pointers-section-done-v1",
        "stack-queue": "alp-stack-queue-section-done-v1",
        "sorting": "alp-sorting-section-done-v1",
        "binary-tree": "alp-binary-tree-section-done-v1",
        "backtracking": "alp-backtracking-section-done-v1",
        "greedy": "alp-greedy-section-done-v1",
        "dp": "alp-dp-section-done-v1",
        "monotonic-stack": "alp-monotonic-stack-section-done-v1",
        "graph": "alp-graph-section-done-v1",
    }
    for mkey, payload_key in module_to_key.items():
        if mkey in done_modules:
            # 合并：以默认 sections 为基础，覆盖 done_modules 中指定的状态
            base = dict(default_sections[payload_key])
            base.update(done_modules[mkey])
            payload[payload_key] = base
        else:
            payload[payload_key] = dict(default_sections[payload_key])
    return payload


def _build_simple_home_activity(now: datetime, active_days_ago: list[int]) -> dict:
    """构造简化版首页活动数据：只在指定日期有 1~2 次访问 + 1 题解题。"""
    shanghai_today = (now + timedelta(hours=8)).date()
    activity: dict[str, dict] = {}
    for d_ago in active_days_ago:
        d = (shanghai_today - timedelta(days=d_ago)).isoformat()
        activity[d] = {"date": d, "visits": 2, "solves": 1}
    return activity


# 6 名演示学生的人设数据。每条 spec 含：
#   username, email, summary, created_days_ago, dimension_scores,
#   mastery_cache (chapter_id -> score), done_modules,
#   active_days (用于首页活动), memories, oj_submissions, resources
_EXTRA_STUDENT_SPECS: list[dict] = [
    # 1. 张明：中等水平，链表 + 二叉树薄弱（与 demo 同类但不同人设）
    {
        "username": "zhang_ming",
        "email": "zhang_ming@alp-learning.example",
        "summary": "计科大二学生，数组模块掌握良好，链表反转与二叉树迭代遍历反复出错，"
                   "需巩固指针操作与栈模拟递归的对应关系。",
        "created_days_ago": 28,
        "dimension_scores": {
            "knowledge_base": 6, "cognitive_style": 7, "coding_ability": 5,
            "learning_goals": 7, "error_preference": 5, "grit_level": 6,
        },
        "mastery_cache": {
            "ch02-linear-list": 35,
            "ch03-stack-queue": 65,
            "ch05-tree-binary-tree": 28,
            "ch04-string": 50,
            "ch01-introduction-complexity": 82,
        },
        "done_modules": {
            "array": {"theory": True, "binary-search": True, "remove-element": True,
                      "sorted-squares": True, "min-subarray": True, "spiral": True, "summary": True},
            "linked-list": {"theory": True, "remove-elements": True, "reverse": False, "summary": False},
            "stack-queue": {"theory": True, "valid-parentheses": True, "summary": False},
            "binary-tree": {"theory": True, "traversal-recursive": True, "traversal-iterative": False, "summary": False},
        },
        "active_days": [1, 2, 3, 5, 7, 10, 14, 18, 22, 25],
        "memories": [
            {
                "chapter_id": "ch02-linear-list", "skill_id": "linked-list-manipulation",
                "problem_slug": "reverse-linked-list", "event_type": "oj_submit_fail",
                "error_pattern": "链表反转 next 保存顺序错误，先覆盖 curr.next 再保存导致断链",
                "trace_summary": "curr.next = prev 先执行，nxt = curr.next 取到已被改写的 prev",
                "failed_strategy": "先 curr.next = prev，后 nxt = curr.next",
                "success_hint": "应先 nxt = curr.next 保存后继，再更新指向",
                "mastery_delta": -1,
                "evidence": {"attempts": 2, "verdict": "WA", "error_type": "pointer_update_error", "module_key": "linked-list"},
                "days_ago": 5,
            },
            {
                "chapter_id": "ch05-tree-binary-tree", "skill_id": "tree-traversal",
                "problem_slug": "binary-tree-inorder-traversal", "event_type": "oj_submit_fail",
                "error_pattern": "迭代中序遍历栈操作顺序错误，先访问根节点",
                "trace_summary": "应先一路向左入栈，再弹出访问",
                "failed_strategy": "混淆前序和中序的迭代写法",
                "success_hint": "中序迭代口诀：一路向左入栈，弹出即访问，转向右子树",
                "mastery_delta": -1,
                "evidence": {"attempts": 2, "verdict": "WA", "error_type": "state_transition_error", "module_key": "binary-tree"},
                "days_ago": 3,
            },
            {
                "chapter_id": "ch03-stack-queue", "skill_id": "stack-application",
                "problem_slug": "valid-parentheses", "event_type": "oj_accepted",
                "error_pattern": "", "trace_summary": "栈匹配括号正确",
                "failed_strategy": "", "success_hint": "右括号到栈顶左括号的映射",
                "mastery_delta": 2,
                "evidence": {"attempts": 1, "verdict": "AC", "module_key": "stack-queue"},
                "days_ago": 7,
            },
            {
                "chapter_id": "ch01-introduction-complexity", "skill_id": "array-two-pointer",
                "problem_slug": "binary-search", "event_type": "oj_accepted",
                "error_pattern": "", "trace_summary": "二分查找闭区间写法正确",
                "failed_strategy": "", "success_hint": "统一使用 [L,R] 闭区间",
                "mastery_delta": 2,
                "evidence": {"attempts": 1, "verdict": "AC", "module_key": "array"},
                "days_ago": 14,
            },
        ],
        "oj_submissions": [
            {"problem_slug": "reverse-linked-list", "verdict": "WA", "passed": 0, "total": 2, "days_ago": 5},
            {"problem_slug": "valid-parentheses", "verdict": "AC", "passed": 3, "total": 3, "days_ago": 7},
        ],
        "resources": [
            {
                "resource_type": "mindmap", "agent_name": "resource_mindmap",
                "title": "链表三指针操作思维导图",
                "content": "# 链表三指针操作\n## 反转链表\n- 保存 next\n- 更新 curr.next\n- 推进 prev/curr\n## 常见错误\n- 先覆盖 curr.next 导致断链",
                "meta": {"module_key": "linked-list", "chapter_id": "ch02-linear-list"},
            },
        ],
    },
    # 2. 李华：整体良好，DP 薄弱
    {
        "username": "li_hua",
        "email": "li_hua@alp-learning.example",
        "summary": "学习踏实，前 6 个模块掌握良好，但动态规划状态定义与转移方程推导薄弱，"
                   "爬楼梯 / 0-1 背包反复 TLE，需要从状态定义开始系统补强。",
        "created_days_ago": 35,
        "dimension_scores": {
            "knowledge_base": 8, "cognitive_style": 7, "coding_ability": 7,
            "learning_goals": 8, "error_preference": 6, "grit_level": 8,
        },
        "mastery_cache": {
            "ch01-introduction-complexity": 85,
            "ch02-linear-list": 75,
            "ch03-stack-queue": 78,
            "ch04-string": 70,
            "ch05-tree-binary-tree": 72,
            "ch08-sorting": 68,
            "ch11-dynamic-programming": 40,
        },
        "done_modules": {
            "array": {"theory": True, "binary-search": True, "remove-element": True,
                      "sorted-squares": True, "min-subarray": True, "spiral": True, "summary": True},
            "linked-list": {"theory": True, "remove-elements": True, "design-list": True,
                            "reverse": True, "swap-pairs": True, "summary": True},
            "stack-queue": {"theory": True, "queue-by-stacks": True, "stack-by-queues": True,
                            "valid-parentheses": True, "summary": True},
            "sorting": {"concepts": True, "basic": True, "merge": True, "summary": True},
            "binary-tree": {"theory": True, "traversal-recursive": True, "traversal-iterative": True,
                            "level-order": True, "summary": True},
            "dp": {"theory": True, "five-steps": False, "climbing-stairs": False, "summary": False},
        },
        "active_days": [0, 1, 2, 3, 5, 7, 9, 12, 15, 18, 22, 26, 30],
        "memories": [
            {
                "chapter_id": "ch11-dynamic-programming", "skill_id": "dp-state-design",
                "problem_slug": "climbing-stairs", "event_type": "oj_submit_fail",
                "error_pattern": "未使用动态规划，直接递归导致超时",
                "trace_summary": "递归树深度过大，存在大量重复计算",
                "failed_strategy": "直接递归 f(n)=f(n-1)+f(n-2)",
                "success_hint": "使用 dp 数组自底向上填表",
                "mastery_delta": -2,
                "evidence": {"attempts": 4, "verdict": "TLE", "error_type": "time_complexity_issue", "module_key": "dp"},
                "days_ago": 2,
            },
            {
                "chapter_id": "ch11-dynamic-programming", "skill_id": "dp-state-design",
                "problem_slug": "knapsack-01", "event_type": "oj_submit_fail",
                "error_pattern": "0-1 背包状态转移方程方向错误，倒序遍历写成顺序",
                "trace_summary": "dp[i][w] 应从 dp[i-1][w] 转移，顺序遍历导致物品重复选取",
                "failed_strategy": "顺序遍历 w 从 0 到 W",
                "success_hint": "0-1 背包必须倒序遍历 w 从 W 到 weight[i]",
                "mastery_delta": -1,
                "evidence": {"attempts": 3, "verdict": "WA", "error_type": "state_transition_error", "module_key": "dp"},
                "days_ago": 4,
            },
            {
                "chapter_id": "ch05-tree-binary-tree", "skill_id": "tree-traversal",
                "problem_slug": "binary-tree-level-order-traversal", "event_type": "oj_accepted",
                "error_pattern": "", "trace_summary": "BFS 层序遍历正确",
                "failed_strategy": "", "success_hint": "for 循环控制每层 size",
                "mastery_delta": 2,
                "evidence": {"attempts": 1, "verdict": "AC", "module_key": "binary-tree"},
                "days_ago": 8,
            },
            {
                "chapter_id": "ch03-stack-queue", "skill_id": "stack-application",
                "problem_slug": "valid-parentheses", "event_type": "oj_accepted",
                "error_pattern": "", "trace_summary": "栈匹配括号正确",
                "failed_strategy": "", "success_hint": "map 映射右括号到左括号",
                "mastery_delta": 2,
                "evidence": {"attempts": 1, "verdict": "AC", "module_key": "stack-queue"},
                "days_ago": 12,
            },
            {
                "chapter_id": "ch02-linear-list", "skill_id": "linked-list-manipulation",
                "problem_slug": "reverse-linked-list", "event_type": "oj_accepted",
                "error_pattern": "", "trace_summary": "三指针反转链表正确",
                "failed_strategy": "", "success_hint": "先保存 next 再更新指向",
                "mastery_delta": 2,
                "evidence": {"attempts": 1, "verdict": "AC", "module_key": "linked-list"},
                "days_ago": 18,
            },
            {
                "chapter_id": "ch01-introduction-complexity", "skill_id": "array-two-pointer",
                "problem_slug": "two-sum", "event_type": "oj_accepted",
                "error_pattern": "", "trace_summary": "哈希表一次遍历解法",
                "failed_strategy": "", "success_hint": "哈希表存储已遍历元素",
                "mastery_delta": 2,
                "evidence": {"attempts": 1, "verdict": "AC", "module_key": "array"},
                "days_ago": 25,
            },
        ],
        "oj_submissions": [
            {"problem_slug": "climbing-stairs", "verdict": "TLE", "passed": 0, "total": 3, "days_ago": 2},
            {"problem_slug": "knapsack-01", "verdict": "WA", "passed": 1, "total": 4, "days_ago": 4},
            {"problem_slug": "binary-tree-level-order-traversal", "verdict": "AC", "passed": 3, "total": 3, "days_ago": 8},
            {"problem_slug": "reverse-linked-list", "verdict": "AC", "passed": 3, "total": 3, "days_ago": 18},
        ],
        "resources": [
            {
                "resource_type": "document", "agent_name": "resource_doc",
                "title": "动态规划状态设计入门讲义",
                "content": "# DP 状态设计\n## 五步法\n1. 定义状态\n2. 推导转移方程\n3. 初始化\n4. 遍历顺序\n5. 举例推导\n## 常见错误\n- 0-1 背包顺序遍历导致重复选取",
                "meta": {"module_key": "dp", "chapter_id": "ch11-dynamic-programming"},
            },
            {
                "resource_type": "exercises", "agent_name": "resource_exercise",
                "title": "DP 入门题单",
                "content": "1. 爬楼梯（简单）\n2. 0-1 背包（中等）\n3. 不同路径（中等）\n4. 最长递增子序列（中等）",
                "meta": {"module_key": "dp", "chapter_id": "ch11-dynamic-programming"},
            },
        ],
    },
    # 3. 王芳：刚开始学习，栈队列不错
    {
        "username": "wang_fang",
        "email": "wang_fang@alp-learning.example",
        "summary": "数据结构初学者，刚完成数组和栈队列模块，栈与队列掌握较好，"
                   "其余模块刚开始接触，链表与二叉树尚无系统学习。",
        "created_days_ago": 14,
        "dimension_scores": {
            "knowledge_base": 4, "cognitive_style": 8, "coding_ability": 4,
            "learning_goals": 7, "error_preference": 5, "grit_level": 7,
        },
        "mastery_cache": {
            "ch01-introduction-complexity": 60,
            "ch02-linear-list": 25,
            "ch03-stack-queue": 75,
            "ch05-tree-binary-tree": 18,
        },
        "done_modules": {
            "array": {"theory": True, "binary-search": True, "remove-element": True, "summary": False},
            "stack-queue": {"theory": True, "queue-by-stacks": True, "stack-by-queues": True,
                            "valid-parentheses": True, "summary": True},
            "linked-list": {"theory": True, "summary": False},
        },
        "active_days": [0, 1, 2, 4, 7, 10],
        "memories": [
            {
                "chapter_id": "ch03-stack-queue", "skill_id": "stack-application",
                "problem_slug": "valid-parentheses", "event_type": "oj_accepted",
                "error_pattern": "", "trace_summary": "栈匹配括号正确",
                "failed_strategy": "", "success_hint": "右括号查栈顶左括号",
                "mastery_delta": 2,
                "evidence": {"attempts": 1, "verdict": "AC", "module_key": "stack-queue"},
                "days_ago": 1,
            },
            {
                "chapter_id": "ch02-linear-list", "skill_id": "linked-list-manipulation",
                "problem_slug": "reverse-linked-list", "event_type": "oj_submit_fail",
                "error_pattern": "链表节点指向更新顺序错误",
                "trace_summary": "未保存 next 直接修改 curr.next",
                "failed_strategy": "直接 curr.next = prev",
                "success_hint": "先保存 next 再修改指向",
                "mastery_delta": -1,
                "evidence": {"attempts": 2, "verdict": "WA", "error_type": "pointer_update_error", "module_key": "linked-list"},
                "days_ago": 4,
            },
            {
                "chapter_id": "ch01-introduction-complexity", "skill_id": "array-binary-search",
                "problem_slug": "binary-search", "event_type": "oj_accepted",
                "error_pattern": "", "trace_summary": "二分查找正确",
                "failed_strategy": "", "success_hint": "闭区间 [L,R] 写法",
                "mastery_delta": 2,
                "evidence": {"attempts": 1, "verdict": "AC", "module_key": "array"},
                "days_ago": 7,
            },
        ],
        "oj_submissions": [
            {"problem_slug": "valid-parentheses", "verdict": "AC", "passed": 3, "total": 3, "days_ago": 1},
        ],
        "resources": [
            {
                "resource_type": "mindmap", "agent_name": "resource_mindmap",
                "title": "栈与队列知识图",
                "content": "# 栈与队列\n## 栈\n- LIFO\n- 入栈出栈\n## 队列\n- FIFO\n- 入队出队",
                "meta": {"module_key": "stack-queue", "chapter_id": "ch03-stack-queue"},
            },
        ],
    },
    # 4. 赵磊：二叉树专家，字符串薄弱
    {
        "username": "zhao_lei",
        "email": "zhao_lei@alp-learning.example",
        "summary": "逻辑思维强，二叉树与递归类题目掌握扎实，但字符串 KMP 与双指针类题目薄弱，"
                   "需要在模式匹配与滑动窗口上专项突破。",
        "created_days_ago": 30,
        "dimension_scores": {
            "knowledge_base": 7, "cognitive_style": 6, "coding_ability": 7,
            "learning_goals": 8, "error_preference": 5, "grit_level": 7,
        },
        "mastery_cache": {
            "ch01-introduction-complexity": 75,
            "ch02-linear-list": 70,
            "ch03-stack-queue": 72,
            "ch04-string": 35,
            "ch05-tree-binary-tree": 88,
            "ch07-search": 60,
        },
        "done_modules": {
            "array": {"theory": True, "binary-search": True, "summary": True},
            "linked-list": {"theory": True, "reverse": True, "summary": True},
            "stack-queue": {"theory": True, "valid-parentheses": True, "summary": True},
            "binary-tree": {"theory": True, "traversal-recursive": True, "traversal-iterative": True,
                            "level-order": True, "invert-tree": True, "symmetric-tree": True,
                            "max-depth": True, "summary": True},
            "string": {"theory": True, "reverse-string": True, "summary": False},
        },
        "active_days": [1, 3, 5, 8, 11, 14, 18, 22, 26],
        "memories": [
            {
                "chapter_id": "ch04-string", "skill_id": "string-matching",
                "problem_slug": "implement-strstr", "event_type": "oj_submit_fail",
                "error_pattern": "KMP next 数组构造错误，未处理前缀与当前字符相等的情况",
                "trace_summary": "next[i] 应在 pattern[i-1] == pattern[next[i-1]] 时继续回退",
                "failed_strategy": "朴素匹配导致 TLE",
                "success_hint": "KMP next 数组：当字符相等时继续回退到 next[next[i-1]]",
                "mastery_delta": -1,
                "evidence": {"attempts": 3, "verdict": "WA", "error_type": "boundary_condition_error", "module_key": "string"},
                "days_ago": 3,
            },
            {
                "chapter_id": "ch04-string", "skill_id": "two-pointers",
                "problem_slug": "reverse-words-in-a-string", "event_type": "oj_submit_fail",
                "error_pattern": "双指针起止位置错误，多/少反转一个空格",
                "trace_summary": "right 应停在空格前一位，而非空格位置",
                "failed_strategy": "right 指针停在空格位置",
                "success_hint": "right 停在单词最后一个字符，再左移跳过空格",
                "mastery_delta": -1,
                "evidence": {"attempts": 2, "verdict": "WA", "error_type": "boundary_condition_error", "module_key": "string"},
                "days_ago": 5,
            },
            {
                "chapter_id": "ch05-tree-binary-tree", "skill_id": "tree-traversal",
                "problem_slug": "binary-tree-inorder-traversal", "event_type": "oj_accepted",
                "error_pattern": "", "trace_summary": "迭代中序遍历正确",
                "failed_strategy": "", "success_hint": "一路向左入栈，弹出即访问",
                "mastery_delta": 2,
                "evidence": {"attempts": 1, "verdict": "AC", "module_key": "binary-tree"},
                "days_ago": 8,
            },
            {
                "chapter_id": "ch05-tree-binary-tree", "skill_id": "tree-bst",
                "problem_slug": "validate-binary-search-tree", "event_type": "oj_accepted",
                "error_pattern": "", "trace_summary": "BST 验证使用区间递归",
                "failed_strategy": "", "success_hint": "传递 (min, max) 区间约束",
                "mastery_delta": 2,
                "evidence": {"attempts": 1, "verdict": "AC", "module_key": "binary-tree"},
                "days_ago": 12,
            },
        ],
        "oj_submissions": [
            {"problem_slug": "implement-strstr", "verdict": "WA", "passed": 1, "total": 4, "days_ago": 3},
            {"problem_slug": "binary-tree-inorder-traversal", "verdict": "AC", "passed": 3, "total": 3, "days_ago": 8},
            {"problem_slug": "validate-binary-search-tree", "verdict": "AC", "passed": 3, "total": 3, "days_ago": 12},
        ],
        "resources": [
            {
                "resource_type": "document", "agent_name": "resource_doc",
                "title": "二叉树遍历三种写法对比",
                "content": "# 二叉树遍历\n## 递归\n- 前序：中左右\n- 中序：左中右\n- 后序：左右中\n## 迭代\n- 中序：一路向左入栈\n## 层序\n- BFS 队列",
                "meta": {"module_key": "binary-tree", "chapter_id": "ch05-tree-binary-tree"},
            },
            {
                "resource_type": "exercises", "agent_name": "resource_exercise",
                "title": "字符串 KMP 专项练习",
                "content": "1. 实现 strStr()\n2. 重复的子字符串\n3. 最长公共前缀",
                "meta": {"module_key": "string", "chapter_id": "ch04-string"},
            },
        ],
    },
    # 5. 陈静：排序薄弱，其它中等
    {
        "username": "chen_jing",
        "email": "chen_jing@alp-learning.example",
        "summary": "学习态度认真，数组 / 链表 / 栈队列掌握中等，但排序算法稳定性与复杂度理解不清，"
                   "快排 partition 与归并合并写法常出错。",
        "created_days_ago": 22,
        "dimension_scores": {
            "knowledge_base": 6, "cognitive_style": 6, "coding_ability": 5,
            "learning_goals": 7, "error_preference": 5, "grit_level": 6,
        },
        "mastery_cache": {
            "ch01-introduction-complexity": 65,
            "ch02-linear-list": 55,
            "ch03-stack-queue": 60,
            "ch04-string": 50,
            "ch08-sorting": 30,
        },
        "done_modules": {
            "array": {"theory": True, "binary-search": True, "summary": True},
            "linked-list": {"theory": True, "reverse": True, "summary": False},
            "stack-queue": {"theory": True, "valid-parentheses": True, "summary": True},
            "sorting": {"concepts": True, "basic": False, "merge": False, "quick": False, "summary": False},
        },
        "active_days": [0, 2, 5, 8, 12, 16, 20],
        "memories": [
            {
                "chapter_id": "ch08-sorting", "skill_id": "sorting-quick",
                "problem_slug": "sort-colors", "event_type": "oj_submit_fail",
                "error_pattern": "三路 partition 边界错误，i 指针推进时机不当",
                "trace_summary": "遇到 1 时应 i++，遇到 2 时应与右指针交换不推进 i",
                "failed_strategy": "所有情况都 i++",
                "success_hint": "三路快排：0 与左指针换并 i++，1 直接 i++，2 与右指针换不推进",
                "mastery_delta": -1,
                "evidence": {"attempts": 3, "verdict": "WA", "error_type": "boundary_condition_error", "module_key": "sorting"},
                "days_ago": 2,
            },
            {
                "chapter_id": "ch08-sorting", "skill_id": "sorting-merge",
                "problem_slug": "merge-sorted-array", "event_type": "oj_submit_fail",
                "error_pattern": "归并合并从前往后扫描，覆盖了未处理的元素",
                "trace_summary": "应从后往前填充，避免覆盖 nums1 的未处理元素",
                "failed_strategy": "从前往后合并",
                "success_hint": "从后往前双指针填充，空间 O(1)",
                "mastery_delta": -1,
                "evidence": {"attempts": 2, "verdict": "WA", "error_type": "state_transition_error", "module_key": "sorting"},
                "days_ago": 5,
            },
            {
                "chapter_id": "ch03-stack-queue", "skill_id": "stack-application",
                "problem_slug": "valid-parentheses", "event_type": "oj_accepted",
                "error_pattern": "", "trace_summary": "栈匹配括号正确",
                "failed_strategy": "", "success_hint": "右括号查栈顶左括号",
                "mastery_delta": 2,
                "evidence": {"attempts": 1, "verdict": "AC", "module_key": "stack-queue"},
                "days_ago": 8,
            },
        ],
        "oj_submissions": [
            {"problem_slug": "sort-colors", "verdict": "WA", "passed": 1, "total": 3, "days_ago": 2},
        ],
        "resources": [
            {
                "resource_type": "document", "agent_name": "resource_doc",
                "title": "排序算法对比表",
                "content": "# 排序算法对比\n| 算法 | 平均 | 最坏 | 空间 | 稳定 |\n|---|---|---|---|---|\n| 快排 | O(nlogn) | O(n²) | O(logn) | 否 |\n| 归并 | O(nlogn) | O(nlogn) | O(n) | 是 |\n| 堆排 | O(nlogn) | O(nlogn) | O(1) | 否 |",
                "meta": {"module_key": "sorting", "chapter_id": "ch08-sorting"},
            },
        ],
    },
    # 6. 刘伟：刚起步，仅数组完成
    {
        "username": "liu_wei",
        "email": "liu_wei@alp-learning.example",
        "summary": "课程新生，仅完成数组模块，二分查找与双指针基本掌握，"
                   "其余模块刚开始接触，需要在链表 / 栈队列上投入更多时间。",
        "created_days_ago": 7,
        "dimension_scores": {
            "knowledge_base": 3, "cognitive_style": 6, "coding_ability": 3,
            "learning_goals": 8, "error_preference": 4, "grit_level": 7,
        },
        "mastery_cache": {
            "ch01-introduction-complexity": 70,
            "ch02-linear-list": 15,
            "ch03-stack-queue": 18,
        },
        "done_modules": {
            "array": {"theory": True, "binary-search": True, "remove-element": True, "summary": True},
            "linked-list": {"theory": False, "summary": False},
        },
        "active_days": [0, 1, 3, 5],
        "memories": [
            {
                "chapter_id": "ch02-linear-list", "skill_id": "linked-list-manipulation",
                "problem_slug": "reverse-linked-list", "event_type": "oj_submit_fail",
                "error_pattern": "链表反转 next 指针保存顺序错误",
                "trace_summary": "未保存 next 直接修改 curr.next 导致断链",
                "failed_strategy": "直接 curr.next = prev",
                "success_hint": "先 nxt = curr.next 保存后继",
                "mastery_delta": -1,
                "evidence": {"attempts": 2, "verdict": "WA", "error_type": "pointer_update_error", "module_key": "linked-list"},
                "days_ago": 1,
            },
            {
                "chapter_id": "ch01-introduction-complexity", "skill_id": "array-binary-search",
                "problem_slug": "binary-search", "event_type": "oj_accepted",
                "error_pattern": "", "trace_summary": "二分查找正确",
                "failed_strategy": "", "success_hint": "闭区间 [L,R] 写法",
                "mastery_delta": 2,
                "evidence": {"attempts": 1, "verdict": "AC", "module_key": "array"},
                "days_ago": 3,
            },
        ],
        "oj_submissions": [],
        "resources": [],
    },
]


def _write_extra_student(db, spec: dict, now: datetime) -> None:
    """根据 spec 写入一名演示学生及其全部学习数据（幂等：已存在则刷新）。"""
    username = spec["username"]

    # 清理旧数据（用户行本身保留，仅清关联表，便于保留 user.id 稳定）
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        user_id = existing.id
        for model in (StudentProfile, LearningProgress, LearningPathPlan,
                      StudentLearningMemory, LearningEventLog, GeneratedResource,
                      OjSubmission):
            db.query(model).filter(model.user_id == user_id).delete(synchronize_session=False)
        db.commit()
        user = existing
        # 强制重置密码，确保可用 123456 登录
        user.hashed_password = hash_password("123456")
        user.email = spec["email"]
        db.commit()
    else:
        user = User(
            username=username,
            email=spec["email"],
            hashed_password=hash_password("123456"),
            role="student",
            created_at=now - timedelta(days=spec["created_days_ago"]),
        )
        db.add(user)
        db.flush()

    # 1. 学习进度（含首页活动）
    progress = LearningProgress(
        user_id=user.id,
        payload={
            **_module_progress_payload(spec["done_modules"]),
            GAME_PROGRESS_PAYLOAD_KEY: {
                "clearedLevels": {},
                "history": [],
            },
            HOME_ACTIVITY_PAYLOAD_KEY: _build_simple_home_activity(now, spec["active_days"]),
        },
    )
    db.add(progress)

    # 2. 学生画像（六维 + 掌握度缓存）
    mastery_cache = {
        chapter_id: _mastery_entry(chapter_id, score)
        for chapter_id, score in spec["mastery_cache"].items()
    }
    scores = list(spec["mastery_cache"].values())
    overall = round(sum(scores) / len(scores), 1) if scores else 0.0
    profile = StudentProfile(
        user_id=user.id,
        summary=spec["summary"],
        dimensions={
            "knowledge_base": "见 _mastery_cache 各章掌握度",
            "cognitive_style": "图解 + Trace 动画学习者",
            "coding_ability": "见 OJ 提交记录",
            "learning_goals": "系统学习数据结构与算法",
            "error_preference": "见 recent_memories 失败模式",
            "grit_level": "见 _dimension_scores",
            "_dimension_scores": spec["dimension_scores"],
            "_mastery_cache": mastery_cache,
            "_evaluation_history": [
                {"ts": (now - timedelta(days=d)).isoformat(), "overall_score": overall}
                for d in (spec["created_days_ago"], max(1, spec["created_days_ago"] // 2), 1)
            ],
        },
        chat_history=[],
    )
    db.add(profile)

    # 3. 学习记忆（按 spec 中的 days_ago 设置 created_at）
    memories = []
    for m in spec["memories"]:
        memories.append(StudentLearningMemory(
            user_id=user.id,
            course_id="data_structures_algorithms",
            chapter_id=m["chapter_id"],
            skill_id=m["skill_id"],
            problem_slug=m["problem_slug"],
            event_type=m["event_type"],
            observed_error_pattern=m["error_pattern"],
            trace_summary=m["trace_summary"],
            failed_strategy=m["failed_strategy"],
            successful_hint=m["success_hint"],
            mastery_delta=m["mastery_delta"],
            evidence_json=m["evidence"],
            created_at=now - timedelta(days=m["days_ago"]),
        ))
    if memories:
        db.add_all(memories)

    # 4. OJ 提交记录
    oj_subs = []
    for o in spec["oj_submissions"]:
        oj_subs.append(OjSubmission(
            user_id=user.id,
            problem_slug=o["problem_slug"],
            language="python",
            code="",
            verdict=o["verdict"],
            passed=o["passed"],
            total=o["total"],
            compile_error="",
            cases=[],
            runtime_ms_avg=0,
            created_at=now - timedelta(days=o["days_ago"]),
        ))
    if oj_subs:
        db.add_all(oj_subs)

    # 5. 生成资源
    resources = []
    for r in spec["resources"]:
        resources.append(GeneratedResource(
            user_id=user.id,
            resource_type=r["resource_type"],
            agent_name=r["agent_name"],
            title=r["title"],
            content=r["content"],
            meta=r["meta"],
        ))
    if resources:
        db.add_all(resources)

    db.commit()


def seed_extra_students(db) -> None:
    """创建 6 名演示学生（如已存在则刷新学习数据），密码统一为 123456。"""
    now = datetime.now(timezone.utc)
    for spec in _EXTRA_STUDENT_SPECS:
        _write_extra_student(db, spec, now)
        print(f"  已写入演示学生：{spec['username']}（薄弱模块："
              f"{[m['evidence'].get('module_key') for m in spec['memories'] if m['event_type'] == 'oj_submit_fail']}）")


if __name__ == "__main__":
    seed()
