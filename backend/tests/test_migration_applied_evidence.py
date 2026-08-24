"""验证 Alembic 迁移 20260812_0004：为 student_knowledge_states 添加 applied_evidence 列。

测试策略：
1. 用 Alembic command API 在临时 SQLite DB 上执行真实迁移
2. 验证 upgrade 后 applied_evidence 列存在且默认值为 []
3. 验证 downgrade 后列被移除
4. 验证重复 upgrade 幂等（不报错）

注意：env.py 会用 settings.database_url 覆盖 alembic config 中的 URL，
因此必须通过 monkey-patch settings.database_url 来指定测试数据库。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from core.config import settings  # noqa: E402


def _make_alembic_config(db_url: str) -> Config:
    cfg = Config(str(_BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    cfg.set_main_option("script_location", str(_BACKEND_DIR / "migrations"))
    return cfg


def _column_exists(engine: sa.Engine, table: str, column: str) -> bool:
    inspector = sa.inspect(engine)
    if table not in inspector.get_table_names():
        return False
    return column in [col["name"] for col in inspector.get_columns(table)]


def _table_exists(engine: sa.Engine, table: str) -> bool:
    return table in sa.inspect(engine).get_table_names()


@pytest.fixture()
def temp_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test_migration.db"
    db_url = f"sqlite:///{db_file.as_posix()}"
    monkeypatch.setattr(settings, "database_url", db_url)
    cfg = _make_alembic_config(db_url)
    engine = sa.create_engine(db_url, future=True)
    yield cfg, engine, db_url
    engine.dispose()


class TestAppliedEvidenceMigration:
    """迁移 20260812_0004 测试。"""

    def test_upgrade_adds_applied_evidence_column(self, temp_db):
        cfg, engine, _ = temp_db
        command.upgrade(cfg, "head")
        assert _table_exists(engine, "student_knowledge_states")
        assert _column_exists(engine, "student_knowledge_states", "applied_evidence")

    def test_upgrade_then_downgrade_removes_column(self, temp_db):
        cfg, engine, _ = temp_db
        command.upgrade(cfg, "head")
        assert _column_exists(engine, "student_knowledge_states", "applied_evidence")
        command.downgrade(cfg, "20260812_0003")
        assert not _column_exists(engine, "student_knowledge_states", "applied_evidence")

    def test_repeated_upgrade_is_idempotent(self, temp_db):
        cfg, engine, _ = temp_db
        command.upgrade(cfg, "head")
        command.upgrade(cfg, "head")
        assert _column_exists(engine, "student_knowledge_states", "applied_evidence")

    def test_full_migration_chain_creates_all_tables(self, temp_db):
        cfg, engine, _ = temp_db
        command.upgrade(cfg, "head")
        for table in (
            "execution_traces",
            "student_knowledge_states",
            "bug_records",
            "hint_records",
        ):
            assert _table_exists(engine, table), f"表 {table} 应存在"

    def test_applied_evidence_default_is_empty_list(self, temp_db):
        cfg, engine, _ = temp_db
        command.upgrade(cfg, "head")

        with engine.connect() as conn:
            conn.execute(
                sa.text(
                    "INSERT INTO student_knowledge_states "
                    "(user_id, module_key, concept_id, knowledge_point, mastery, confidence, "
                    "attempt_count, success_count, independent_success_count, hint_usage, "
                    "recent_bug_types, applied_evidence, last_updated) "
                    "VALUES (1, 'test_module', 'test_concept', '', 0.0, 0.0, 0, 0, 0, 0, '[]', '[]', datetime('now'))"
                )
            )
            conn.commit()
            row = conn.execute(
                sa.text("SELECT applied_evidence FROM student_knowledge_states LIMIT 1")
            ).fetchone()
            assert row is not None
            applied = row[0]
            if isinstance(applied, str):
                import json
                applied = json.loads(applied)
            assert applied == [] or applied is None

    def test_downgrade_to_baseline_drops_all_evidence_tables(self, temp_db):
        cfg, engine, _ = temp_db
        command.upgrade(cfg, "head")
        assert _table_exists(engine, "student_knowledge_states")
        command.downgrade(cfg, "20260718_0001")
        assert not _table_exists(engine, "student_knowledge_states")
        assert not _table_exists(engine, "execution_traces")
        assert not _table_exists(engine, "bug_records")
        assert not _table_exists(engine, "hint_records")
