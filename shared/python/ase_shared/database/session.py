"""Async SQLAlchemy engine and session factory.

Usage in FastAPI:
    from ase_shared.database.session import get_db

    @router.get("/items")
    async def list_items(db: AsyncSession = Depends(get_db)):
        ...
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ase_shared.database.base import Base

_DEFAULT_DATABASE_URL = (
    "postgresql+asyncpg://ase_app:password@postgres:5432/ase"
)

DATABASE_URL: str = os.environ.get("DATABASE_URL", _DEFAULT_DATABASE_URL)

engine = create_async_engine(
    DATABASE_URL,
    echo=os.environ.get("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides an ``AsyncSession`` and ensures cleanup."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables.  Intended for tests — production uses Alembic."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
