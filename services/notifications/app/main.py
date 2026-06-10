"""Notifications Service — dispatches alerts via Email, Discord, Telegram, and Slack."""

from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Response, status
from prometheus_fastapi_instrumentator import Instrumentator

from ase_shared.cache.redis import close_redis, ping_redis
from ase_shared.logging.config import configure_logging

from .config import settings

configure_logging("notifications")
logger = structlog.get_logger()

SERVICE_NAME = "notifications"


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    logger.info("starting", service=SERVICE_NAME, environment=settings.ENVIRONMENT)
    yield
    logger.info("shutdown", service=SERVICE_NAME)
    await close_redis()


app = FastAPI(
    title="ASE Notifications",
    description="Dispatches alerts via Email, Discord, Telegram, and Slack.",
    version="0.1.0",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app)


@app.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    """Liveness probe — returns 200 if the process is running."""
    return {"status": "ok", "service": SERVICE_NAME}


@app.get("/ready", tags=["ops"])
async def ready(response: Response) -> dict[str, Any]:
    """Readiness probe — checks downstream dependencies."""
    checks: dict[str, str] = {}

    redis_ok = await ping_redis()
    checks["redis"] = "ok" if redis_ok else "error"

    db_ok = False
    try:
        import asyncpg  # noqa: F401
        conn = await asyncpg.connect(
            settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"),
            timeout=3,
        )
        await conn.close()
        db_ok = True
    except Exception as exc:
        logger.warning("db_check_failed", error=str(exc), service=SERVICE_NAME)

    checks["database"] = "ok" if db_ok else "error"

    all_ok = all(v == "ok" for v in checks.values())
    if not all_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if all_ok else "degraded",
        "service": SERVICE_NAME,
        "checks": checks,
    }
