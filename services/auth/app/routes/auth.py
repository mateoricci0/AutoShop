"""Auth routes: login, logout, verify."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from redis.asyncio import Redis

from ase_shared.security.hashing import verify_password

from app.config import settings
from app.dependencies import get_redis
from app.schemas.auth import LoginRequest, LoginResponse, LogoutResponse, VerifyResponse
from app.services.session import create_session, revoke_session, validate_session

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["auth"])

_SESSION_COOKIE = "session"


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_SESSION_COOKIE,
        value=token,
        httponly=True,
        secure=(settings.ENVIRONMENT == "production"),
        samesite="lax",
        max_age=settings.SESSION_TTL_SECONDS,
        path="/",
    )


def _delete_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=_SESSION_COOKIE,
        httponly=True,
        secure=(settings.ENVIRONMENT == "production"),
        samesite="lax",
        path="/",
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    response: Response,
    redis: Redis = Depends(get_redis),
) -> LoginResponse:
    """Verify the admin password and issue a session cookie on success."""
    if not settings.ADMIN_PASSWORD_HASH:
        raise HTTPException(status_code=503, detail="Auth service not configured")

    if not verify_password(body.password, settings.ADMIN_PASSWORD_HASH):
        logger.warning("login_failed_invalid_password")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = await create_session(redis, settings.SESSION_TTL_SECONDS)
    _set_session_cookie(response, token)
    logger.info("login_success")
    return LoginResponse()


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    response: Response,
    redis: Redis = Depends(get_redis),
) -> LogoutResponse:
    """Revoke the current session token and clear the cookie."""
    token = request.cookies.get(_SESSION_COOKIE)
    if token:
        await revoke_session(redis, token)
        logger.info("logout_success")
    _delete_session_cookie(response)
    return LogoutResponse()


@router.get("/verify", response_model=VerifyResponse)
async def verify(
    request: Request,
    redis: Redis = Depends(get_redis),
) -> VerifyResponse:
    """Validate the session cookie.

    Returns 200 + ``{"ok": true}`` when the session is active.
    Returns 401 when no session cookie is present or the session has expired.

    This endpoint is called by other microservices as an auth check.
    """
    token = request.cookies.get(_SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="No session cookie")

    if not await validate_session(redis, token):
        raise HTTPException(status_code=401, detail="Session expired or invalid")

    return VerifyResponse()
