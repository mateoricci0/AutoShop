"""Trigger and monitor Shopify publish jobs."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from celery.result import AsyncResult
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db
from ..schemas.publish import PublishRequest, TriggerPublishResponse, ChecklistResult, JobStatusResponse, ChecklistItem
from ..services.checklist import run_checklist
from ..tasks.celery_app import celery_app

router = APIRouter(prefix="/publish", tags=["publish"])


@router.get("/checklist", response_model=ChecklistResult)
async def get_checklist(
    candidate_id: str,
    store_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Validate a candidate is ready to publish."""
    import uuid
    result = await run_checklist(db, uuid.UUID(candidate_id), uuid.UUID(store_id))
    return ChecklistResult(
        candidate_id=result.candidate_id,
        store_id=result.store_id,
        passed=result.passed,
        items=[
            ChecklistItem(
                key=i.key,
                label=i.label,
                passed=i.passed,
                detail=i.detail,
            )
            for i in result.items
        ],
    )


@router.post("", status_code=202, response_model=TriggerPublishResponse)
async def trigger_publish(
    body: PublishRequest,
    db: AsyncSession = Depends(get_db),
):
    """Run checklist and enqueue a Shopify publish job."""
    result = await run_checklist(db, body.candidate_id, body.store_id)
    if not result.passed:
        failed = [i.label for i in result.items if not i.passed]
        raise HTTPException(
            status_code=422,
            detail=f"Checklist failed: {', '.join(failed)}",
        )

    from ..tasks.publish_tasks import publish_to_shopify

    task = publish_to_shopify.apply_async(
        kwargs={
            "candidate_id": str(body.candidate_id),
            "store_id": str(body.store_id),
            "price": str(body.price),
            "compare_at_price": str(body.compare_at_price) if body.compare_at_price else None,
            "vendor": body.vendor,
            "product_type": body.product_type,
            "publish_status": body.publish_status,
        }
    )
    return TriggerPublishResponse(
        job_id=task.id,
        status="queued",
        candidate_id=str(body.candidate_id),
        store_id=str(body.store_id),
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Poll publish job status."""
    result = AsyncResult(job_id, app=celery_app)
    state = result.state

    if state == "PENDING":
        return JobStatusResponse(job_id=job_id, status="queued")
    if state == "STARTED":
        meta = result.info or {}
        return JobStatusResponse(job_id=job_id, status="running", step=meta.get("step"))
    if state == "SUCCESS":
        return JobStatusResponse(job_id=job_id, status="completed", result=result.result)
    if state == "FAILURE":
        return JobStatusResponse(job_id=job_id, status="failed", error=str(result.result))
    return JobStatusResponse(job_id=job_id, status=state.lower())
