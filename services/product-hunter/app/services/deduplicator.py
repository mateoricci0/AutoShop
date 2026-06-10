import redis.asyncio as aioredis
import structlog
from .scrapers.base import ScrapedProduct

logger = structlog.get_logger()

DEDUP_PREFIX = "ase:product_hash:"
DEDUP_TTL_SECONDS = 60 * 60 * 24 * 30  # 30 days


async def is_duplicate(redis: aioredis.Redis, product_hash: str) -> bool:
    return bool(await redis.exists(f"{DEDUP_PREFIX}{product_hash}"))


async def mark_seen(redis: aioredis.Redis, product_hash: str) -> None:
    await redis.setex(f"{DEDUP_PREFIX}{product_hash}", DEDUP_TTL_SECONDS, "1")


async def filter_duplicates(
    redis: aioredis.Redis,
    products: list[ScrapedProduct],
    force: bool = False,
) -> tuple[list[ScrapedProduct], int]:
    """
    Returns (unique_products, duplicate_count).
    If force=True, skips dedup check (but still computes hashes).
    """
    if force:
        return products, 0

    unique = []
    dup_count = 0

    for product in products:
        product_hash = product.compute_hash()
        if await is_duplicate(redis, product_hash):
            dup_count += 1
            logger.debug("product_duplicate_skipped", title=product.title[:50], source=product.source)
        else:
            unique.append(product)

    logger.info("dedup_complete", total=len(products), unique=len(unique), duplicates=dup_count)
    return unique, dup_count
