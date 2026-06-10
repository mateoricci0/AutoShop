from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from ase_shared.database.session import AsyncSessionLocal
import redis.asyncio as aioredis

from .config import settings


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


_redis: aioredis.Redis | None = None


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    yield _redis
