"""学习效果统计与导出 API。"""

from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from api.deps import get_current_user
from core.database import get_db
from models.db_models import User
from services.analytics.effectiveness import (
    EffectivenessResponse,
    build_csv_rows,
    compute_effectiveness,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/effectiveness", response_model=EffectivenessResponse)
def get_effectiveness(
    course_id: str = Query(default="data_structures_algorithms"),
    chapter_id: str = Query(default=""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EffectivenessResponse:
    return compute_effectiveness(
        db,
        user.id,
        course_id=course_id,
        chapter_id=chapter_id,
    )


@router.get("/effectiveness/export.csv")
def export_effectiveness_csv(
    course_id: str = Query(default="data_structures_algorithms"),
    chapter_id: str = Query(default=""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = compute_effectiveness(
        db,
        user.id,
        course_id=course_id,
        chapter_id=chapter_id,
    )
    buf = io.StringIO()
    writer = csv.writer(buf)
    for row in build_csv_rows(data):
        writer.writerow(row)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=effectiveness_export.csv"},
    )
