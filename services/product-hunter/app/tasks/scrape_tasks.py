import asyncio
from celery import Task
from ..tasks.celery_app import celery_app
import structlog

logger = structlog.get_logger()


def run_async(coro):
    """Run async coroutine in Celery sync worker."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="products.scrape.hunt_products",
    queue="products.scrape",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    track_started=True,
)
def hunt_products(self: Task, store_id: str | None = None, sources: list[str] | None = None, force: bool = False):
    """
    Main orchestration task.
    Scrapes all enabled sources, normalizes, deduplicates,
    inserts into DB, and triggers scoring for each new candidate.
    """
    return run_async(_hunt_products_async(self, store_id, sources, force))


async def _hunt_products_async(task, store_id, sources, force):
    from ..services.scrapers import (
        GoogleTrendsScraper, RedditScraper, AmazonScraper,
        AliExpressScraper, TikTokCreativeScraper, FacebookAdsScraper, TemuScraper,
        ScraperUnavailable,
    )
    from ..services.normalizer import normalize
    from ..services.deduplicator import filter_duplicates, mark_seen
    from ..config import settings
    from ase_shared.database.session import AsyncSessionLocal
    from ase_shared.models.product import ProductCandidate
    from ase_shared.cache.redis import get_redis_client
    import uuid
    from datetime import datetime, timezone

    run_id = str(uuid.uuid4())
    logger.info("hunt_started", run_id=run_id, store_id=store_id, sources=sources)

    all_scrapers = [
        GoogleTrendsScraper(),
        RedditScraper(),
        AmazonScraper(),
        AliExpressScraper(),
        TikTokCreativeScraper(apify_api_key=settings.APIFY_API_KEY),
        FacebookAdsScraper(apify_api_key=settings.APIFY_API_KEY),
        TemuScraper(),
    ]

    enabled_scrapers = [
        s for s in all_scrapers
        if sources is None or s.name in sources
    ]

    redis = await get_redis_client()
    total_new = 0

    for scraper in enabled_scrapers:
        try:
            logger.info("scraper_starting", scraper=scraper.name)
            raw_products = await scraper.scrape(limit=settings.SCRAPE_LIMIT_PER_SOURCE)
            logger.info("scraper_done", scraper=scraper.name, count=len(raw_products))
        except ScraperUnavailable as e:
            logger.warning("scraper_unavailable", scraper=scraper.name, reason=str(e))
            continue
        except Exception as e:
            logger.error("scraper_failed", scraper=scraper.name, error=str(e))
            continue

        # Dedup against raw products (before normalization, uses compute_hash)
        unique_raw, dup_count = await filter_duplicates(redis, raw_products, force=force)
        unique_normalized = [normalize(p) for p in unique_raw]
        logger.info("dedup_done", scraper=scraper.name, unique=len(unique_normalized), dupes=dup_count)

        # Insert into DB
        async with AsyncSessionLocal() as db:
            for norm, raw in zip(unique_normalized, unique_raw):
                product_hash = raw.compute_hash()
                candidate = ProductCandidate(
                    store_id=uuid.UUID(store_id) if store_id else None,
                    title=norm.title,
                    description=norm.description,
                    source=norm.source,
                    source_url=norm.source_url,
                    source_product_id=norm.source_product_id,
                    source_hash=product_hash,
                    cost=norm.cost,
                    recommended_price=norm.recommended_price,
                    estimated_margin=norm.estimated_margin,
                    category=norm.category,
                    tags=norm.tags,
                    images=norm.images,
                    raw_data=norm.raw_data,
                    status="pending",
                    scraped_at=datetime.now(timezone.utc),
                )
                db.add(candidate)
                try:
                    await db.flush()
                    # Mark as seen in Redis
                    await mark_seen(redis, product_hash)
                    # Trigger scoring
                    from ..tasks.analyze_tasks import score_candidate
                    score_candidate.delay(str(candidate.id))
                    total_new += 1
                except Exception as e:
                    await db.rollback()
                    logger.error("candidate_insert_failed", error=str(e), title=norm.title[:50])
                    continue
            try:
                await db.commit()
            except Exception as e:
                logger.error("db_commit_failed", error=str(e))

    logger.info("hunt_complete", run_id=run_id, total_new=total_new)
    return {"run_id": run_id, "total_new": total_new}
