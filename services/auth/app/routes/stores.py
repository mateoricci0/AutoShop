"""Store CRUD routes."""

from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ase_shared.exceptions import ExternalAPIError, NotFoundError

from app.dependencies import get_db
from app.schemas.store import (
    StoreCreate,
    StoreResponse,
    StoreUpdate,
    TestConnectionResponse,
)
from app.services import store_service

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["stores"])


@router.get("/stores", response_model=list[StoreResponse])
async def list_stores(db: AsyncSession = Depends(get_db)) -> list[StoreResponse]:
    """Return all active stores (``shopify_access_token`` excluded)."""
    stores = await store_service.list_stores(db)
    return [StoreResponse.model_validate(s) for s in stores]


@router.post("/stores", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
async def create_store(
    body: StoreCreate,
    db: AsyncSession = Depends(get_db),
) -> StoreResponse:
    """Create a new Shopify store configuration.

    The ``shopify_access_token`` is encrypted before being persisted and is
    never returned by any endpoint.
    """
    try:
        store = await store_service.create_store(db, body)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A store with domain '{body.shopify_domain}' already exists",
        )
    return StoreResponse.model_validate(store)


@router.get("/stores/{store_id}", response_model=StoreResponse)
async def get_store(
    store_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StoreResponse:
    """Fetch a single active store by ID."""
    try:
        store = await store_service.get_store(db, store_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return StoreResponse.model_validate(store)


@router.put("/stores/{store_id}", response_model=StoreResponse)
async def update_store(
    store_id: uuid.UUID,
    body: StoreUpdate,
    db: AsyncSession = Depends(get_db),
) -> StoreResponse:
    """Update a store's ``name`` and/or ``settings``."""
    try:
        store = await store_service.update_store(db, store_id, body)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return StoreResponse.model_validate(store)


@router.delete("/stores/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_store(
    store_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete a store (sets ``is_active = False``)."""
    try:
        await store_service.delete_store(db, store_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/stores/{store_id}/test-connection",
    response_model=TestConnectionResponse,
)
async def test_connection(
    store_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TestConnectionResponse:
    """Test the Shopify API connection for a store.

    Calls ``GET /admin/api/2024-10/shop.json`` using the stored (decrypted)
    access token and returns plan/currency/name from the response.
    """
    try:
        store = await store_service.get_store(db, store_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    try:
        result = await store_service.test_shopify_connection(store)
    except ExternalAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )

    return TestConnectionResponse(**result)
