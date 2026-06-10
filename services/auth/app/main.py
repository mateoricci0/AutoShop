"""Auth service FastAPI application."""

from __future__ import annotations

import sqlalchemy
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from ase_shared.cache.redis import close_redis, ping_redis
from ase_shared.database.session import engine
from ase_shared.exceptions import (
    ASEError,
    AuthenticationError,
    ConflictError,
    ExternalAPIError,
    NotFoundError,
    ValidationError,
)
from ase_shared.logging.config import configure_logging

from app.config import settings
from app.routes.auth import router as auth_router
from app.routes.stores import router as stores_router

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    """Configure logging on startup; clean up connections on shutdown."""
    configure_logging(level=settings.LOG_LEVEL, environment=settings.ENVIRONMENT)
    logger.info(
        "auth_service_starting",
        environment=settings.ENVIRONMENT,
        log_level=settings.LOG_LEVEL,
    )
    yield
    await close_redis()
    await engine.dispose()
    logger.info("auth_service_stopped")


app = FastAPI(
    title="ASE Auth Service",
    description="Single-user authentication with Redis-backed session tokens.",
    version="0.1.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator(
    should_group_status_codes=False,
    excluded_handlers=["/health", "/ready", "/metrics"],
).instrument(app).expose(app, endpoint="/metrics")

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


def _ase_error_status(exc: ASEError) -> int:
    """Map ASE exception types to HTTP status codes."""
    if isinstance(exc, NotFoundError):
        return 404
    if isinstance(exc, ConflictError):
        return 409
    if isinstance(exc, ValidationError):
        return 422
    if isinstance(exc, AuthenticationError):
        return 401
    if isinstance(exc, ExternalAPIError):
        return 502
    return 500


@app.exception_handler(ASEError)
async def ase_error_handler(request: Request, exc: ASEError) -> JSONResponse:
    status_code = _ase_error_status(exc)
    logger.warning(
        "ase_error",
        error_type=type(exc).__name__,
        detail=str(exc),
        status_code=status_code,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc), "error": type(exc).__name__},
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(auth_router, prefix="")
app.include_router(stores_router, prefix="")

# ---------------------------------------------------------------------------
# Health / readiness endpoints
# ---------------------------------------------------------------------------


@app.get("/health", tags=["ops"])
async def health() -> dict[str, Any]:
    """Liveness probe — always returns 200 if the process is running."""
    return {"status": "ok", "service": settings.SERVICE_NAME}


@app.get("/ready", tags=["ops"])
async def ready() -> dict[str, Any]:
    """Readiness probe — checks DB and Redis connectivity."""
    redis_ok = await ping_redis()

    db_ok = False
    try:
        async with engine.connect() as conn:
            await conn.execute(sqlalchemy.text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    if not redis_ok or not db_ok:
        raise HTTPException(
            status_code=503,
            detail={"db": db_ok, "redis": redis_ok},
        )

    return {
        "status": "ready",
        "service": settings.SERVICE_NAME,
        "db": db_ok,
        "redis": redis_ok,
    }
