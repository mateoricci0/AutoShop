"""Pydantic schemas for auth endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Request body for POST /login."""

    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    """Successful login response."""

    ok: bool = True


class VerifyResponse(BaseModel):
    """Successful session verification response."""

    ok: bool = True


class LogoutResponse(BaseModel):
    """Successful logout response."""

    ok: bool = True
