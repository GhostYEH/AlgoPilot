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
from services.analytics.community import (
    build_ac_leaderboard,
    build_activity_feed,
    build_community_stats,
    build_streak_leaderboard,
)
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
    # 写入 UTF-8 BOM，避免 Excel 用 GBK 解码导致中文乱码
    buf.write("\ufeff")
    writer = csv.writer(buf)
    for row in build_csv_rows(data):
        writer.writerow(row)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=effectiveness_export.csv"},
    )


@router.get("/community")
def get_community(db: Session = Depends(get_db)) -> dict:
    """社区全站数据：公开接口，无需登录。返回统计、AC 榜、打卡榜、学习动态。"""
    stats = build_community_stats(db)
    ac_board = build_ac_leaderboard(db)
    streak_board = build_streak_leaderboard(db)
    feed = build_activity_feed(db)
    return {
        "stats": stats,
        "ac_board": ac_board,
        "streak_board": streak_board,
        "feed": feed,
    }
