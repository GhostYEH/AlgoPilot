import re
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from core.config import settings

CPP_SECURITY_MESSAGE = "安全系统拦截：代码包含违规的系统调用或头文件"

_DANGEROUS_HEADER_PATTERNS = (
    re.compile(r"#\s*include\s*[<\"]\s*cstdlib\s*[>\"]", re.IGNORECASE),
    re.compile(r"#\s*include\s*[<\"]\s*windows\.h\s*[>\"]", re.IGNORECASE),
    re.compile(r"#\s*include\s*[<\"]\s*unistd\.h\s*[>\"]", re.IGNORECASE),
    re.compile(r"#\s*include\s*[<\"]\s*fstream\s*[>\"]", re.IGNORECASE),
)

_DANGEROUS_CALL_PATTERNS = (
    re.compile(r"\bsystem\s*\(", re.IGNORECASE),
    re.compile(r"\bpopen\s*\(", re.IGNORECASE),
    re.compile(r"\bfork\s*\(", re.IGNORECASE),
    re.compile(r"\bexec(?:v|ve|vp|vpe|vep|l|le|lp|lpe|p|pe)?\s*\(", re.IGNORECASE),
    re.compile(r"\bsyscall\s*\(", re.IGNORECASE),
    re.compile(r"\b__asm__\b", re.IGNORECASE),
    re.compile(r"\basm\s*\(", re.IGNORECASE),
)


class CppSecurityViolation(Exception):
    """用户 C++ 代码命中静态安全规则时抛出。"""


def check_cpp_security(code: str) -> None:
    """基于正则的 C++ 静态安全拦截（Docker 沙箱接入前的第一道防线）。"""
    if not code or not code.strip():
        return
    for pattern in _DANGEROUS_HEADER_PATTERNS:
        if pattern.search(code):
            raise CppSecurityViolation(CPP_SECURITY_MESSAGE)
    for pattern in _DANGEROUS_CALL_PATTERNS:
        if pattern.search(code):
            raise CppSecurityViolation(CPP_SECURITY_MESSAGE)


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(*, user_id: int, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "username": username, "exp": int(expire.timestamp())}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def safe_decode_user_id(token: str) -> int | None:
    try:
        data = decode_token(token)
        return int(data.get("sub", 0))
    except (JWTError, ValueError, TypeError):
        return None
