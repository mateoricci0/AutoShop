"""FastAPI shared dependencies for the auth service."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from ase_shared.database.session import AsyncSessionLocal
from ase_shared.cache.redis import get_redis_client


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session and ensure it is cleaned up."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:  # type: ignore[type-arg]
    """Yield the shared async Redis client."""
    client = await get_redis_client()
    yield client
