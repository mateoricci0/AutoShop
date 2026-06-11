"""Shopify Publisher Service — publishes approved products to Shopify stores."""

from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Response, status
from prometheus_fastapi_instrumentator import Instrumentator

from ase_shared.cache.redis import close_redis, ping_redis
from ase_shared.logging.config import configure_logging

from .config import settings
from .routes.publish import router as publish_router
from .routes.published import router as published_router
from .routes.webhooks import router as webhooks_router

configure_logging("shopify-publisher")
logger = structlog.get_logger()

SERVICE_NAME = "shopify-publisher"


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    logger.info("starting", service=SERVICE_NAME, environment=settings.ENVIRONMENT)
    yield
    logger.info("shutdown", service=SERVICE_NAME)
    await close_redis()


app = FastAPI(
    title="ASE Shopify Publisher",
    description="Publishes approved products to Shopify stores.",
    version="0.1.0",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app)

app.include_router(publish_router, prefix="/v1")
app.include_router(published_router, prefix="/v1")
app.include_router(webhooks_router, prefix="/v1")


@app.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME}


@app.get("/ready", tags=["ops"])
async def ready(response: Response) -> dict[str, Any]:
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
