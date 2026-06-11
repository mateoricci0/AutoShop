"""Trigger image generation jobs."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult

from ..schemas.image import GenerateImagesRequest, RegenerateImageRequest
from ..tasks.celery_app import celery_app

router = APIRouter(prefix="/generate", tags=["generate"])


@router.post("", status_code=202)
async def trigger_generation(body: GenerateImagesRequest):
    """Enqueue image generation for all 7 types (or a subset)."""
    from ..tasks.image_tasks import generate_product_images

    task = generate_product_images.apply_async(
        kwargs={
            "candidate_id": str(body.candidate_id),
            "store_id": str(body.store_id) if body.store_id else None,
            "image_types": body.image_types,
            "provider": body.provider,
        }
    )
    return {"job_id": task.id, "status": "queued", "candidate_id": str(body.candidate_id)}


@router.post("/regenerate", status_code=202)
async def regenerate_single(body: RegenerateImageRequest):
    """Re-generate a single image by its ID."""
    from ..tasks.image_tasks import regenerate_image

    task = regenerate_image.apply_async(
        kwargs={
            "image_id": str(body.image_id),
            "provider": body.provider,
        }
    )
    return {"job_id": task.id, "status": "queued", "image_id": str(body.image_id)}


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    result = AsyncResult(job_id, app=celery_app)
    state = result.state

    if state == "PENDING":
        return {"job_id": job_id, "status": "queued"}
    if state == "STARTED":
        meta = result.info or {}
        return {"job_id": job_id, "status": "running", "progress": meta.get("progress")}
    if state == "SUCCESS":
        return {"job_id": job_id, "status": "completed", "result": result.result}
    if state == "FAILURE":
        return {"job_id": job_id, "status": "failed", "error": str(result.result)}
    return {"job_id": job_id, "status": state.lower()}
