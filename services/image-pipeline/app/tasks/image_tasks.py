"""Celery tasks for image generation."""
from __future__ import annotations

import asyncio
import uuid

import structlog

from .celery_app import celery_app

logger = structlog.get_logger()

IMAGE_TYPES_ALL = ["hero", "lifestyle", "infographic", "before_after", "banner", "ad_square", "ad_story"]


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="images.generate",
    queue="images.generate",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def generate_product_images(
    self,
    candidate_id: str,
    store_id: str | None = None,
    image_types: list[str] | None = None,
    provider: str | None = None,
):
    return run_async(_generate_images_async(self, candidate_id, store_id, image_types, provider))


async def _generate_images_async(task, candidate_id: str, store_id: str | None, image_types: list[str] | None, provider: str | None):
    from ase_shared.database.session import AsyncSessionLocal
    from ase_shared.models.product import ProductCandidate
    from ase_shared.models.marketing import GeneratedImage
    from sqlalchemy import select

    from ..config import settings
    from ..services.providers import get_provider, OpenAIDALLEProvider, StabilityAIProvider
    from ..services.providers.base import ImageSize
    from ..services.prompt_generator import generate_prompts
    from ..services.quality_reviewer import review_image
    from ..services.storage import get_storage

    types_to_generate = image_types or IMAGE_TYPES_ALL
    results = []

    async with AsyncSessionLocal() as db:
        candidate = await db.get(ProductCandidate, uuid.UUID(candidate_id))
        if not candidate:
            logger.warning("candidate_not_found", candidate_id=candidate_id)
            return {"error": "Candidate not found"}

        # Resolve provider
        if provider == "openai":
            img_provider = OpenAIDALLEProvider(settings.OPENAI_API_KEY)
        elif provider == "stability":
            from ..services.providers.stability_ai import StabilityAIProvider as _S
            img_provider = _S(settings.STABILITY_API_KEY)
        else:
            img_provider = get_provider(settings)

        storage = get_storage(settings)

        # Get marketing asset for brand context (optional)
        from ase_shared.models.marketing import MarketingAsset
        asset_result = await db.execute(
            select(MarketingAsset)
            .where(MarketingAsset.candidate_id == uuid.UUID(candidate_id))
            .limit(1)
        )
        asset = asset_result.scalar_one_or_none()

        prompts = generate_prompts(
            product_title=candidate.title,
            category=candidate.category,
            description=candidate.description,
            brand_name=asset.brand_name if asset else None,
            tagline=asset.tagline if asset else None,
        )

        prompts_to_run = [p for p in prompts if p.image_type in types_to_generate]
        total = len(prompts_to_run)

        for idx, spec in enumerate(prompts_to_run):
            task.update_state(
                state="STARTED",
                meta={"progress": f"{idx}/{total}", "type": spec.image_type},
            )

            # Check if image for this type already exists
            existing = await db.execute(
                select(GeneratedImage)
                .where(GeneratedImage.candidate_id == uuid.UUID(candidate_id))
                .where(GeneratedImage.type == spec.image_type)
                .limit(1)
            )
            existing_img = existing.scalar_one_or_none()

            size = ImageSize({"square": "1024x1024", "landscape": "1792x1024", "portrait": "1024x1792"}[spec.size])

            db_image = existing_img or GeneratedImage(
                candidate_id=uuid.UUID(candidate_id),
                store_id=uuid.UUID(store_id) if store_id else candidate.store_id,
                type=spec.image_type,
                prompt=spec.prompt,
                negative_prompt=spec.negative_prompt,
            )

            if not existing_img:
                db_image.prompt = spec.prompt
                db_image.negative_prompt = spec.negative_prompt

            db_image.status = "generating"
            db.add(db_image)
            await db.commit()

            try:
                result = await img_provider.generate(
                    spec.prompt,
                    negative_prompt=spec.negative_prompt,
                    size=size,
                )

                status, clip_score = await review_image(result.image_bytes, spec.prompt)

                # If needs_review and not first try, attempt once more
                if status == "needs_review" and db_image.retry_count < 1:
                    db_image.retry_count += 1
                    await db.commit()
                    result2 = await img_provider.generate(spec.prompt, negative_prompt=spec.negative_prompt, size=size)
                    status2, clip_score2 = await review_image(result2.image_bytes, spec.prompt)
                    if clip_score2 is None or (clip_score2 and clip_score2 > (clip_score or 0)):
                        result = result2
                        status = status2
                        clip_score = clip_score2

                effective_store = store_id or (str(candidate.store_id) if candidate.store_id else "default")
                storage_key, storage_url = storage.upload(
                    result.image_bytes,
                    store_id=effective_store,
                    candidate_id=candidate_id,
                    image_type=spec.image_type,
                    fmt=result.format,
                )

                db_image.storage_key = storage_key
                db_image.storage_url = storage_url
                db_image.thumbnail_url = storage_url  # same URL; thumbnail resize in v2
                db_image.width = result.width
                db_image.height = result.height
                db_image.format = result.format
                db_image.file_size_bytes = len(result.image_bytes)
                db_image.model = result.model
                db_image.provider = result.provider
                db_image.generation_cost = result.cost_usd
                db_image.generation_time_ms = result.generation_time_ms
                db_image.clip_score = clip_score
                db_image.status = status
                db_image.error_message = None

                await db.commit()
                results.append({"type": spec.image_type, "image_id": str(db_image.id), "status": status})
                logger.info("image_generated", type=spec.image_type, candidate_id=candidate_id)

            except Exception as e:
                db_image.status = "failed"
                db_image.error_message = str(e)
                await db.commit()
                results.append({"type": spec.image_type, "status": "failed", "error": str(e)})
                logger.error("image_generation_failed", type=spec.image_type, error=str(e))

    return {"candidate_id": candidate_id, "results": results, "total": total}


