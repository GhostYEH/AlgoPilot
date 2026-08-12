from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from core.config import settings

_is_sqlite = settings.database_url.startswith("sqlite")

_engine_kwargs: dict = {}
if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
    _engine_kwargs["pool_pre_ping"] = False
else:
    _engine_kwargs["pool_pre_ping"] = True
    _engine_kwargs["pool_recycle"] = 3600

engine = create_engine(settings.database_url, **_engine_kwargs)

if _is_sqlite:

    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
