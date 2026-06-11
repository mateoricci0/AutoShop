"""Validate marketing asset completeness before saving."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ValidationResult:
    valid: bool
    missing_fields: list[str]
    warnings: list[str]


_REQUIRED_FIELDS = [
    "brand_name",
    "tagline",
    "short_description",
    "long_description",
    "meta_title",
    "meta_description",
    "hooks",
    "headlines",
    "ctas",
]

_MIN_LENGTHS = {
    "long_description": 100,
    "short_description": 20,
    "meta_title": 10,
    "meta_description": 50,
}

_LIST_MIN_ITEMS = {
    "hooks": 1,
    "headlines": 1,
    "ctas": 1,
    "bullet_points": 3,
    "keywords": 3,
}


def validate_asset(data: dict) -> ValidationResult:
    missing: list[str] = []
    warnings: list[str] = []

    for field in _REQUIRED_FIELDS:
        val = data.get(field)
        if not val:
            missing.append(field)
            continue

        if field in _MIN_LENGTHS and isinstance(val, str):
            if len(val) < _MIN_LENGTHS[field]:
                warnings.append(f"{field} is too short ({len(val)} chars)")

        if field in _LIST_MIN_ITEMS and isinstance(val, list):
            if len(val) < _LIST_MIN_ITEMS[field]:
                warnings.append(f"{field} has fewer than {_LIST_MIN_ITEMS[field]} items")

    for field, min_items in _LIST_MIN_ITEMS.items():
        val = data.get(field)
        if val is not None and isinstance(val, list) and len(val) < min_items:
            if field not in missing:
                warnings.append(f"{field} has fewer than {min_items} items")

    return ValidationResult(
        valid=len(missing) == 0,
        missing_fields=missing,
        warnings=warnings,
    )
