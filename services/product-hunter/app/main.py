"""Product Hunter Service — discovers and scores trending products."""

from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Response, status
from prometheus_fastapi_instrumentator import Instrumentator

from ase_shared.cache.redis import close_redis, ping_redis
from ase_shared.logging.config import configure_logging

from .config import settings
from .routes.candidates import router as candidates_router
from .routes.jobs import router as jobs_router

configure_logging("product-hunter")
logger = structlog.get_logger()

SERVICE_NAME = "product-hunter"


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    logger.info("starting", service=SERVICE_NAME, environment=settings.ENVIRONMENT)

    # Try to start Playwright pool; degrade gracefully if unavailable
    try:
        from playwright.async_api import async_playwright
        _pw = await async_playwright().start()
        app.state.playwright = _pw
        logger.info("playwright_ready")
    except Exception as exc:
        logger.warning("playwright_unavailable", reason=str(exc))
        app.state.playwright = None

    yield

    # Stop Playwright if it started
    pw = getattr(app.state, "playwright", None)
    if pw:
        try:
            await pw.stop()
        except Exception:
            pass

    logger.info("shutdown", service=SERVICE_NAME)
    await close_redis()


app = FastAPI(
    title="ASE Product Hunter",
    description="Discovers and scores trending products from multiple sources.",
    version="0.1.0",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app)

app.include_router(candidates_router, prefix="/v1")
app.include_router(jobs_router, prefix="/v1")


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
