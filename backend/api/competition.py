from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_optional_user
from core.database import get_db
from models.db_models import User
from schemas.competition import LearningLoopSummary
from services.competition.learning_loop import build_learning_loop_summary

router = APIRouter(prefix="/competition", tags=["competition"])


@router.get("/learning-loop-summary", response_model=LearningLoopSummary)
def get_learning_loop_summary(
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> LearningLoopSummary:
    return LearningLoopSummary(**build_learning_loop_summary(db, user))
