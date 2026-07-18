"""Alembic schema migration entry point used by startup and maintenance scripts."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine

from core.database import engine as default_engine


def _alembic_config() -> Config:
    backend_root = Path(__file__).resolve().parent.parent
    config = Config(str(backend_root / "alembic.ini"))
    # An absolute path also works from a PyInstaller extraction directory.
    config.set_main_option("script_location", str(backend_root / "migrations"))
    return config


def upgrade_schema(target_engine: Engine | None = None) -> None:
    """Upgrade the configured database to the latest committed schema revision."""
    engine = target_engine or default_engine
    config = _alembic_config()
    with engine.connect() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
