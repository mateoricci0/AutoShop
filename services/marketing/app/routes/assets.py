"""CRUD endpoints for marketing assets."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ase_shared.models.marketing import MarketingAsset
from ..dependencies import get_db
from ..schemas.asset import AssetDetail, AssetListItem, AssetUpdateRequest

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("", response_model=dict)
async def list_assets(
    candidate_id: uuid.UUID | None = Query(None),
    store_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    q = select(MarketingAsset)
    if candidate_id:
        q = q.where(MarketingAsset.candidate_id == candidate_id)
    if store_id:
        q = q.where(MarketingAsset.store_id == store_id)
    if status:
        q = q.where(MarketingAsset.status == status)
    q = q.order_by(desc(MarketingAsset.created_at))

    count_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = count_result.scalar() or 0

    result = await db.execute(q.offset(offset).limit(limit))
    items = result.scalars().all()

    return {
        "items": [AssetListItem.model_validate(i) for i in items],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total,
    }


@router.get("/{asset_id}", response_model=AssetDetail)
async def get_asset(asset_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    asset = await db.get(MarketingAsset, asset_id)
    if not asset:
        raise HTTPException(404, "Asset not found")
    return AssetDetail.model_validate(asset)


@router.patch("/{asset_id}", response_model=AssetDetail)
async def update_asset(
    asset_id: uuid.UUID,
    body: AssetUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    asset = await db.get(MarketingAsset, asset_id)
    if not asset:
        raise HTTPException(404, "Asset not found")

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(asset, field, value)

    await db.commit()
    await db.refresh(asset)
    return AssetDetail.model_validate(asset)


@router.delete("/{asset_id}", status_code=204)
async def delete_asset(asset_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    asset = await db.get(MarketingAsset, asset_id)
    if not asset:
        raise HTTPException(404, "Asset not found")
    await db.delete(asset)
    await db.commit()


@router.patch("/{asset_id}/approve", response_model=AssetDetail)
async def approve_asset(asset_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    asset = await db.get(MarketingAsset, asset_id)
    if not asset:
        raise HTTPException(404, "Asset not found")
    asset.status = "approved"
    await db.commit()
    await db.refresh(asset)
    return AssetDetail.model_validate(asset)
