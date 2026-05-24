from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_current_user
from core.database import get_db
from models.db_models import LearningProgress, User
from schemas.learning import LearningProgressOut, LearningProgressUpdate

router = APIRouter()

GAME_PROGRESS_KEY = "alp_game_progress_v1"


def _merge_section_maps(old: dict, new: dict) -> dict:
    out = dict(old)
    for k, v in new.items():
        if isinstance(v, bool):
            out[k] = bool(out.get(k)) or v
        else:
            out[k] = v
    return out


def _merge_game_progress(old: dict, new: dict) -> dict:
    old_cleared = dict(old.get("clearedLevels") or {})
    new_cleared = dict(new.get("clearedLevels") or {})
    merged_cleared: dict = {}
    for gid in set(old_cleared) | set(new_cleared):
        a = old_cleared.get(gid) or []
        b = new_cleared.get(gid) or []
        merged_cleared[gid] = list(dict.fromkeys([*(a if isinstance(a, list) else []), *(b if isinstance(b, list) else [])]))

    old_hist = old.get("history") or []
    new_hist = new.get("history") or []
    if not isinstance(old_hist, list):
        old_hist = []
    if not isinstance(new_hist, list):
        new_hist = []
    by_key: dict = {}
    for item in [*old_hist, *new_hist]:
        if not isinstance(item, dict):
            continue
        gid = item.get("gameId")
        lid = item.get("levelId")
        if not gid or not lid:
            continue
        key = f"{gid}:{lid}"
        prev = by_key.get(key)
        ts = item.get("clearedAt") or 0
        if not prev or ts > (prev.get("clearedAt") or 0):
            by_key[key] = item
    history = sorted(by_key.values(), key=lambda x: x.get("clearedAt") or 0, reverse=True)[:200]
    return {"clearedLevels": merged_cleared, "history": history}


def _merge_payload(old: dict, new: dict) -> dict:
    out = dict(old)
    for key, val in new.items():
        prev = out.get(key)
        if isinstance(prev, dict) and isinstance(val, dict):
            if key == GAME_PROGRESS_KEY:
                out[key] = _merge_game_progress(prev, val)
            else:
                out[key] = _merge_section_maps(prev, val)
        else:
            out[key] = val
    return out


@router.get("/learning-progress", response_model=LearningProgressOut)
def get_learning_progress(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LearningProgressOut:
    row = db.get(LearningProgress, user.id)
    if row is None:
        return LearningProgressOut(payload={})
    return LearningProgressOut(payload=dict(row.payload or {}))


@router.put("/learning-progress", response_model=LearningProgressOut)
def put_learning_progress(
    body: LearningProgressUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LearningProgressOut:
    row = db.get(LearningProgress, user.id)
    if row is None:
        row = LearningProgress(user_id=user.id, payload=dict(body.payload))
        db.add(row)
    else:
        row.payload = _merge_payload(dict(row.payload or {}), dict(body.payload))
    db.commit()
    db.refresh(row)
    return LearningProgressOut(payload=dict(row.payload or {}))
