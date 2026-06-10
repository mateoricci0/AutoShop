"""Unit tests for session management using a mock Redis client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.session import (
    SESSION_PREFIX,
    _hash_token,
    create_session,
    revoke_session,
    validate_session,
)


def _make_redis_mock() -> MagicMock:
    """Return an async-capable Mock that simulates a Redis client."""
    mock = MagicMock()
    mock.setex = AsyncMock(return_value=True)
    mock.exists = AsyncMock(return_value=1)
    mock.delete = AsyncMock(return_value=1)
    return mock


class TestHashToken:
    def test_returns_hex_string(self) -> None:
        digest = _hash_token("my-token")
        assert len(digest) == 64
        assert all(c in "0123456789abcdef" for c in digest)

    def test_deterministic(self) -> None:
        assert _hash_token("abc") == _hash_token("abc")

    def test_different_inputs_produce_different_hashes(self) -> None:
        assert _hash_token("token-a") != _hash_token("token-b")


class TestCreateSession:
    @pytest.mark.asyncio
    async def test_returns_raw_token(self) -> None:
        redis = _make_redis_mock()
        token = await create_session(redis, ttl_seconds=3600)
        assert len(token) > 10

    @pytest.mark.asyncio
    async def test_stores_hash_in_redis(self) -> None:
        redis = _make_redis_mock()
        token = await create_session(redis, ttl_seconds=3600)
        expected_key = f"{SESSION_PREFIX}{_hash_token(token)}"
        redis.setex.assert_awaited_once_with(expected_key, 3600, "1")

    @pytest.mark.asyncio
    async def test_two_sessions_have_different_tokens(self) -> None:
        redis = _make_redis_mock()
        t1 = await create_session(redis, ttl_seconds=3600)
        t2 = await create_session(redis, ttl_seconds=3600)
        assert t1 != t2


class TestValidateSession:
    @pytest.mark.asyncio
    async def test_returns_true_for_existing_session(self) -> None:
        redis = _make_redis_mock()
        redis.exists = AsyncMock(return_value=1)
        result = await validate_session(redis, "some-token")
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_for_missing_session(self) -> None:
        redis = _make_redis_mock()
        redis.exists = AsyncMock(return_value=0)
        result = await validate_session(redis, "some-token")
        assert result is False

    @pytest.mark.asyncio
    async def test_looks_up_correct_key(self) -> None:
        redis = _make_redis_mock()
        token = "my-test-token"
        await validate_session(redis, token)
        expected_key = f"{SESSION_PREFIX}{_hash_token(token)}"
        redis.exists.assert_awaited_once_with(expected_key)


class TestRevokeSession:
    @pytest.mark.asyncio
    async def test_deletes_correct_key(self) -> None:
        redis = _make_redis_mock()
        token = "revoke-me"
        await revoke_session(redis, token)
        expected_key = f"{SESSION_PREFIX}{_hash_token(token)}"
        redis.delete.assert_awaited_once_with(expected_key)

    @pytest.mark.asyncio
    async def test_does_not_raise_when_key_missing(self) -> None:
        redis = _make_redis_mock()
        redis.delete = AsyncMock(return_value=0)  # key didn't exist
        await revoke_session(redis, "nonexistent-token")  # should not raise
