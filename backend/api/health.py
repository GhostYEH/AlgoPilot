"""健康检查与联调接口"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """前后端联调探活，返回固定 JSON。"""
    return {"status": "ok"}
