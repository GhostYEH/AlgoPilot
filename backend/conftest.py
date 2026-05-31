"""pytest 全局 fixture：确保 backend 包可导入。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("JWT_SECRET", "pytest-secret-do-not-use-in-production")


@pytest.fixture(scope="session", autouse=True)
def _ensure_db_tables():
    """确保测试库包含 StudentLearningMemory 等新表。"""
    import models.db_models  # noqa: F401
    from core.database import Base, engine

    Base.metadata.create_all(bind=engine)
    yield
