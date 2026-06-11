"""Celery tasks for marketing asset generation."""
from __future__ import annotations

import asyncio
import uuid

import structlog

from .celery_app import celery_app

logger = structlog.get_logger()


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="marketing.generate",
    queue="marketing.generate",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def generate_marketing_asset(self, candidate_id: str, store_id: str | None = None, provider: str | None = None):
    return run_async(_generate_async(self, candidate_id, store_id, provider))


async def _generate_async(task, candidate_id: str, store_id: str | None, provider: str | None):
    from ase_shared.database.session import AsyncSessionLocal
    from ase_shared.models.product import ProductCandidate
    from ase_shared.models.marketing import MarketingAsset
    from sqlalchemy import select

    from ..config import settings
    from ..services.llm import get_primary_provider, get_premium_provider
    from ..services.context_builder import build_product_context
    from ..services.generator import MarketingGenerator

    async with AsyncSessionLocal() as db:
        candidate = await db.get(ProductCandidate, uuid.UUID(candidate_id))
        if not candidate:
            logger.warning("candidate_not_found", candidate_id=candidate_id)
            return {"error": "Candidate not found"}

        # Check if asset already exists for this candidate
        existing = await db.execute(
            select(MarketingAsset).where(
                MarketingAsset.candidate_id == uuid.UUID(candidate_id)
            ).limit(1)
        )
        asset = existing.scalar_one_or_none()

        if not asset:
            asset = MarketingAsset(
                candidate_id=uuid.UUID(candidate_id),
                store_id=uuid.UUID(store_id) if store_id else candidate.store_id,
            )
            db.add(asset)

        asset.status = "generating"
        await db.commit()

        try:
            llm = get_primary_provider(settings)

            task.update_state(state="STARTED", meta={"step": "building_context"})
            ctx = build_product_context(candidate)

            task.update_state(state="STARTED", meta={"step": "generating_copy"})
            generator = MarketingGenerator(llm)
            result = await generator.generate(ctx)

            asset.brand_name = result.get("brand_name")
            asset.tagline = result.get("tagline")
            asset.short_description = result.get("short_description")
            asset.long_description = result.get("long_description")
            asset.bullet_points = result.get("bullet_points", [])
            asset.faqs = result.get("faqs", [])
            asset.meta_title = result.get("meta_title")
            asset.meta_description = result.get("meta_description")
            asset.keywords = result.get("keywords", [])
            asset.hooks = result.get("hooks", [])
            asset.headlines = result.get("headlines", [])
            asset.ctas = result.get("ctas", [])
            asset.ad_copies = result.get("ad_copies", [])
            asset.facebook_ads = result.get("facebook_ads", {})
            asset.instagram_ads = result.get("instagram_ads", {})
            asset.tiktok_ads = result.get("tiktok_ads", {})
            asset.google_ads = result.get("google_ads", {})
            asset.email_campaigns = result.get("email_campaigns", {})
            asset.ai_model = result.get("_model")
            asset.tokens_used = result.get("_tokens_used")
            asset.generation_cost = result.get("_cost_usd")
            asset.status = "draft"

            await db.commit()
            logger.info("marketing_asset_generated", candidate_id=candidate_id, asset_id=str(asset.id))
            return {"asset_id": str(asset.id), "candidate_id": candidate_id}

        except Exception as e:
            asset.status = "draft"
            await db.commit()
            logger.error("marketing_generation_failed", candidate_id=candidate_id, error=str(e))
            raise task.retry(exc=e)
