"""Async engine va sessiya fabrikasi."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bot.config import get_settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def _prepare_sqlite_path(url: str) -> None:
    """SQLite fayli joylashadigan papkani yaratadi."""
    marker = "sqlite+aiosqlite:///"
    if not url.startswith(marker):
        return
    db_path = url[len(marker):].split("?", 1)[0]
    if db_path and db_path != ":memory:":
        Path(db_path).expanduser().parent.mkdir(parents=True, exist_ok=True)


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _prepare_sqlite_path(settings.database_url)
        kwargs: dict[str, object] = {"echo": False, "pool_pre_ping": True}
        if settings.is_sqlite:
            # SQLite'da pool sozlamalari qo'llanmaydi
            kwargs.pop("pool_pre_ping")
        _engine = create_async_engine(settings.database_url, **kwargs)

        if settings.is_sqlite:
            @event.listens_for(_engine.sync_engine, "connect")
            def _sqlite_pragmas(dbapi_conn, _record) -> None:  # type: ignore[no-untyped-def]
                cursor = dbapi_conn.cursor()
                # WAL — parallel o'qish/yozishda "database is locked" xatosini kamaytiradi
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA busy_timeout=10000")
                cursor.close()
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            get_engine(),
            expire_on_commit=False,
            autoflush=False,
        )
    return _sessionmaker


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Tranzaksiya konteksti: xatoda rollback, oxirida sessiya yopiladi."""
    factory = get_sessionmaker()
    session = factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def ping() -> bool:
    """Baza javob beryaptimi — `/health` uchun."""
    try:
        async with session_scope() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def dispose_engine() -> None:
    """Graceful shutdown: barcha ulanishlarni yopish."""
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None
