from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.deps import get_current_user
from core.database import get_db
from models.db_models import User
from schemas.teacher_dashboard import (
    ClassOverviewResponse,
    InterventionResponse,
    ResourceStatsResponse,
    WeakPointsResponse,
)
from services.teacher_dashboard.service import (
    get_class_overview,
    get_interventions,
    get_resource_stats,
    get_weak_points,
)

router = APIRouter(prefix="/teacher-dashboard", tags=["teacher-dashboard"])


@router.get("/class-overview", response_model=ClassOverviewResponse)
def api_class_overview(
    course_id: str = Query(default="data_structures_algorithms"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClassOverviewResponse:
    return get_class_overview(db)


@router.get("/weak-points", response_model=WeakPointsResponse)
def api_weak_points(
    course_id: str = Query(default="data_structures_algorithms"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WeakPointsResponse:
    return get_weak_points(db)


@router.get("/resource-stats", response_model=ResourceStatsResponse)
def api_resource_stats(
    course_id: str = Query(default="data_structures_algorithms"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResourceStatsResponse:
    return get_resource_stats(db)


@router.get("/interventions", response_model=InterventionResponse)
def api_interventions(
    course_id: str = Query(default="data_structures_algorithms"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InterventionResponse:
    return get_interventions(db)
