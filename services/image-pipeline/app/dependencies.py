"""FastAPI dependency injection."""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from ase_shared.database.session import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
