from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.deps import require_teacher
from core.database import get_db
from models.db_models import User
from schemas.teacher_dashboard import (
    OjAnalyticsResponse,
    StudentDetailResponse,
    StudentRosterResponse,
    TeacherDashboardSummaryResponse,
)
from services.teacher_dashboard.service import (
    get_dashboard_summary,
    get_oj_analytics,
    get_student_detail,
    get_student_roster,
)

router = APIRouter(prefix="/teacher", tags=["teacher-dashboard"])


@router.get("/dashboard-summary", response_model=TeacherDashboardSummaryResponse)
def dashboard_summary(
    course_id: str = Query(default="data_structures_algorithms"),
    _user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> TeacherDashboardSummaryResponse:
    """汇总真实学生学习记录，仅教师账号可访问。"""
    return get_dashboard_summary(db, course_id=course_id)


@router.get("/students", response_model=StudentRosterResponse)
def student_roster(
    course_id: str = Query(default="data_structures_algorithms"),
    _user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> StudentRosterResponse:
    """获取全班学生花名册及关键学习指标，仅教师账号可访问。"""
    return get_student_roster(db, course_id=course_id)


@router.get("/students/{user_id}", response_model=StudentDetailResponse)
def student_detail(
    user_id: int,
    course_id: str = Query(default="data_structures_algorithms"),
    _user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> StudentDetailResponse:
    """获取单个学生的详细学情，仅教师账号可访问。"""
    result = get_student_detail(db, user_id, course_id=course_id)
    if result is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    return result


@router.get("/oj-analytics", response_model=OjAnalyticsResponse)
def oj_analytics(
    course_id: str = Query(default="data_structures_algorithms"),
    _user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> OjAnalyticsResponse:
    """获取全班 OJ 提交分析，仅教师账号可访问。"""
    return get_oj_analytics(db, course_id=course_id)
