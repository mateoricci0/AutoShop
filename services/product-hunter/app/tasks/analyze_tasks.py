import asyncio
from ..tasks.celery_app import celery_app
import structlog

logger = structlog.get_logger()


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="products.analyze.score_candidate",
    queue="products.analyze",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def score_candidate(self, candidate_id: str):
    return run_async(_score_candidate_async(self, candidate_id))


async def _score_candidate_async(task, candidate_id: str):
    from ase_shared.database.session import AsyncSessionLocal
    from ase_shared.models.product import ProductCandidate
    from ..services.scorer import get_scorer
    from ..services.normalizer import NormalizedProduct
    from datetime import datetime, timezone
    import uuid

    async with AsyncSessionLocal() as db:
        candidate = await db.get(ProductCandidate, uuid.UUID(candidate_id))
        if not candidate:
            logger.warning("candidate_not_found", candidate_id=candidate_id)
            return

        candidate.status = "analyzing"
        await db.commit()

        try:
            scorer = get_scorer()
            # Build NormalizedProduct from DB candidate
            norm = NormalizedProduct(
                title=candidate.title,
                source=candidate.source,
                source_url=candidate.source_url,
                source_product_id=candidate.source_product_id,
                description=candidate.description,
                cost=float(candidate.cost) if candidate.cost else None,
                recommended_price=float(candidate.recommended_price) if candidate.recommended_price else None,
                estimated_margin=float(candidate.estimated_margin) if candidate.estimated_margin else None,
                images=candidate.images or [],
                category=candidate.category,
                tags=candidate.tags or [],
                raw_data=candidate.raw_data or {},
                engagement_summary="",
            )

            result = await scorer.score(norm)

            candidate.demand_score      = result.demand_score
            candidate.competition_score = result.competition_score
            candidate.trend_score       = result.trend_score
            candidate.engagement_score  = result.engagement_score
            candidate.saturation_score  = result.saturation_score
            candidate.branding_score    = result.branding_score
            candidate.margin_score      = result.margin_score
            candidate.success_score     = result.success_score
            candidate.ai_analysis       = {"analysis": result.analysis}
            candidate.ai_model          = result.model
            candidate.ai_tokens_used    = result.tokens_used
            candidate.ai_cost           = result.cost_usd
            candidate.analyzed_at       = datetime.now(timezone.utc)
            candidate.status            = "pending"  # back to pending for human review

            if result.recommended_price and not candidate.recommended_price:
                candidate.recommended_price = result.recommended_price
            if result.estimated_margin and not candidate.estimated_margin:
                candidate.estimated_margin = result.estimated_margin

            await db.commit()
            logger.info("candidate_scored", candidate_id=candidate_id, score=result.success_score)
            return {"candidate_id": candidate_id, "success_score": result.success_score}

        except Exception as e:
            candidate.status = "pending"
            candidate.ai_analysis = {"error": str(e)}
            await db.commit()
            logger.error("scoring_failed", candidate_id=candidate_id, error=str(e))
            raise task.retry(exc=e)


@celery_app.task(
    name="products.analyze.batch_score",
    queue="products.analyze",
)
def batch_score(limit: int = 50):
    """Score all unscored pending candidates."""
    return run_async(_batch_score_async(limit))


async def _batch_score_async(limit: int):
    from ase_shared.database.session import AsyncSessionLocal
    from ase_shared.models.product import ProductCandidate
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ProductCandidate)
            .where(ProductCandidate.status == "pending")
            .where(ProductCandidate.success_score.is_(None))
            .limit(limit)
        )
        candidates = result.scalars().all()

    for c in candidates:
        score_candidate.delay(str(c.id))

    logger.info("batch_score_queued", count=len(candidates))
    return {"queued": len(candidates)}
