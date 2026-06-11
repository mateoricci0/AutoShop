"""CRUD endpoints for generated images."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ase_shared.models.marketing import GeneratedImage
from ..dependencies import get_db
from ..schemas.image import ImageDetail, ImageListItem

router = APIRouter(prefix="/images", tags=["images"])


@router.get("", response_model=dict)
async def list_images(
    candidate_id: uuid.UUID | None = Query(None),
    store_id: uuid.UUID | None = Query(None),
    image_type: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    q = select(GeneratedImage)
    if candidate_id:
        q = q.where(GeneratedImage.candidate_id == candidate_id)
    if store_id:
        q = q.where(GeneratedImage.store_id == store_id)
    if image_type:
        q = q.where(GeneratedImage.type == image_type)
    if status:
        q = q.where(GeneratedImage.status == status)
    q = q.order_by(desc(GeneratedImage.created_at))

    count_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = count_result.scalar() or 0

    result = await db.execute(q.offset(offset).limit(limit))
    items = result.scalars().all()

    return {
        "items": [ImageListItem.model_validate(i) for i in items],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total,
    }


@router.get("/{image_id}", response_model=ImageDetail)
async def get_image(image_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    img = await db.get(GeneratedImage, image_id)
    if not img:
        raise HTTPException(404, "Image not found")
    return ImageDetail.model_validate(img)


@router.patch("/{image_id}/approve", response_model=ImageDetail)
async def approve_image(image_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    img = await db.get(GeneratedImage, image_id)
    if not img:
        raise HTTPException(404, "Image not found")
    img.status = "approved"
    await db.commit()
    await db.refresh(img)
    return ImageDetail.model_validate(img)


@router.delete("/{image_id}", status_code=204)
async def delete_image(image_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    img = await db.get(GeneratedImage, image_id)
    if not img:
        raise HTTPException(404, "Image not found")
    await db.delete(img)
    await db.commit()
