from __future__ import annotations

from sqlalchemy import create_engine, inspect, text

from core.schema_migrations import upgrade_schema


def test_fresh_database_is_created_at_head(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'fresh.db').as_posix()}")
    upgrade_schema(engine)

    inspector = inspect(engine)
    assert "users" in inspector.get_table_names()
    assert "oj_submissions" in inspector.get_table_names()
    with engine.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "20260718_0002"


def test_legacy_oj_event_link_is_migrated(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'legacy.db').as_posix()}")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE learning_event_logs (event_id VARCHAR(32) PRIMARY KEY)"))
        connection.execute(
            text(
                """
                CREATE TABLE oj_submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    problem_slug VARCHAR(128) NOT NULL,
                    language VARCHAR(16) NOT NULL,
                    code TEXT NOT NULL,
                    verdict VARCHAR(8) NOT NULL,
                    passed INTEGER NOT NULL,
                    total INTEGER NOT NULL,
                    compile_error TEXT NOT NULL,
                    cases JSON NOT NULL,
                    runtime_ms_avg INTEGER NOT NULL,
                    event_id VARCHAR(64),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )
        )
        connection.execute(text("INSERT INTO users (id) VALUES (1)"))
        connection.execute(
            text(
                """
                INSERT INTO oj_submissions (
                    user_id, problem_slug, language, code, verdict, passed, total,
                    compile_error, cases, runtime_ms_avg, event_id
                ) VALUES (1, 'two-sum', 'python', '', 'WA', 0, 1, '', '[]', 0, 'orphan')
                """
            )
        )

    upgrade_schema(engine)
    foreign_keys = inspect(engine).get_foreign_keys("oj_submissions")
    assert any(
        fk["constrained_columns"] == ["event_id"] and fk["referred_table"] == "learning_event_logs"
        for fk in foreign_keys
    )
    with engine.connect() as connection:
        assert connection.execute(text("SELECT event_id FROM oj_submissions")).scalar_one() is None

    # Running the compatibility migration again must be a no-op.
    upgrade_schema(engine)
