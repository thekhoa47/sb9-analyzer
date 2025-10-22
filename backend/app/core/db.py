# app/core/db.py
from __future__ import annotations

from typing import AsyncIterator, Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import settings


class Base(DeclarativeBase):
    pass


def _to_psycopg3_url(url: str) -> str:
    """
    Normalize any Postgres URL to the psycopg3 dialect.
    Examples:
      postgresql://...   -> postgresql+psycopg://...
      postgres://...     -> postgresql+psycopg://...
      postgresql+asyncpg://... (leave as-is if you explicitly want asyncpg)
    """
    if url.startswith("postgresql+psycopg://") or url.startswith(
        "postgresql+asyncpg://"
    ):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


# ---------- Sync engine & session (psycopg3) ----------
SYNC_DATABASE_URL = _to_psycopg3_url(settings.DATABASE_URL)

engine = create_engine(
    SYNC_DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_local_session() -> Iterator:
    """FastAPI dependency to yield a SYNC session (psycopg3)."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ---------- Async engine & session (psycopg3 async) ----------
def _to_async_psycopg3_url(url: str) -> str:
    # For psycopg3, the same 'postgresql+psycopg://' URL works for async engine too.
    # SQLAlchemy handles the async connection under the hood when using create_async_engine.
    return _to_psycopg3_url(url)


ASYNC_DATABASE_URL = getattr(
    settings, "ASYNC_DATABASE_URL", None
) or _to_async_psycopg3_url(settings.DATABASE_URL)

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency for ASYNC session (psycopg3)."""
    async with AsyncSessionLocal() as session:
        yield session
        # closed by context manager
