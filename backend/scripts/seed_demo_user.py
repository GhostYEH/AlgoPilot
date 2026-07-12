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
    # ── 1. 学习进度 ──
    progress = LearningProgress(
        user_id=user.id,
        payload=LEARNING_PROGRESS_PAYLOAD,
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
        # 检查是否已存在 demo 用户
        existing = db.query(User).filter(User.username == "demo").first()
        if existing:
            print("用户 demo 已存在（id={}），刷新其学习数据为链表反转薄弱初始状态。".format(existing.id))
            _refresh_demo_learning_data(db, existing)
            seed_teacher_demo(db)
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

        seed_teacher_demo(db)

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def seed_teacher_demo(db) -> None:
    """创建教师测试账号 teacher_demo / 123456（如已存在则跳过）。"""
    teacher_existing = db.query(User).filter(User.username == "teacher_demo").first()
    if teacher_existing:
        print(f"用户 teacher_demo 已存在（id={teacher_existing.id}），跳过创建。")
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


if __name__ == "__main__":
    seed()
