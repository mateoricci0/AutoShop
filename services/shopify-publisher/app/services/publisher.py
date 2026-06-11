"""Shopify publish flow orchestrator.

Steps:
1. Load candidate, marketing asset, and approved images from DB
2. Build Shopify product payload (title, body_html, vendor, tags, SEO, variants)
3. Create draft product in Shopify
4. Upload approved images to Shopify CDN (by URL — Shopify fetches from MinIO)
5. Assign product to collections derived from tags/category
6. Activate product (status → active)
7. Persist ProductPublished record in DB
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ase_shared.models.marketing import MarketingAsset, GeneratedImage
from ase_shared.models.product import ProductCandidate, ProductPublished, ProductStatus
from ase_shared.models.store import Store
from ase_shared.security.encryption import decrypt

from .shopify_client import ShopifyClient

logger = structlog.get_logger()


def _build_product_payload(
    candidate: ProductCandidate,
    asset: MarketingAsset,
    price: Decimal,
    compare_at_price: Decimal | None,
    vendor: str | None,
    product_type: str | None,
    publish_status: str,
) -> dict[str, Any]:
    title = asset.brand_name or candidate.title
    body_html = asset.long_description or asset.short_description or candidate.description or ""

    tags: list[str] = list(candidate.tags or [])
    if asset.keywords:
        tags.extend(asset.keywords[:5])
    tags = list(dict.fromkeys(tags))[:20]

    variant: dict[str, Any] = {
        "price": str(price),
        "requires_shipping": True,
        "taxable": True,
        "inventory_management": None,
    }
    if compare_at_price:
        variant["compare_at_price"] = str(compare_at_price)

    payload: dict[str, Any] = {
        "title": title,
        "body_html": body_html,
        "vendor": vendor or (asset.brand_name or ""),
        "product_type": product_type or (candidate.category or ""),
        "tags": ",".join(tags),
        "status": "draft",
        "variants": [variant],
    }

    if asset.meta_title or asset.meta_description:
        payload["metafields_global_title_tag"] = asset.meta_title or title
        payload["metafields_global_description_tag"] = asset.meta_description or ""

    return payload


async def publish_to_shopify(
    db: AsyncSession,
    candidate_id: uuid.UUID,
    store_id: uuid.UUID,
    price: Decimal,
    compare_at_price: Decimal | None,
    vendor: str | None,
    product_type: str | None,
    publish_status: str,
    api_version: str,
    update_step: Any = None,
) -> ProductPublished:
    def step(s: str) -> None:
        logger.info("publish_step", step=s, candidate_id=str(candidate_id))
        if update_step:
            update_step(s)

    step("loading_data")
    candidate = await db.get(ProductCandidate, candidate_id)
    store = await db.get(Store, store_id)

    asset_res = await db.execute(
        select(MarketingAsset).where(MarketingAsset.candidate_id == candidate_id).limit(1)
    )
    asset = asset_res.scalar_one_or_none()

    images_res = await db.execute(
        select(GeneratedImage).where(
            GeneratedImage.candidate_id == candidate_id,
            GeneratedImage.status == "approved",
        )
    )
    images = images_res.scalars().all()

    access_token = decrypt(store.shopify_access_token)
    client = ShopifyClient(store.shopify_domain, access_token, api_version)

    step("creating_product")
    payload = _build_product_payload(
        candidate, asset, price, compare_at_price, vendor, product_type, publish_status
    )
    shopify_product = await client.create_product(payload)
    shopify_id = str(shopify_product["id"])
    logger.info("shopify_product_created", shopify_id=shopify_id)

    step("uploading_images")
    shopify_images = []
    for img in images:
        if img.storage_url:
            try:
                shopify_img = await client.add_product_image(
                    shopify_id, img.storage_url, alt=f"{candidate.title} — {img.type}"
                )
                shopify_images.append(shopify_img)
            except Exception as exc:
                logger.warning("image_upload_failed", image_id=str(img.id), error=str(exc))

    step("assigning_collections")
    collection_ids: list[str] = []
    if candidate.category:
        existing = await client.list_custom_collections()
        found = next((c for c in existing if c["title"].lower() == candidate.category.lower()), None)
        if found:
            coll = found
        else:
            coll = await client.create_custom_collection(candidate.category)
        try:
            await client.add_collect(shopify_id, str(coll["id"]))
            collection_ids.append(str(coll["id"]))
        except Exception as exc:
            logger.warning("collection_assign_failed", error=str(exc))

    step("activating_product")
    if publish_status == "active":
        await client.update_product(shopify_id, {"status": "active"})

    shopify_handle = shopify_product.get("handle")
    variant_ids = [str(v["id"]) for v in shopify_product.get("variants", [])]

    step("persisting_record")
    candidate.status = ProductStatus.published
    await db.flush()

    published = ProductPublished(
        candidate_id=candidate_id,
        store_id=store_id,
        shopify_product_id=shopify_id,
        shopify_variant_ids=variant_ids,
        shopify_collection_ids=collection_ids,
        shopify_handle=shopify_handle,
        title=asset.brand_name or candidate.title,
        description_html=asset.long_description or asset.short_description or "",
        vendor=vendor or asset.brand_name or "",
        product_type=product_type or candidate.category or "",
        tags=list(candidate.tags or []),
        price=price,
        compare_at_price=compare_at_price,
        cost_per_item=candidate.cost,
        seo_title=asset.meta_title if asset else None,
        seo_description=asset.meta_description if asset else None,
        variants=[{"id": vid, "price": str(price)} for vid in variant_ids],
        options=[],
        images=[{"id": si["id"], "src": si["src"]} for si in shopify_images],
        status=publish_status,
        published_at=datetime.now(timezone.utc) if publish_status == "active" else None,
    )
    db.add(published)
    await db.commit()
    await db.refresh(published)

    logger.info(
        "publish_complete",
        candidate_id=str(candidate_id),
        published_id=str(published.id),
        shopify_id=shopify_id,
    )
    return published
