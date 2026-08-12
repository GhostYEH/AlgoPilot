"""社区全站统计服务：聚合用户数、资源数、AC 榜、打卡榜、学习动态。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.db_models import GeneratedResource, LearningEventLog, User


def _avatar_hue(name: str) -> int:
    """根据用户名生成稳定的头像色相值。"""
    h = 0
    for ch in name:
        h = (h * 31 + ord(ch)) % 360
    return h


def _relative_time(ts: datetime) -> str:
    now = datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    diff = now - ts
    sec = int(diff.total_seconds())
    if sec < 60:
        return "刚刚"
    if sec < 3600:
        return f"{sec // 60} 分钟前"
    if sec < 86400:
        return f"{sec // 3600} 小时前"
    return f"{sec // 86400} 天前"


def build_community_stats(db: Session) -> dict:
    """全站统计：学生数、资源数、本周 AC 次数、本周活跃用户。"""
    student_count = (
        db.query(func.count(User.id)).filter(User.role == "student").scalar() or 0
    )
    resource_count = db.query(func.count(GeneratedResource.id)).scalar() or 0

    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    week_ac = (
        db.query(func.count(LearningEventLog.event_id))
        .filter(LearningEventLog.event_type.in_(("oj_submit_success", "oj_submit")))
        .filter(LearningEventLog.created_at >= week_ago)
        .scalar()
        or 0
    )
    week_active = (
        db.query(func.count(func.distinct(LearningEventLog.user_id)))
        .filter(LearningEventLog.created_at >= week_ago)
        .scalar()
        or 0
    )

    return {
        "student_count": student_count,
        "resource_count": resource_count,
        "week_ac_count": week_ac,
        "week_active_count": week_active,
    }


def build_ac_leaderboard(db: Session, limit: int = 8) -> list[dict]:
    """本周 AC 榜：按用户本周 AC 次数降序。"""
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    rows = (
        db.query(
            LearningEventLog.user_id,
            func.count(LearningEventLog.event_id).label("ac_count"),
        )
        .filter(LearningEventLog.event_type.in_(("oj_submit_success", "oj_submit")))
        .filter(LearningEventLog.created_at >= week_ago)
        .group_by(LearningEventLog.user_id)
        .order_by(func.count(LearningEventLog.event_id).desc())
        .limit(limit)
        .all()
    )
    if not rows:
        return []

    user_ids = [r.user_id for r in rows]
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    user_map = {u.id: u for u in users}

    board: list[dict] = []
    for idx, row in enumerate(rows):
        user = user_map.get(row.user_id)
        if not user:
            continue
        board.append(
            {
                "rank": idx + 1,
                "name": user.username,
                "avatarHue": _avatar_hue(user.username),
                "score": int(row.ac_count),
                "unit": "AC",
            }
        )
    return board


def build_streak_leaderboard(db: Session, limit: int = 8) -> list[dict]:
    """连续打卡榜：按用户连续学习天数（基于 learning_event_logs 的去重日期）降序。"""
    # 取最近 30 天内所有事件，按用户聚合去重日期计算连续天数
    thirty_ago = datetime.now(timezone.utc) - timedelta(days=30)
    rows = (
        db.query(
            LearningEventLog.user_id,
            func.date(LearningEventLog.created_at).label("day"),
        )
        .filter(LearningEventLog.created_at >= thirty_ago)
        .distinct()
        .all()
    )
    if not rows:
        return []

    # 按用户分组日期集合
    user_days: dict[int, set[str]] = {}
    for r in rows:
        user_days.setdefault(r.user_id, set()).add(str(r.day))

    # 计算每个用户的连续打卡天数（从今天往前数）
    today = datetime.now(timezone.utc).date()
    user_streaks: list[tuple[int, int]] = []
    for uid, days in user_days.items():
        streak = 0
        cur = today
        while str(cur) in days:
            streak += 1
            cur = cur - timedelta(days=1)
        user_streaks.append((uid, streak))

    user_streaks.sort(key=lambda x: x[1], reverse=True)
    top = user_streaks[:limit]
    if not top:
        return []

    user_ids = [uid for uid, _ in top]
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    user_map = {u.id: u for u in users}

    board: list[dict] = []
    for idx, (uid, streak) in enumerate(top):
        user = user_map.get(uid)
        if not user:
            continue
        board.append(
            {
                "rank": idx + 1,
                "name": user.username,
                "avatarHue": _avatar_hue(user.username),
                "score": streak,
                "unit": "天",
            }
        )
    return board


def build_activity_feed(db: Session, limit: int = 10) -> list[dict]:
    """学习动态：最近的学习事件流。"""
    rows = (
        db.query(LearningEventLog, User)
        .join(User, LearningEventLog.user_id == User.id)
        .order_by(LearningEventLog.created_at.desc())
        .limit(limit)
        .all()
    )

    feed: list[dict] = []
    for log, user in rows:
        action = _describe_event(log)
        if not action:
            continue
        feed.append(
            {
                "id": log.event_id,
                "user": user.username,
                "action": action,
                "time": _relative_time(log.created_at),
            }
        )
    return feed


def _describe_event(log: LearningEventLog) -> str:
    """将学习事件转为友好文案。"""
    et = log.event_type
    payload = log.payload or {}
    if et == "section_done":
        module_key = payload.get("module_key", "")
        section_id = payload.get("section_id", "")
        parts = [p for p in (module_key, section_id) if p]
        target = " · ".join(parts) if parts else "一个小节"
        return f"完成了 {target}"
    if et in ("oj_submit", "oj_submit_success"):
        slug = payload.get("problem_slug", "")
        return f"通过了 {slug}" if slug else "通过了一道题"
    if et in ("oj_submit_fail", "on_oj_submission_failed"):
        slug = payload.get("problem_slug", "")
        return f"提交 {slug} 未通过" if slug else "一道题未通过"
    if et == "on_resource_generated":
        module_key = payload.get("module_key", "")
        return f"生成了 {module_key} 资源" if module_key else "生成了个性化资源"
    if et == "on_quiz_completed":
        return "完成了章节测验"
    if et == "on_trace_diagnosed":
        slug = payload.get("problem_slug", "")
        return f"诊断了 {slug} 执行轨迹" if slug else "诊断了执行轨迹"
    if et == "on_mastery_recalculated":
        return "掌握度已更新"
    if et == "on_path_adjusted":
        return "学习路径已调整"
    return ""
