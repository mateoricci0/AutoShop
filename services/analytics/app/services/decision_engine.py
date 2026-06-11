"""Decision engine — maps aggregate metrics to scale/optimize/pause/insufficient_data.

Thresholds:
  ROAS ≥ 3.0  → scale
  ROAS 1.5..3 → optimize
  ROAS < 1.5  → pause
  < 50 orders → insufficient_data
"""
from __future__ import annotations


_MIN_ORDERS_FOR_DECISION = 50
_ROAS_SCALE_THRESHOLD = 3.0
_ROAS_PAUSE_THRESHOLD = 1.5


def make_decision(roas: float | None, total_orders: int) -> str:
    if total_orders < _MIN_ORDERS_FOR_DECISION or roas is None:
        return "insufficient_data"
    if roas >= _ROAS_SCALE_THRESHOLD:
        return "scale"
    if roas >= _ROAS_PAUSE_THRESHOLD:
        return "optimize"
    return "pause"
