from collections.abc import AsyncIterator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def init_engine(url: str) -> AsyncEngine:
    global _engine, _sessionmaker
    if url.startswith("sqlite"):
        _engine = create_async_engine(url, connect_args={"timeout": 30})

        @event.listens_for(_engine.sync_engine, "connect")
        def _sqlite_pragmas(conn, _record):  # noqa: ANN001
            cur = conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA synchronous=NORMAL")
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()
    else:
        _engine = create_async_engine(url, pool_size=5, max_overflow=5, pool_pre_ping=True)
    _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def engine() -> AsyncEngine:
    assert _engine is not None, "init_engine() no se ha llamado"
    return _engine


def session_factory() -> async_sessionmaker[AsyncSession]:
    assert _sessionmaker is not None, "init_engine() no se ha llamado"
    return _sessionmaker


async def create_all() -> None:
    from app import models  # noqa: F401

    async with engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_factory()() as session:
        yield session


def dialect() -> str:
    return engine().dialect.name
