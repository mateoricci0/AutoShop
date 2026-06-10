from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc, nulls_last
from ase_shared.models.product import ProductCandidate
from ..schemas.candidate import (
    CandidateListItem, CandidateDetail, ApproveRequest, RejectRequest,
)
from ..dependencies import get_db
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get("", response_model=dict)
async def list_candidates(
    status: str | None = Query(None),
    source: str | None = Query(None),
    min_score: float | None = Query(None, ge=0, le=100),
    store_id: uuid.UUID | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: str = Query("created_at_desc"),
    db: AsyncSession = Depends(get_db),
):
    q = select(ProductCandidate)
    if status:
        q = q.where(ProductCandidate.status == status)
    if source:
        q = q.where(ProductCandidate.source == source)
    if min_score is not None:
        q = q.where(ProductCandidate.success_score >= min_score)
    if store_id:
        q = q.where(ProductCandidate.store_id == store_id)

    # Sorting
    sort_map = {
        "created_at_desc": desc(ProductCandidate.created_at),
        "created_at_asc":  asc(ProductCandidate.created_at),
        "score_desc":      desc(nulls_last(ProductCandidate.success_score)),
        "score_asc":       asc(nulls_last(ProductCandidate.success_score)),
    }
    q = q.order_by(sort_map.get(sort, desc(ProductCandidate.created_at)))

    # Count
    count_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = count_result.scalar() or 0

    # Page
    result = await db.execute(q.offset(offset).limit(limit))
    items = result.scalars().all()

    return {
        "items": [CandidateListItem.model_validate(i) for i in items],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total,
    }


@router.get("/{candidate_id}", response_model=CandidateDetail)
async def get_candidate(candidate_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    c = await db.get(ProductCandidate, candidate_id)
    if not c:
        raise HTTPException(404, "Candidate not found")
    return CandidateDetail.model_validate(c)


@router.patch("/{candidate_id}/approve", response_model=CandidateDetail)
async def approve_candidate(
    candidate_id: uuid.UUID,
    body: ApproveRequest,
    db: AsyncSession = Depends(get_db),
):
    c = await db.get(ProductCandidate, candidate_id)
    if not c:
        raise HTTPException(404, "Candidate not found")
    if c.status not in ("pending", "analyzing"):
        raise HTTPException(400, f"Cannot approve candidate with status '{c.status}'")
    c.status = "approved"
    c.approved_at = datetime.now(timezone.utc)
    if body.store_id:
        c.store_id = body.store_id
    await db.commit()
    await db.refresh(c)
    return CandidateDetail.model_validate(c)


@router.patch("/{candidate_id}/reject", response_model=CandidateDetail)
async def reject_candidate(
    candidate_id: uuid.UUID,
    body: RejectRequest,
    db: AsyncSession = Depends(get_db),
):
    c = await db.get(ProductCandidate, candidate_id)
    if not c:
        raise HTTPException(404, "Candidate not found")
    c.status = "rejected"
    c.rejection_reason = body.reason
    await db.commit()
    await db.refresh(c)
    return CandidateDetail.model_validate(c)


@router.delete("/{candidate_id}", status_code=204)
async def delete_candidate(candidate_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    c = await db.get(ProductCandidate, candidate_id)
    if not c:
        raise HTTPException(404, "Candidate not found")
    await db.delete(c)
    await db.commit()
