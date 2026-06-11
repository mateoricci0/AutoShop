"""Scheduler jobs — list and patch frequency."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from celery.schedules import crontab

from ..schemas.analytics import ScheduledJobItem, UpdateJobRequest
from ..tasks.analytics_tasks import celery_app

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _beat_entry_to_item(name: str, entry: dict) -> ScheduledJobItem:
    schedule = entry.get("schedule")
    if isinstance(schedule, crontab):
        minute = getattr(schedule, "_orig_minute", "*")
        hour = getattr(schedule, "_orig_hour", "*")
        cron_str = f"{minute} {hour} * * *"
    else:
        every = getattr(schedule, "run_every", None)
        seconds = int(every.total_seconds()) if every else 0
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        cron_str = f"every {hours}h {minutes}m" if hours else f"every {minutes}m"

    disabled = entry.get("options", {}).get("expires") == 0
    return ScheduledJobItem(
        id=name,
        name=name,
        task=entry.get("task", ""),
        cron=cron_str,
        enabled=not disabled,
        last_run_at=None,
    )


@router.get("", response_model=list[ScheduledJobItem])
async def list_jobs():
    schedule = celery_app.conf.beat_schedule or {}
    return [_beat_entry_to_item(name, entry) for name, entry in schedule.items()]


@router.patch("/{job_id}", response_model=ScheduledJobItem)
async def update_job(job_id: str, body: UpdateJobRequest):
    schedule = celery_app.conf.beat_schedule or {}
    if job_id not in schedule:
        raise HTTPException(status_code=404, detail="Job not found")

    entry = schedule[job_id]
    if body.enabled is not None:
        opts = entry.setdefault("options", {})
        if not body.enabled:
            opts["expires"] = 0
        else:
            opts.pop("expires", None)

    return _beat_entry_to_item(job_id, entry)
