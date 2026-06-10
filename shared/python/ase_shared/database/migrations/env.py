"""Alembic async migration environment.

Supports both offline mode (generates SQL) and online mode (runs against a
live database) using asyncpg.
"""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

# Import Base and all models so Alembic can detect table definitions.
from ase_shared.database.base import Base
import ase_shared.models  # noqa: F401 — registers all mappers with Base

# ---------------------------------------------------------------------------
# Alembic Config object
# ---------------------------------------------------------------------------
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# ---------------------------------------------------------------------------
# Database URL — prefer environment variable over alembic.ini
# ---------------------------------------------------------------------------
_DEFAULT_DATABASE_URL = "postgresql+asyncpg://ase_app:password@postgres:5432/ase"
DATABASE_URL: str = os.environ.get("DATABASE_URL", _DEFAULT_DATABASE_URL)


# ---------------------------------------------------------------------------
# Offline migrations (generate SQL without connecting)
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migrations (connect and run)
# ---------------------------------------------------------------------------
def do_run_migrations(connection):  # type: ignore[no-untyped-def]
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = create_async_engine(DATABASE_URL, poolclass=None)  # type: ignore[call-arg]
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
