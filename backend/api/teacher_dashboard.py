from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.deps import get_current_user
from core.database import get_db
from models.db_models import User
from schemas.teacher_dashboard import TeacherDashboardSummaryResponse
from services.teacher_dashboard.service import get_dashboard_summary

router = APIRouter(prefix="/teacher", tags=["teacher-dashboard"])


@router.get("/dashboard-summary", response_model=TeacherDashboardSummaryResponse)
def dashboard_summary(
    course_id: str = Query(default="data_structures_algorithms"),
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TeacherDashboardSummaryResponse:
    """比赛演示阶段对已登录用户开放，后续可在此依赖教师角色权限。"""
    return get_dashboard_summary(db, course_id=course_id)
