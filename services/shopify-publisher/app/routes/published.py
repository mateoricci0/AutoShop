"""CRUD for published products."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ase_shared.models.product import ProductPublished, ProductStatus

from ..dependencies import get_db
from ..schemas.publish import PublishedProductDetail, PublishedProductListItem, ArchiveRequest
from ..services.shopify_client import ShopifyClient
from ase_shared.security.encryption import decrypt
from ase_shared.models.store import Store

router = APIRouter(prefix="/published", tags=["published"])


@router.get("", response_model=dict)
async def list_published(
    store_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List published products with optional filters."""
    q = select(ProductPublished)
    if store_id:
        q = q.where(ProductPublished.store_id == uuid.UUID(store_id))
    if status:
        q = q.where(ProductPublished.status == status)
    q = q.order_by(ProductPublished.created_at.desc()).offset(offset).limit(limit)

    count_q = select(func.count()).select_from(ProductPublished)
    if store_id:
        count_q = count_q.where(ProductPublished.store_id == uuid.UUID(store_id))
    if status:
        count_q = count_q.where(ProductPublished.status == status)

    results = await db.execute(q)
    total = (await db.execute(count_q)).scalar_one()
    items = results.scalars().all()

    return {
        "items": [PublishedProductListItem.model_validate(p) for p in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{id}", response_model=PublishedProductDetail)
async def get_published(id: str, db: AsyncSession = Depends(get_db)):
    """Get a single published product by ID."""
    product = await db.get(ProductPublished, uuid.UUID(id))
    if not product:
        raise HTTPException(status_code=404, detail="Published product not found")
    return PublishedProductDetail.model_validate(product)


@router.post("/{id}/sync")
async def sync_from_shopify(id: str, db: AsyncSession = Depends(get_db)):
    """Pull latest data from Shopify and update our record."""
    from ..config import settings

    product = await db.get(ProductPublished, uuid.UUID(id))
    if not product:
        raise HTTPException(status_code=404, detail="Published product not found")
    if not product.shopify_product_id:
        raise HTTPException(status_code=422, detail="No Shopify product ID on record")

    store = await db.get(Store, product.store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    access_token = decrypt(store.shopify_access_token)
    client = ShopifyClient(store.shopify_domain, access_token, settings.SHOPIFY_API_VERSION)
    shopify_product = await client.get_product(product.shopify_product_id)

    product.status = shopify_product.get("status", product.status)
    product.shopify_handle = shopify_product.get("handle", product.shopify_handle)
    product.shopify_variant_ids = [str(v["id"]) for v in shopify_product.get("variants", [])]
    product.images = [{"id": i["id"], "src": i["src"]} for i in shopify_product.get("images", [])]
    from datetime import timezone
    from datetime import datetime
    product.last_synced_at = datetime.now(timezone.utc)
    await db.commit()

    return {"status": "synced", "shopify_status": shopify_product.get("status")}


@router.patch("/{id}/archive")
async def archive_published(
    id: str,
    body: ArchiveRequest,
    db: AsyncSession = Depends(get_db),
):
    """Archive a published product (in Shopify + mark locally)."""
    from ..config import settings

    product = await db.get(ProductPublished, uuid.UUID(id))
    if not product:
        raise HTTPException(status_code=404, detail="Published product not found")

    if product.shopify_product_id:
        store = await db.get(Store, product.store_id)
        if store:
            access_token = decrypt(store.shopify_access_token)
            client = ShopifyClient(store.shopify_domain, access_token, settings.SHOPIFY_API_VERSION)
            try:
                await client.archive_product(product.shopify_product_id)
            except Exception:
                pass

    product.status = "archived"
    await db.commit()
    return {"status": "archived", "id": id}
