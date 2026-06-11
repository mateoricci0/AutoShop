"""Trigger marketing generation jobs."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult

from ..schemas.asset import GenerateRequest
from ..tasks.celery_app import celery_app

router = APIRouter(prefix="/generate", tags=["generate"])


@router.post("", status_code=202)
async def trigger_generation(body: GenerateRequest):
    """Enqueue a marketing generation job for a product candidate."""
    from ..tasks.marketing_tasks import generate_marketing_asset

    task = generate_marketing_asset.apply_async(
        kwargs={
            "candidate_id": str(body.candidate_id),
            "store_id": str(body.store_id) if body.store_id else None,
            "provider": body.provider,
        }
    )
    return {"job_id": task.id, "status": "queued", "candidate_id": str(body.candidate_id)}


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get generation job status."""
    result = AsyncResult(job_id, app=celery_app)
    state = result.state

    if state == "PENDING":
        return {"job_id": job_id, "status": "queued"}
    if state == "STARTED":
        meta = result.info or {}
        return {"job_id": job_id, "status": "running", "step": meta.get("step")}
    if state == "SUCCESS":
        return {"job_id": job_id, "status": "completed", "result": result.result}
    if state == "FAILURE":
        return {"job_id": job_id, "status": "failed", "error": str(result.result)}
    return {"job_id": job_id, "status": state.lower()}
