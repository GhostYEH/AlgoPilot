"""Student Knowledge State 更新服务。

AlgoPilot 核心创新：Bug → Knowledge Point → 掌握度更新。
不是简单的 AC+10/WA-10，而是综合：
  - 题目难度
  - 历史表现
  - 是否第一次 AC
  - 修改次数（attempt_count）
  - Bug 类型（重复相同 Bug 降权）
  - Hint Level（使用越高级别提示，独立掌握度越低）
  - 是否独立完成

mastery 和 confidence 分开维护：
  - mastery: 知识掌握程度（基于成功率）
  - confidence: 置信度（基于样本量）
"""

from __future__ import annotations

import logging
from sqlalchemy.orm import Session

from models.db_models import StudentKnowledgeState

_logger = logging.getLogger(__name__)

_MASTERY_MIN = 0.0
_MASTERY_MAX = 100.0
_CONFIDENCE_MIN = 0.0
_CONFIDENCE_MAX = 100.0

_DIFFICULTY_WEIGHT = {"easy": 1.0, "medium": 1.5, "hard": 2.0}
_HINT_PENALTY = {0: 0.0, 1: 5.0, 2: 12.0, 3: 20.0, 4: 30.0}
_MAX_RECENT_BUG_TYPES = 5
_MAX_APPLIED_EVIDENCE = 50
_EVIDENCE_SUBMISSION = "SUBMISSION_RESULT"
_EVIDENCE_DIAGNOSIS = "DIAGNOSIS_BUG"
_EVIDENCE_HINT = "HINT_USAGE"


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _confidence_from_samples(attempt_count: int) -> float:
    """样本量越大置信度越高，但增速递减。

    1 次 → 20, 3 次 → 45, 5 次 → 60, 10 次 → 80, 20+ 次 → 95
    """
    if attempt_count <= 0:
        return 0.0
    return _clamp(100.0 * (1.0 - 1.0 / (1.0 + attempt_count / 3.0)), 0.0, 95.0)


def update_knowledge_state(
    db: Session,
    *,
    user_id: int,
    module_key: str,
    concept_id: str = "",
    knowledge_point: str = "",
    verdict: str = "WA",
    bug_type: str = "",
    hint_level_used: int = 0,
    difficulty: str = "medium",
    is_first_ac: bool = False,
    is_independent: bool = True,
    submission_id: int | None = None,
    evidence_type: str = _EVIDENCE_SUBMISSION,
) -> StudentKnowledgeState | None:
    """更新学生知识状态。

    幂等机制：同一个 (submission_id, evidence_type) 不会重复应用。
    不同 evidence_type 对同一次提交可以分别应用：
      - SUBMISSION_RESULT: 提交结果（AC/WA）→ 更新 attempt/success/mastery
      - DIAGNOSIS_BUG: AI 诊断 Bug → 更新 bug_type/recent_bugs/mastery
      - HINT_USAGE: 提示使用 → 更新 hint_usage/mastery

    Args:
        verdict: AC / WA / RE / TLE / CE
        bug_type: 本次 Bug 类型（用于检测重复 Bug）
        hint_level_used: 使用的最高提示级别（0=未用提示）
        difficulty: easy / medium / hard
        is_first_ac: 是否第一次 AC（首次 AC 加权）
        is_independent: 是否独立完成（未看提示或只看 L1）
        submission_id: 关联的提交 ID（用于幂等）
        evidence_type: 证据类型（用于幂等）

    Returns:
        更新后的 StudentKnowledgeState，失败返回 None。
        如果 (submission_id, evidence_type) 已应用过，返回现有记录（幂等跳过）。
    """
    if not module_key and not concept_id:
        return None

    try:
        record = (
            db.query(StudentKnowledgeState)
            .filter(
                StudentKnowledgeState.user_id == user_id,
                StudentKnowledgeState.module_key == module_key,
                StudentKnowledgeState.concept_id == concept_id,
            )
            .first()
        )

        if record is None:
            record = StudentKnowledgeState(
                user_id=user_id,
                module_key=module_key,
                concept_id=concept_id,
                knowledge_point=knowledge_point,
                mastery=0.0,
                confidence=0.0,
                attempt_count=0,
                success_count=0,
                independent_success_count=0,
                hint_usage=0,
                recent_bug_types=[],
                applied_evidence=[],
            )
            db.add(record)

        # 幂等检查：同一个 (submission_id, evidence_type) 不重复应用
        if submission_id is not None:
            evidence_key = f"{submission_id}:{evidence_type}"
            applied = list(record.applied_evidence or [])
            if evidence_key in applied:
                db.commit()
                db.refresh(record)
                return record

        is_ac = verdict == "AC" and evidence_type == _EVIDENCE_SUBMISSION
        repeated_bug = bool(bug_type and bug_type in record.recent_bug_types)

        if evidence_type == _EVIDENCE_SUBMISSION:
            record.attempt_count += 1
            if is_ac:
                record.success_count += 1
                if is_independent:
                    record.independent_success_count += 1
        elif evidence_type == _EVIDENCE_HINT:
            record.hint_usage += hint_level_used

        if bug_type and bug_type != "unknown":
            recent_bugs = list(record.recent_bug_types or [])
            recent_bugs.append(bug_type)
            recent_bugs = recent_bugs[-_MAX_RECENT_BUG_TYPES:]
            record.recent_bug_types = recent_bugs

        success_rate = record.success_count / record.attempt_count if record.attempt_count else 0.0

        diff_weight = _DIFFICULTY_WEIGHT.get(difficulty, 1.0)
        base_mastery = success_rate * 100.0

        if is_ac:
            ac_bonus = 10.0 * diff_weight
            if is_first_ac:
                ac_bonus *= 1.5
            if is_independent:
                ac_bonus *= 1.2
            target_mastery = base_mastery + ac_bonus
        else:
            hint_penalty = _HINT_PENALTY.get(hint_level_used, 0.0)
            repeated_penalty = 8.0 if repeated_bug else 0.0
            target_mastery = base_mastery - hint_penalty - repeated_penalty

        alpha = 0.3
        record.mastery = _clamp(
            record.mastery * (1.0 - alpha) + target_mastery * alpha,
            _MASTERY_MIN,
            _MASTERY_MAX,
        )

        record.confidence = _confidence_from_samples(record.attempt_count)

        # 记录已应用的证据
        if submission_id is not None:
            evidence_key = f"{submission_id}:{evidence_type}"
            applied = list(record.applied_evidence or [])
            applied.append(evidence_key)
            record.applied_evidence = applied[-_MAX_APPLIED_EVIDENCE:]

        db.commit()
        db.refresh(record)
        return record

    except Exception:
        db.rollback()
        _logger.exception(
            "update_knowledge_state 失败 user=%s module=%s concept=%s",
            user_id,
            module_key,
            concept_id,
        )
        return None


def get_knowledge_state(
    db: Session,
    user_id: int,
    module_key: str,
    concept_id: str = "",
) -> StudentKnowledgeState | None:
    """查询学生某知识点的当前状态。"""
    return (
        db.query(StudentKnowledgeState)
        .filter(
            StudentKnowledgeState.user_id == user_id,
            StudentKnowledgeState.module_key == module_key,
            StudentKnowledgeState.concept_id == concept_id,
        )
        .first()
    )
