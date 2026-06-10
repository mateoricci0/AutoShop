"""Business logic for store management."""

from __future__ import annotations

import uuid
from typing import Sequence

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ase_shared.exceptions import ExternalAPIError, NotFoundError
from ase_shared.models.store import Store
from ase_shared.security.encryption import decrypt, encrypt

from app.schemas.store import StoreCreate, StoreUpdate

logger = structlog.get_logger(__name__)


async def get_store(db: AsyncSession, store_id: uuid.UUID) -> Store:
    """Fetch a single active store by primary key.

    Raises:
        NotFoundError: if the store does not exist or is inactive.
    """
    result = await db.execute(
        select(Store).where(Store.id == store_id, Store.is_active.is_(True))
    )
    store = result.scalar_one_or_none()
    if store is None:
        raise NotFoundError(f"Store {store_id} not found")
    return store


async def list_stores(db: AsyncSession) -> Sequence[Store]:
    """Return all active stores ordered by name."""
    result = await db.execute(
        select(Store).where(Store.is_active.is_(True)).order_by(Store.name)
    )
    return result.scalars().all()


async def create_store(db: AsyncSession, data: StoreCreate) -> Store:
    """Create a new store, encrypting the Shopify access token.

    Args:
        db: Active async DB session.
        data: Validated store creation payload.

    Returns:
        The persisted :class:`Store` ORM instance.
    """
    encrypted_token = encrypt(data.shopify_access_token)
    store = Store(
        name=data.name,
        shopify_domain=data.shopify_domain,
        shopify_access_token=encrypted_token,
        currency=data.currency,
        timezone=data.timezone,
    )
    db.add(store)
    await db.commit()
    await db.refresh(store)
    logger.info("store_created", store_id=str(store.id), domain=store.shopify_domain)
    return store


async def update_store(
    db: AsyncSession, store_id: uuid.UUID, data: StoreUpdate
) -> Store:
    """Partially update a store's ``name`` and/or ``settings``.

    Raises:
        NotFoundError: if the store does not exist or is inactive.
    """
    store = await get_store(db, store_id)
    if data.name is not None:
        store.name = data.name
    if data.settings is not None:
        store.settings = data.settings
    await db.commit()
    await db.refresh(store)
    logger.info("store_updated", store_id=str(store.id))
    return store


async def delete_store(db: AsyncSession, store_id: uuid.UUID) -> None:
    """Soft-delete a store by setting ``is_active = False``.

    Raises:
        NotFoundError: if the store does not exist or is already inactive.
    """
    store = await get_store(db, store_id)
    store.is_active = False
    await db.commit()
    logger.info("store_deleted", store_id=str(store.id))


async def test_shopify_connection(store: Store) -> dict:
    """Call Shopify's ``shop.json`` endpoint to verify credentials.

    Args:
        store: The ORM store instance.  Its ``shopify_access_token`` will be
            decrypted before use.

    Returns:
        A dict with keys: ``ok``, ``shopify_plan``, ``currency``, ``shop_name``.

    Raises:
        ExternalAPIError: if Shopify returns a non-200 status.
    """
    decrypted_token = decrypt(store.shopify_access_token)
    url = f"https://{store.shopify_domain}/admin/api/2024-10/shop.json"

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            url,
            headers={"X-Shopify-Access-Token": decrypted_token},
        )

    if resp.status_code != 200:
        raise ExternalAPIError(
            f"Shopify returned {resp.status_code}",
            status_code=resp.status_code,
            provider="shopify",
        )

    shop = resp.json()["shop"]
    return {
        "ok": True,
        "shopify_plan": shop["plan_name"],
        "currency": shop["currency"],
        "shop_name": shop["name"],
    }
