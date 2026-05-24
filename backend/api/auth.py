from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from models.db_models import User
from schemas.auth import TokenResponse, UserLogin, UserOut, UserRegister
from utils.security import create_access_token, hash_password, verify_password

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
def register(body: UserRegister, db: Session = Depends(get_db)) -> TokenResponse:
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "用户名已被使用")
    if body.email and db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "邮箱已被使用")
    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user_id=user.id, username=user.username)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(body: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.username == body.username).first()
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户名或密码错误")
    token = create_access_token(user_id=user.id, username=user.username)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))