@celery_app.task(
    name="images.regenerate",
    queue="images.generate",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def regenerate_image(self, image_id: str, provider: str | None = None):
    return run_async(_regenerate_async(self, image_id, provider))


async def _regenerate_async(task, image_id: str, provider: str | None):
    from ase_shared.database.session import AsyncSessionLocal
    from ase_shared.models.marketing import GeneratedImage

    from ..config import settings
    from ..services.providers import get_provider, OpenAIDALLEProvider
    from ..services.providers.base import ImageSize
    from ..services.quality_reviewer import review_image
    from ..services.storage import get_storage

    async with AsyncSessionLocal() as db:
        img = await db.get(GeneratedImage, uuid.UUID(image_id))
        if not img:
            return {"error": "Image not found"}

        if provider == "openai":
            img_provider = OpenAIDALLEProvider(settings.OPENAI_API_KEY)
        elif provider == "stability":
            from ..services.providers.stability_ai import StabilityAIProvider
            img_provider = StabilityAIProvider(settings.STABILITY_API_KEY)
        else:
            img_provider = get_provider(settings)

        storage = get_storage(settings)

        # Infer size from type
        size_map = {
            "hero": ImageSize.square,
            "lifestyle": ImageSize.landscape,
            "infographic": ImageSize.square,
            "before_after": ImageSize.landscape,
            "banner": ImageSize.landscape,
            "ad_square": ImageSize.square,
            "ad_story": ImageSize.portrait,
        }
        size = size_map.get(img.type, ImageSize.square)

        img.status = "generating"
        img.retry_count += 1
        await db.commit()

        try:
            result = await img_provider.generate(img.prompt, negative_prompt=img.negative_prompt, size=size)
            status, clip_score = await review_image(result.image_bytes, img.prompt)

            candidate_id = str(img.candidate_id) if img.candidate_id else "unknown"
            store_id = str(img.store_id) if img.store_id else "default"
            storage_key, storage_url = storage.upload(
                result.image_bytes,
                store_id=store_id,
                candidate_id=candidate_id,
                image_type=img.type,
                fmt=result.format,
            )

            img.storage_key = storage_key
            img.storage_url = storage_url
            img.thumbnail_url = storage_url
            img.width = result.width
            img.height = result.height
            img.format = result.format
            img.file_size_bytes = len(result.image_bytes)
            img.model = result.model
            img.provider = result.provider
            img.generation_cost = result.cost_usd
            img.generation_time_ms = result.generation_time_ms
            img.clip_score = clip_score
            img.status = status
            img.error_message = None
            await db.commit()

            return {"image_id": image_id, "status": status}

        except Exception as e:
            img.status = "failed"
            img.error_message = str(e)
            await db.commit()
            raise task.retry(exc=e)
