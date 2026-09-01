"""SQLAlchemy 2.0 engine / session。

SQLite（测试与本地轻量开发）与 MySQL 8（生产）双方言：
- SQLite 内存库用 StaticPool，让 TestClient 的多线程共享同一个连接；
- SQLite 打开 PRAGMA foreign_keys，使 ON DELETE CASCADE 行为与生产 MySQL 一致。
"""

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .config import get_settings


class Base(DeclarativeBase):
    pass


def _make_engine(database_url: str):
    if database_url.startswith("sqlite"):
        kwargs: dict = {"pool_pre_ping": True}
        if database_url.endswith(":memory:") or "mode=memory" in database_url:
            kwargs.update(
                poolclass=StaticPool,
                connect_args={"check_same_thread": False},
            )
        eng = create_engine(database_url, **kwargs)

        @event.listens_for(eng, "connect")
        def _fk_on(dbapi_conn, _record):  # noqa: ANN001 -- DBAPI 连接对象
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return eng
    return create_engine(database_url, pool_pre_ping=True, pool_recycle=3600)


engine = _make_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
