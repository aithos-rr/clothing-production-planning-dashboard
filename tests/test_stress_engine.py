"""Unit tests for aggregate phase-overload stress events."""
from __future__ import annotations

import pandas as pd

from src.engines.stress_engine import evaluate_aggregate_phase_stress
from src.utils.constants import EVENT_PHASE_OVERLOAD


def _cap(order_id: str, lab: str, phase: str, required: float, available: float) -> dict:
    util = (required / available) if available else float("inf")
    return {
        "order_id": order_id, "assigned_lab": lab, "product_type": "P",
        "phase_name": phase, "quantity": 10,
        "required_minutes": required, "available_minutes": available,
        "utilization_rate": util, "capacity_gap_minutes": available - required,
        "is_overloaded": util > 0.85, "is_bottleneck": False,
    }


def test_aggregate_overload_emits_event_per_participating_order() -> None:
    from src.engines.capacity_engine import aggregate_lab_phase
    cap = pd.DataFrame([
        _cap("O1", "L1", "shared", 40, 100),
        _cap("O2", "L1", "shared", 40, 100),
        _cap("O3", "L1", "shared", 40, 100),  # aggregate 120% on L1/shared
    ])
    agg = aggregate_lab_phase(cap)
    events = evaluate_aggregate_phase_stress(cap, agg)
    assert not events.empty
    assert set(events["event_type"]) == {EVENT_PHASE_OVERLOAD}
    assert set(events["order_id"]) == {"O1", "O2", "O3"}


def test_no_aggregate_event_when_phase_healthy() -> None:
    from src.engines.capacity_engine import aggregate_lab_phase
    cap = pd.DataFrame([_cap("O1", "L1", "ph", 10, 100)])  # 10%
    agg = aggregate_lab_phase(cap)
    events = evaluate_aggregate_phase_stress(cap, agg)
    assert events.empty
