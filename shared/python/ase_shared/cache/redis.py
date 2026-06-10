"""Redis client factory for ASE services.

Provides an async Redis connection (via redis.asyncio) that each service
can import and use without managing connection lifecycle manually.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from typing import Optional

import redis.asyncio as aioredis

_REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

_client: Optional[aioredis.Redis] = None  # type: ignore[type-arg]


async def get_redis_client() -> aioredis.Redis:  # type: ignore[type-arg]
    """Return (or create) the shared async Redis client.

    The client is created lazily on first call and reused thereafter.
    """
    global _client
    if _client is None:
        _client = aioredis.from_url(
            _REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _client


# Backward-compatible sync accessor (returns the cached client or creates one
# synchronously via from_url — connection is still lazy).
def get_redis() -> aioredis.Redis:  # type: ignore[type-arg]
    """Return the shared Redis client (synchronous accessor for non-async contexts)."""
    global _client
    if _client is None:
        _client = aioredis.from_url(
            _REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _client


async def get_redis_dep() -> AsyncGenerator[aioredis.Redis, None]:  # type: ignore[type-arg]
    """FastAPI dependency that yields the shared Redis client."""
    client = await get_redis_client()
    yield client


async def close_redis() -> None:
    """Close the Redis connection.  Call during application shutdown."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


async def ping_redis() -> bool:
    """Return True if Redis is reachable, False otherwise."""
    try:
        client = await get_redis_client()
        return await client.ping()
    except Exception:
        return False
