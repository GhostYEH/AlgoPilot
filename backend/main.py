"""
算法智能学习平台 — FastAPI 入口
扩展：账号体系、学习进度（MySQL）、后续 LangChain / 星火等
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.ai_tutor import router as ai_tutor_router
from api.tts import router as tts_router
from api.oj_assistant import router as oj_assistant_router
from api.orchestrator import router as orchestrator_router
from api.auth import router as auth_router
from api.health import router as health_router
from api.learning import router as learning_router
from api.oj import router as oj_router
from api.search import router as search_router
from api.skills import router as skills_router
from api.memory import router as memory_router
from api.mastery import router as mastery_router
from api.events import router as events_router
from api.analytics import router as analytics_router
from core.database import Base, engine


@asynccontextmanager
async def lifespan(_app: FastAPI):
    import models.db_models  # noqa: F401 — 注册 ORM 元数据

    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="算法智能学习平台 API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(orchestrator_router, prefix="/api/orchestrator", tags=["orchestrator"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(learning_router, prefix="/api/me", tags=["learning"])
app.include_router(ai_tutor_router, prefix="/api/ai", tags=["ai"])
app.include_router(tts_router, prefix="/api/ai/tts", tags=["ai-tts"])
app.include_router(oj_assistant_router, prefix="/api/ai/oj", tags=["ai-oj"])
app.include_router(oj_router, prefix="/api", tags=["oj"])
app.include_router(search_router, prefix="/api/search", tags=["search"])
app.include_router(skills_router, prefix="/api")
app.include_router(memory_router, prefix="/api")
app.include_router(mastery_router, prefix="/api")
app.include_router(events_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
