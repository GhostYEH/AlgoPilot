"""pytest 全局配置：确保 backend 目录在 sys.path 中，并提供共享 fixture。"""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))