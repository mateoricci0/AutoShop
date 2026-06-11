"""Agent logs and agent-status endpoints."""
from __future__ import annotations

import httpx
import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ase_shared.models.task import Task

from ..dependencies import get_db
from ..schemas.analytics import AgentLog, AgentStatus

logger = structlog.get_logger()

router = APIRouter(prefix="/logs", tags=["logs"])
router_agents = APIRouter(prefix="/agents", tags=["agents"])

_AGENTS = [
    {
        "id": "product-hunter",
        "name": "product-hunter",
        "display_name": "Product Hunter",
        "description": "Scraping y scoring de productos ganadores",
        "service_url": "http://product-hunter:8002",
    },
    {
        "id": "marketing",
        "name": "marketing",
        "display_name": "Marketing Agent",
        "description": "Generación de copy y assets con DeepSeek",
        "service_url": "http://marketing:8003",
    },
    {
        "id": "image-pipeline",
        "name": "image-pipeline",
        "display_name": "Image Pipeline",
        "description": "Generación de imágenes con DALL·E / Stability AI",
        "service_url": "http://image-pipeline:8004",
    },
    {
        "id": "shopify-publisher",
        "name": "shopify-publisher",
        "display_name": "Shopify Publisher",
        "description": "Publicación automatizada en Shopify Admin API",
        "service_url": "http://shopify-publisher:8005",
    },
    {
        "id": "analytics",
        "name": "analytics",
        "display_name": "Analytics Agent",
        "description": "Recolección de métricas y motor de decisiones",
        "service_url": "http://analytics:8006",
    },
    {
        "id": "notifications",
        "name": "notifications",
        "display_name": "Notifications",
        "description": "Envío de alertas por Discord, Telegram, Email, Slack",
        "service_url": "http://notifications:8007",
    },
]


@router_agents.get("", response_model=list[AgentStatus])
async def list_agents():
    """Return status of each service by probing /health endpoints."""
    statuses = []
    async with httpx.AsyncClient(timeout=3) as client:
        for agent in _AGENTS:
            try:
                resp = await client.get(f"{agent['service_url']}/health")
                status = "running" if resp.status_code == 200 else "error"
                last_error = None
            except Exception as exc:
                status = "unreachable"
                last_error = str(exc)[:120]

            statuses.append(AgentStatus(
                id=agent["id"],
                name=agent["name"],
                display_name=agent["display_name"],
                description=agent["description"],
                status=status,
                last_run_at=None,
                last_error=last_error,
                service_url=agent["service_url"],
            ))
    return statuses


@router.get("", response_model=list[AgentLog])
async def list_logs(
    agent_name: str | None = None,
    level: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Query agent_logs table with optional filters."""
    # Use raw Task table as a proxy for agent activity (agent_logs is partitioned)
    q = select(Task).order_by(desc(Task.created_at)).limit(limit)
    if agent_name:
        q = q.where(Task.task_name.contains(agent_name))
    result = await db.execute(q)
    tasks = result.scalars().all()

    return [
        AgentLog(
            id=str(t.id),
            agent_name=t.task_name.split(".")[0] if "." in t.task_name else t.task_name,
            level="ERROR" if t.status == "failure" else "INFO",
            message=t.error_message or f"{t.task_name} → {t.status}",
            ai_cost=None,
            tokens_used=None,
            duration_ms=int((t.completed_at - t.started_at).total_seconds() * 1000)
            if t.completed_at and t.started_at else None,
            created_at=t.created_at.isoformat(),
        )
        for t in tasks
    ]
