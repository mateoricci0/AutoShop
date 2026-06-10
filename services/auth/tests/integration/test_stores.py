"""Integration tests for store CRUD endpoints.

Shopify's shop.json API call is mocked using respx/unittest.mock so tests
don't require a live Shopify account.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, Response


_VALID_STORE_PAYLOAD = {
    "name": "My Test Store",
    "shopify_domain": "mytest.myshopify.com",
    "shopify_access_token": "shpat_test123",
    "currency": "USD",
    "timezone": "UTC",
}

_SHOPIFY_SHOP_RESPONSE = {
    "shop": {
        "id": 12345678,
        "name": "My Test Store",
        "plan_name": "basic",
        "currency": "USD",
        "domain": "mytest.myshopify.com",
    }
}


class TestListStores:
    @pytest.mark.asyncio
    async def test_empty_list_on_fresh_db(self, client: AsyncClient) -> None:
        resp = await client.get("/stores")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_includes_created_store(self, client: AsyncClient) -> None:
        create_resp = await client.post("/stores", json=_VALID_STORE_PAYLOAD)
        assert create_resp.status_code == 201

        list_resp = await client.get("/stores")
        assert list_resp.status_code == 200
        stores = list_resp.json()
        assert len(stores) == 1
        assert stores[0]["shopify_domain"] == "mytest.myshopify.com"

    @pytest.mark.asyncio
    async def test_access_token_never_returned(self, client: AsyncClient) -> None:
        await client.post("/stores", json=_VALID_STORE_PAYLOAD)
        resp = await client.get("/stores")
        for store in resp.json():
            assert "shopify_access_token" not in store


class TestCreateStore:
    @pytest.mark.asyncio
    async def test_create_returns_201(self, client: AsyncClient) -> None:
        resp = await client.post("/stores", json=_VALID_STORE_PAYLOAD)
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_create_returns_store_fields(self, client: AsyncClient) -> None:
        resp = await client.post("/stores", json=_VALID_STORE_PAYLOAD)
        data = resp.json()
        assert data["name"] == "My Test Store"
        assert data["shopify_domain"] == "mytest.myshopify.com"
        assert data["currency"] == "USD"
        assert data["is_active"] is True
        assert "id" in data

    @pytest.mark.asyncio
    async def test_duplicate_domain_returns_409(self, client: AsyncClient) -> None:
        await client.post("/stores", json=_VALID_STORE_PAYLOAD)
        resp = await client.post("/stores", json=_VALID_STORE_PAYLOAD)
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_invalid_domain_returns_422(self, client: AsyncClient) -> None:
        payload = {**_VALID_STORE_PAYLOAD, "shopify_domain": "not-a-valid-domain.com"}
        resp = await client.post("/stores", json=payload)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_access_token_not_in_response(self, client: AsyncClient) -> None:
        resp = await client.post("/stores", json=_VALID_STORE_PAYLOAD)
        assert "shopify_access_token" not in resp.json()


class TestGetStore:
    @pytest.mark.asyncio
    async def test_get_existing_store(self, client: AsyncClient) -> None:
        create = await client.post("/stores", json=_VALID_STORE_PAYLOAD)
        store_id = create.json()["id"]

        resp = await client.get(f"/stores/{store_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == store_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_store_returns_404(self, client: AsyncClient) -> None:
        resp = await client.get(f"/stores/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestUpdateStore:
    @pytest.mark.asyncio
    async def test_update_name(self, client: AsyncClient) -> None:
        create = await client.post("/stores", json=_VALID_STORE_PAYLOAD)
        store_id = create.json()["id"]

        resp = await client.put(f"/stores/{store_id}", json={"name": "Renamed Store"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed Store"

    @pytest.mark.asyncio
    async def test_update_settings(self, client: AsyncClient) -> None:
        create = await client.post("/stores", json=_VALID_STORE_PAYLOAD)
        store_id = create.json()["id"]

        new_settings = {"theme": "dark", "notifications": True}
        resp = await client.put(f"/stores/{store_id}", json={"settings": new_settings})
        assert resp.status_code == 200
        assert resp.json()["settings"] == new_settings

    @pytest.mark.asyncio
    async def test_update_nonexistent_store_returns_404(self, client: AsyncClient) -> None:
        resp = await client.put(f"/stores/{uuid.uuid4()}", json={"name": "Ghost"})
        assert resp.status_code == 404


class TestDeleteStore:
    @pytest.mark.asyncio
    async def test_delete_returns_204(self, client: AsyncClient) -> None:
        create = await client.post("/stores", json=_VALID_STORE_PAYLOAD)
        store_id = create.json()["id"]

        resp = await client.delete(f"/stores/{store_id}")
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_deleted_store_not_in_list(self, client: AsyncClient) -> None:
        create = await client.post("/stores", json=_VALID_STORE_PAYLOAD)
        store_id = create.json()["id"]
        await client.delete(f"/stores/{store_id}")

        list_resp = await client.get("/stores")
        ids = [s["id"] for s in list_resp.json()]
        assert store_id not in ids

    @pytest.mark.asyncio
    async def test_delete_nonexistent_store_returns_404(self, client: AsyncClient) -> None:
        resp = await client.delete(f"/stores/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestTestConnection:
    @pytest.mark.asyncio
    async def test_successful_shopify_connection(self, client: AsyncClient) -> None:
        create = await client.post("/stores", json=_VALID_STORE_PAYLOAD)
        store_id = create.json()["id"]

        # Mock the httpx client so no real network call is made
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = _SHOPIFY_SHOP_RESPONSE

        with patch(
            "app.services.store_service.httpx.AsyncClient"
        ) as mock_client_class:
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_context)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_context.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_context

            resp = await client.post(f"/stores/{store_id}/test-connection")

        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["shopify_plan"] == "basic"
        assert data["currency"] == "USD"
        assert data["shop_name"] == "My Test Store"

    @pytest.mark.asyncio
    async def test_shopify_auth_failure_returns_502(self, client: AsyncClient) -> None:
        create = await client.post("/stores", json=_VALID_STORE_PAYLOAD)
        store_id = create.json()["id"]

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"errors": "Invalid API key"}

        with patch(
            "app.services.store_service.httpx.AsyncClient"
        ) as mock_client_class:
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_context)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_context.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_context

            resp = await client.post(f"/stores/{store_id}/test-connection")

        assert resp.status_code == 502

    @pytest.mark.asyncio
    async def test_connection_for_nonexistent_store_returns_404(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(f"/stores/{uuid.uuid4()}/test-connection")
        assert resp.status_code == 404
