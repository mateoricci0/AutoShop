"""Session management — create, validate, and revoke session tokens in Redis.

Tokens are opaque URL-safe random strings.  Only their SHA-256 hash is stored
in Redis (and optionally in ``admin_session`` for audit purposes).  This
means even if Redis is compromised, the raw tokens cannot be recovered.
"""

from __future__ import annotations

import hashlib
import secrets

import redis.asyncio as aioredis

SESSION_PREFIX = "session:"


def _hash_token(token: str) -> str:
    """Return the SHA-256 hex digest of *token*."""
    return hashlib.sha256(token.encode()).hexdigest()


async def create_session(redis: aioredis.Redis, ttl_seconds: int) -> str:  # type: ignore[type-arg]
    """Create a new session token, persist its hash in Redis, and return the raw token.

    Args:
        redis: An active async Redis client.
        ttl_seconds: How long the session should live (in seconds).

    Returns:
        The raw (unhashed) opaque token.  This value should be placed in the
        ``session`` HttpOnly cookie and never stored directly.
    """
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    await redis.setex(f"{SESSION_PREFIX}{token_hash}", ttl_seconds, "1")
    return token


async def validate_session(redis: aioredis.Redis, token: str) -> bool:  # type: ignore[type-arg]
    """Return True if *token* maps to a live session in Redis.

    Args:
        redis: An active async Redis client.
        token: The raw token from the ``session`` cookie.
    """
    token_hash = _hash_token(token)
    result = await redis.exists(f"{SESSION_PREFIX}{token_hash}")
    return bool(result)


async def revoke_session(redis: aioredis.Redis, token: str) -> None:  # type: ignore[type-arg]
    """Delete the session corresponding to *token* from Redis.

    Args:
        redis: An active async Redis client.
        token: The raw token from the ``session`` cookie.
    """
    token_hash = _hash_token(token)
    await redis.delete(f"{SESSION_PREFIX}{token_hash}")
