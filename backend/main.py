"""
算法智能学习平台 — FastAPI 入口
扩展：账号体系、学习进度（MySQL）、后续 LangChain / 星火等
"""

from contextlib import asynccontextmanager
import logging
import os
import runpy
import sys
from pathlib import Path


def _handle_exec_script() -> None:
    """PyInstaller 打包后 sys.executable 指向 AlgoPilot.exe，
    子进程无法直接用它执行 Python 脚本。通过 --exec-script 参数
    让打包后的 exe 充当 Python 解释器运行指定脚本。"""
    if len(sys.argv) >= 3 and sys.argv[1] == "--exec-script":
        script_path = sys.argv[2]
        extra_args = sys.argv[3:]
        # 将脚本所在目录加入 sys.path，确保同目录模块可被 import
        script_dir = str(Path(script_path).resolve().parent)
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        sys.argv = [script_path, *extra_args]
        try:
            runpy.run_path(script_path, run_name="__main__")
        except SystemExit:
            raise
        except Exception as e:
            print(f"[exec-script error] {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)


# 在模块加载最早期处理 --exec-script，避免启动 FastAPI
_handle_exec_script()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.ai_tutor import router as ai_tutor_router
from api.oj_assistant import router as oj_assistant_router
from api.orchestrator import router as orchestrator_router
from api.auth import router as auth_router
from api.health import router as health_router
from api.learning import router as learning_router
from api.oj import router as oj_router
from api.oj_admin import router as oj_admin_router
from api.search import router as search_router
from api.skills import router as skills_router
from api.memory import router as memory_router
from api.mastery import router as mastery_router
from api.events import router as events_router
from api.analytics import router as analytics_router
from api.teacher_dashboard import router as teacher_dashboard_router
from core.config import settings
from core.database import engine

_logger = logging.getLogger(__name__)

_INSECURE_JWT_SECRETS = frozenset(
    {
        "dev-change-me-use-long-random-string",
        "changeme",
        "secret",
        "jwt-secret",
        "test",
    }
)


def _check_jwt_secret() -> None:
    """在应用启动前校验 JWT_SECRET，生产环境拒绝不安全默认值。"""
    if settings.jwt_secret not in _INSECURE_JWT_SECRETS:
        return
    if settings.is_production:
        _logger.critical(
            "JWT_SECRET 使用了不安全的默认值且检测到生产环境，拒绝启动。请在 .env 中设置一个长随机字符串。"
        )
        sys.exit(1)
    _logger.warning("JWT_SECRET 使用了不安全的默认值，仅限本地开发使用，请勿部署到生产环境。")


def _check_oj_execution_mode() -> None:
    """阻止生产服务退回到宿主机子进程判题。

    ``local`` 模式仅适合单机开发和桌面版；生产环境必须由独立的
    sandbox worker 接管代码执行。当前进程不把正则或 AST 审计当成
    隔离边界，因此在 worker 接入前宁可拒绝启动。
    """
    if settings.is_production:
        _logger.critical(
            "内置 OJ 判题器只能在受控本机开发环境运行。生产环境必须改接隔离 "
            "sandbox worker；当前服务拒绝以宿主机子进程方式启动。"
        )
        sys.exit(1)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _check_jwt_secret()
    _check_oj_execution_mode()

    from core.schema_migrations import upgrade_schema

    upgrade_schema(engine)

    # 数据自愈：把旧格式学习路径计划 steps 升级为新格式，避免 schema 演进导致 500
    try:
        from core.database import SessionLocal
        from services.orchestrator.core import migrate_legacy_learning_path_plans

        with SessionLocal() as session:
            migrate_legacy_learning_path_plans(session)
    except Exception:
        _logger.warning("学习路径计划数据迁移失败", exc_info=True)

    yield


app = FastAPI(title="算法智能学习平台 API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(orchestrator_router, prefix="/api/orchestrator", tags=["orchestrator"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(learning_router, prefix="/api/me", tags=["learning"])
app.include_router(ai_tutor_router, prefix="/api/ai", tags=["ai"])
app.include_router(oj_assistant_router, prefix="/api/ai/oj", tags=["ai-oj"])
app.include_router(oj_router, prefix="/api", tags=["oj"])
app.include_router(oj_admin_router, prefix="/api", tags=["oj-admin"])
app.include_router(search_router, prefix="/api/search", tags=["search"])
app.include_router(skills_router, prefix="/api")
app.include_router(memory_router, prefix="/api")
app.include_router(mastery_router, prefix="/api")
app.include_router(events_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(teacher_dashboard_router, prefix="/api")

# --- 内嵌前端静态文件（打包部署时使用） ---
_FRONTEND_DIR: Path | None = None
if getattr(sys, "frozen", False):
    # PyInstaller 打包后：_internal/frontend/ 目录
    _FRONTEND_DIR = Path(sys.executable).parent / "_internal" / "frontend"
else:
    # 开发模式：项目根目录 frontend/dist
    _FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if _FRONTEND_DIR and _FRONTEND_DIR.is_dir() and (_FRONTEND_DIR / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=str(_FRONTEND_DIR / "assets")), name="static-assets")

    @app.get("/{full_path:path}")
    async def _serve_spa(full_path: str):
        """SPA fallback：非 /api 路径和非静态文件均返回 index.html；
        以 /api 开头但不匹配任何已注册路由的路径返回 404 JSON。"""
        if full_path and full_path.startswith("api"):
            from fastapi.responses import JSONResponse

            return JSONResponse({"detail": "Not Found"}, status_code=404)
        if full_path:
            candidate = _FRONTEND_DIR / full_path
            if candidate.is_file():
                return FileResponse(str(candidate))
        return FileResponse(str(_FRONTEND_DIR / "index.html"))


if __name__ == "__main__":
    import uvicorn

    # The portable launcher selects an unused local port and passes it through
    # the environment.  Binding to loopback keeps the packaged app local-only.
    port = int(os.environ.get("ALGOPILOT_PORT", "8000"))
    uvicorn.run(app, host="127.0.0.1", port=port)
