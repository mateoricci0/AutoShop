"""Pre-publication validation checklist.

Returns a list of ChecklistItem results that must ALL pass before
a publish job can be enqueued.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ase_shared.models.marketing import MarketingAsset, GeneratedImage, AssetStatus
from ase_shared.models.product import ProductCandidate, ProductStatus
from ase_shared.models.store import Store


@dataclass
class ChecklistItem:
    key: str
    label: str
    passed: bool
    detail: str | None = None


@dataclass
class ChecklistResult:
    candidate_id: str
    store_id: str
    passed: bool
    items: list[ChecklistItem] = field(default_factory=list)


async def run_checklist(
    db: AsyncSession, candidate_id: uuid.UUID, store_id: uuid.UUID
) -> ChecklistResult:
    items: list[ChecklistItem] = []

    # 1 — Candidate exists and is approved
    candidate = await db.get(ProductCandidate, candidate_id)
    if candidate is None:
        items.append(ChecklistItem("candidate_exists", "Candidato existe", False, "No encontrado"))
        return ChecklistResult(str(candidate_id), str(store_id), False, items)

    items.append(
        ChecklistItem(
            "candidate_exists",
            "Candidato existe",
            True,
        )
    )
    items.append(
        ChecklistItem(
            "candidate_approved",
            "Candidato aprobado",
            candidate.status == ProductStatus.approved,
            None if candidate.status == ProductStatus.approved else f"Estado: {candidate.status}",
        )
    )

    # 2 — Store exists and is active
    store = await db.get(Store, store_id)
    store_ok = store is not None and store.is_active
    items.append(
        ChecklistItem(
            "store_active",
            "Tienda activa",
            store_ok,
            None if store_ok else "Tienda no encontrada o inactiva",
        )
    )

    # 3 — Marketing asset exists (approved or draft)
    asset_result = await db.execute(
        select(MarketingAsset)
        .where(MarketingAsset.candidate_id == candidate_id)
        .limit(1)
    )
    asset = asset_result.scalar_one_or_none()
    asset_ok = asset is not None and asset.status in (AssetStatus.approved, AssetStatus.draft, AssetStatus.active)
    items.append(
        ChecklistItem(
            "marketing_asset",
            "Asset de marketing generado",
            asset_ok,
            None if asset_ok else "No hay copy generado. Usa 'Generar copy' primero.",
        )
    )

    # 4 — At least one approved image
    img_result = await db.execute(
        select(GeneratedImage)
        .where(
            GeneratedImage.candidate_id == candidate_id,
            GeneratedImage.status == "approved",
        )
        .limit(1)
    )
    has_images = img_result.scalar_one_or_none() is not None
    items.append(
        ChecklistItem(
            "has_approved_images",
            "Al menos 1 imagen aprobada",
            has_images,
            None if has_images else "Aprueba al menos una imagen en la sección de imágenes.",
        )
    )

    # 5 — Price is present on candidate (the caller provides it, but at least cost should be set)
    has_price_hint = candidate.recommended_price is not None or candidate.cost is not None
    items.append(
        ChecklistItem(
            "has_price_hint",
            "Información de precio disponible",
            has_price_hint,
            None if has_price_hint else "El candidato no tiene precio ni coste estimado.",
        )
    )

    passed = all(item.passed for item in items)
    return ChecklistResult(str(candidate_id), str(store_id), passed, items)
