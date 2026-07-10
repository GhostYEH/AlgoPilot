"""学习效果掌握度 API。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.deps import get_current_user
from core.database import get_db
from models.db_models import User
from schemas.mastery import (
    MasteryRecalculateRequest,
    MasteryRecalculateResponse,
    MasteryReportResponse,
)
from services.mastery.mastery_service import MasteryService

router = APIRouter(prefix="/mastery", tags=["mastery"])


def _to_response(overview) -> MasteryReportResponse:
    return MasteryReportResponse(
        course_id=overview.course_id,
        overall_score=overview.overall_score,
        overall_level=overview.overall_level,
        report=overview.report,
        chapters=overview.chapters,
        updated_at=overview.updated_at,
    )


@router.get("/report", response_model=MasteryReportResponse)
def get_mastery_report(
    course_id: str = Query(default="data_structures_algorithms"),
    chapter_id: str = Query(default=""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MasteryReportResponse:
    overview = MasteryService(db).get_report(
        user.id,
        course_id=course_id,
        chapter_id=chapter_id,
    )
    return _to_response(overview)


@router.post("/recalculate", response_model=MasteryRecalculateResponse)
def recalculate_mastery(
    body: MasteryRecalculateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MasteryRecalculateResponse:
    overview = MasteryService(db).recalculate(
        user.id,
        course_id=body.course_id,
        chapter_id=body.chapter_id,
        modules=body.modules,
    )
    return MasteryRecalculateResponse(overview=_to_response(overview))
