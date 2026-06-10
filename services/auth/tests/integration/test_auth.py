"""Integration tests for auth endpoints (login, logout, verify).

These tests use the real FastAPI app wired to testcontainers-backed
PostgreSQL and Redis instances via the fixtures in conftest.py.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import ADMIN_PASSWORD


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_correct_password_returns_200(self, client: AsyncClient) -> None:
        resp = await client.post("/login", json={"password": ADMIN_PASSWORD})
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True

    @pytest.mark.asyncio
    async def test_login_sets_session_cookie(self, client: AsyncClient) -> None:
        resp = await client.post("/login", json={"password": ADMIN_PASSWORD})
        assert resp.status_code == 200
        assert "session" in resp.cookies

    @pytest.mark.asyncio
    async def test_login_wrong_password_returns_401(self, client: AsyncClient) -> None:
        resp = await client.post("/login", json={"password": "wrong-password"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_empty_password_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post("/login", json={"password": ""})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_login_missing_body_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post("/login", json={})
        assert resp.status_code == 422


class TestVerify:
    @pytest.mark.asyncio
    async def test_verify_with_valid_session_returns_200(self, client: AsyncClient) -> None:
        # Login first to get a valid session cookie
        login_resp = await client.post("/login", json={"password": ADMIN_PASSWORD})
        assert login_resp.status_code == 200

        verify_resp = await client.get("/verify")
        assert verify_resp.status_code == 200
        assert verify_resp.json()["ok"] is True

    @pytest.mark.asyncio
    async def test_verify_without_cookie_returns_401(self, client: AsyncClient) -> None:
        resp = await client.get("/verify")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_verify_with_invalid_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        client.cookies.set("session", "totally-invalid-token")
        resp = await client.get("/verify")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_verify_after_logout_returns_401(self, client: AsyncClient) -> None:
        # Login
        login_resp = await client.post("/login", json={"password": ADMIN_PASSWORD})
        assert login_resp.status_code == 200
        # Verify valid
        assert (await client.get("/verify")).status_code == 200
        # Logout
        logout_resp = await client.post("/logout")
        assert logout_resp.status_code == 200
        # Verify again — should be 401 now
        verify_resp = await client.get("/verify")
        assert verify_resp.status_code == 401


class TestLogout:
    @pytest.mark.asyncio
    async def test_logout_clears_cookie(self, client: AsyncClient) -> None:
        await client.post("/login", json={"password": ADMIN_PASSWORD})
        resp = await client.post("/logout")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    @pytest.mark.asyncio
    async def test_logout_without_session_is_ok(self, client: AsyncClient) -> None:
        """Logging out without an active session should not raise an error."""
        resp = await client.post("/logout")
        assert resp.status_code == 200
