"""Tests for build_timeline: undefined-capacity phases must not inflate duration."""
from __future__ import annotations

from datetime import date

import pandas as pd

from src.engines.timeline_engine import build_timeline
from src.utils.constants import TIMELINE_BLOCKED, TIMELINE_ON_TRACK


def _orders() -> pd.DataFrame:
    return pd.DataFrame([{
        "order_id": "O1", "product_type": "Jeans", "quantity": 100,
        "start_date": date(2026, 6, 1), "deadline": date(2026, 12, 31),
        "assigned_lab": "L1",
    }])


def _cap(rows) -> pd.DataFrame:
    cols = ["order_id", "assigned_lab", "product_type", "phase_name", "quantity",
            "required_minutes", "available_minutes", "utilization_rate",
            "capacity_gap_minutes", "is_overloaded", "is_bottleneck"]
    return pd.DataFrame(rows)[cols]


def test_undefined_capacity_phase_does_not_inflate_duration() -> None:
    # Two phases: "cut" has capacity (300/day via available_minutes over 5 days),
    # "wash" has NO matching phase_capacity row (available 0 -> undefined).
    cap = _cap([
        {"order_id": "O1", "assigned_lab": "L1", "product_type": "Jeans",
         "phase_name": "cut", "quantity": 100, "required_minutes": 600.0,
         "available_minutes": 1500.0, "utilization_rate": 0.4,
         "capacity_gap_minutes": 900.0, "is_overloaded": False, "is_bottleneck": False},
        {"order_id": "O1", "assigned_lab": "L1", "product_type": "Jeans",
         "phase_name": "wash", "quantity": 100, "required_minutes": 500.0,
         "available_minutes": 0.0, "utilization_rate": float("inf"),
         "capacity_gap_minutes": 0.0, "is_overloaded": True, "is_bottleneck": False},
    ])
    # phase_capacity defines ONLY cut on L1 (300/day). wash is absent -> undefined.
    pc = pd.DataFrame([{"lab_id": "L1", "phase_name": "cut", "available_minutes_per_day": 300.0}])
    tl = build_timeline(_orders(), cap, pc, today=date(2026, 6, 1), planning_days=5)
    row = tl.iloc[0]
    # cut: ceil(600/300) = 2 days. wash undefined -> skipped, NOT +999.
    assert row["duration_days"] == 2
    assert bool(row["has_undefined_capacity"]) is True
    assert row["status"] == TIMELINE_BLOCKED


def test_all_phases_defined_is_not_blocked() -> None:
    cap = _cap([
        {"order_id": "O1", "assigned_lab": "L1", "product_type": "Jeans",
         "phase_name": "cut", "quantity": 100, "required_minutes": 600.0,
         "available_minutes": 1500.0, "utilization_rate": 0.4,
         "capacity_gap_minutes": 900.0, "is_overloaded": False, "is_bottleneck": False},
    ])
    pc = pd.DataFrame([{"lab_id": "L1", "phase_name": "cut", "available_minutes_per_day": 300.0}])
    tl = build_timeline(_orders(), cap, pc, today=date(2026, 6, 1), planning_days=5)
    row = tl.iloc[0]
    assert bool(row["has_undefined_capacity"]) is False
    assert row["status"] == TIMELINE_ON_TRACK  # deadline far in the future
    assert row["duration_days"] == 2
