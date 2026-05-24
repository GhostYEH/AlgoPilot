from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.database import get_db
from models.db_models import User
from utils.security import safe_decode_user_id

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not cred or cred.scheme.lower() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "未登录或令牌无效")
    uid = safe_decode_user_id(cred.credentials)
    if uid is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "令牌已过期或无效")
    user = db.get(User, uid)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户不存在")
    return user


def get_optional_user(
    cred: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if not cred or cred.scheme.lower() != "bearer":
        return None
    uid = safe_decode_user_id(cred.credentials)
    if uid is None:
        return None
    return db.get(User, uid)
