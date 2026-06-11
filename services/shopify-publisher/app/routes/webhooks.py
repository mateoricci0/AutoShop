"""Shopify webhook receiver.

Shopify sends webhooks when products are updated/deleted externally.
We verify the HMAC signature and update our local record accordingly.
"""
from __future__ import annotations

import hashlib
import hmac
import os

import structlog
from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from ase_shared.models.product import ProductPublished

from ..dependencies import get_db

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

logger = structlog.get_logger()


def _verify_hmac(body: bytes, shopify_hmac: str) -> bool:
    secret = os.environ.get("SHOPIFY_WEBHOOK_SECRET", "")
    if not secret:
        return True  # not configured — skip verification in dev
    digest = hmac.new(secret.encode(), body, hashlib.sha256).digest()
    import base64
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(expected, shopify_hmac)


@router.post("/shopify")
async def receive_shopify_webhook(
    request: Request,
    x_shopify_hmac_sha256: str = Header(default=""),
    x_shopify_topic: str = Header(default=""),
    db: AsyncSession = Depends(get_db),
):
    """Handle incoming Shopify webhook events."""
    body = await request.body()

    if not _verify_hmac(body, x_shopify_hmac_sha256):
        raise HTTPException(status_code=401, detail="Invalid HMAC signature")

    try:
        import json
        payload = json.loads(body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    topic = x_shopify_topic
    logger.info("shopify_webhook_received", topic=topic, id=payload.get("id"))

    shopify_id = str(payload.get("id", ""))

    if topic in ("products/update", "products/delete"):
        result = await db.execute(
            select(ProductPublished).where(
                ProductPublished.shopify_product_id == shopify_id
            ).limit(1)
        )
        product = result.scalar_one_or_none()
        if product:
            if topic == "products/delete":
                product.status = "deleted"
                logger.info("product_deleted_via_webhook", shopify_id=shopify_id)
            elif topic == "products/update":
                new_status = payload.get("status")
                if new_status:
                    product.status = new_status
                logger.info("product_updated_via_webhook", shopify_id=shopify_id, status=new_status)
            await db.commit()

    return {"ok": True, "topic": topic}
