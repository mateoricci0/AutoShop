"""Pytest fixtures for auth service tests.

Integration tests use testcontainers to spin up real PostgreSQL and Redis
instances.  The containers are started once per test session and torn down
at the end.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
import redis.asyncio as aioredis
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from ase_shared.database.base import Base
from ase_shared.security.hashing import hash_password

# ---------------------------------------------------------------------------
# Generate test secrets at module import time
# ---------------------------------------------------------------------------

_FERNET_KEY = Fernet.generate_key().decode()
_ADMIN_PASSWORD = "test-admin-password"
_ADMIN_PASSWORD_HASH = hash_password(_ADMIN_PASSWORD)


# ---------------------------------------------------------------------------
# Session-scoped containers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def postgres_container():
    """Start a PostgreSQL container once for the whole test session."""
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg


@pytest.fixture(scope="session")
def redis_container():
    """Start a Redis container once for the whole test session."""
    with RedisContainer("redis:7-alpine") as r:
        yield r


# ---------------------------------------------------------------------------
# Environment variables (must be set before importing app modules)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def set_env(postgres_container, redis_container):  # type: ignore[no-untyped-def]
    """Patch environment variables so the app reads from test containers."""
    pg_url = postgres_container.get_connection_url().replace(
        "psycopg2", "asyncpg"
    )
    redis_url = f"redis://{redis_container.get_container_host_ip()}:{redis_container.get_exposed_port(6379)}/0"

    os.environ["DATABASE_URL"] = pg_url
    os.environ["REDIS_URL"] = redis_url
    os.environ["FERNET_KEY"] = _FERNET_KEY
    os.environ["ADMIN_PASSWORD_HASH"] = _ADMIN_PASSWORD_HASH
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["LOG_LEVEL"] = "WARNING"
    yield


# ---------------------------------------------------------------------------
# Async engine + schema creation
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def db_engine(set_env):  # type: ignore[no-untyped-def]
    """Return an async SQLAlchemy engine pointed at the test PostgreSQL."""
    from app.config import settings  # imported after env is set

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    return engine


@pytest_asyncio.fixture(scope="session")
async def create_tables(db_engine):  # type: ignore[no-untyped-def]
    """Create all ORM tables once per test session."""
    import ase_shared.models  # noqa: F401 — register all mappers

    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(db_engine, create_tables) -> AsyncGenerator[AsyncSession, None]:  # type: ignore[no-untyped-def]
    """Provide a transactional DB session that is rolled back after each test."""
    session_factory = async_sessionmaker(
        bind=db_engine, expire_on_commit=False, autoflush=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


# ---------------------------------------------------------------------------
# Redis client
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def redis_client(set_env) -> AsyncGenerator[aioredis.Redis, None]:  # type: ignore[no-untyped-def]
    """Provide a fresh async Redis client, flushing the DB after each test."""
    from app.config import settings

    client = aioredis.from_url(
        settings.REDIS_URL, encoding="utf-8", decode_responses=True
    )
    yield client
    await client.flushdb()
    await client.aclose()


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession,
    redis_client: aioredis.Redis,
    create_tables,  # type: ignore[no-untyped-def]
) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async httpx client wired to the FastAPI app with overrides."""
    from app.dependencies import get_db, get_redis
    from app.main import app

    async def _override_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def _override_redis() -> AsyncGenerator[aioredis.Redis, None]:
        yield redis_client

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_redis] = _override_redis

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Convenience exports for tests
# ---------------------------------------------------------------------------

ADMIN_PASSWORD = _ADMIN_PASSWORD
