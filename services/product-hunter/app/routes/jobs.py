from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult
from ..schemas.candidate import HuntJobRequest
from ..tasks.celery_app import celery_app

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/hunt", status_code=202)
async def trigger_hunt(body: HuntJobRequest):
    """Trigger a product hunt job. Returns the Celery task ID."""
    from ..tasks.scrape_tasks import hunt_products

    task = hunt_products.apply_async(
        kwargs={
            "store_id": str(body.store_id) if body.store_id else None,
            "sources": body.sources,
            "force": body.force,
        }
    )
    return {"job_id": task.id, "status": "queued"}


@router.get("/{job_id}")
async def get_job_status(job_id: str):
    """Get the status and result of a hunt job."""
    result = AsyncResult(job_id, app=celery_app)

    state = result.state
    info: dict = {}

    if state == "PENDING":
        info = {"status": "queued"}
    elif state == "STARTED":
        info = {"status": "running"}
    elif state == "SUCCESS":
        info = {"status": "completed", "result": result.result}
    elif state == "FAILURE":
        info = {"status": "failed", "error": str(result.result)}
    else:
        info = {"status": state.lower()}

    return {"job_id": job_id, **info}
