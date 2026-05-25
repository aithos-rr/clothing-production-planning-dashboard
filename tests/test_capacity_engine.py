"""Unit tests for `src/engines/capacity_engine.py` — TASK-036."""
from __future__ import annotations

import math

import pandas as pd
import pytest

from src.engines.capacity_engine import compute_capacity_results
from src.utils.constants import SAFE_UTILIZATION_THRESHOLD


def _orders(qty: int = 100, lab: str = "L1", product: str = "P") -> pd.DataFrame:
    return pd.DataFrame([{
        "order_id": "O1",
        "client": "Client",
        "product_type": product,
        "quantity": qty,
        "start_date": None,
        "deadline": None,
        "assigned_lab": lab,
        "assigned_chain": "C",
        "progress_percentage": 0.0,
        "priority": "normal",
    }])


def _product_matrix(avg: float = 10.0, setup: float = 0.0, product: str = "P") -> pd.DataFrame:
    return pd.DataFrame([{
        "product_type": product,
        "phase_name": "ph1",
        "min_time_minutes": avg,
        "max_time_minutes": avg,
        "avg_time_minutes": avg,
        "setup_time_minutes": setup,
        "phase_order": 1,
    }])


def _phase_capacity(available_per_day: float = 1000.0, lab: str = "L1") -> pd.DataFrame:
    return pd.DataFrame([{
        "lab_id": lab,
        "phase_name": "ph1",
        "workers_total": 1,
        "workers_assigned": 1,
        "machines_total": 1,
        "available_minutes_per_day": available_per_day,
        "efficiency": 1.0,
        "uptime": 1.0,
    }])


def _labs() -> pd.DataFrame:
    return pd.DataFrame([{
        "lab_id": "L1",
        "lab_name": "L1",
        "working_hours_per_day": 8.0,
        "working_days_per_week": 5,
        "default_efficiency": 1.0,
        "machine_uptime": 1.0,
        "max_weekly_hours": 48.0,
        "overtime_allowed": False,
    }])


def test_required_minutes_basic() -> None:
    cap = compute_capacity_results(
        _orders(qty=10), _product_matrix(avg=5.0, setup=20.0), _labs(),
        _phase_capacity(available_per_day=1000.0), planning_days=1,
    )
    assert len(cap) == 1
    # required = 10 × 5 + 20 = 70
    assert cap.iloc[0]["required_minutes"] == pytest.approx(70.0)


def test_available_minutes_scales_with_planning_days() -> None:
    cap = compute_capacity_results(
        _orders(qty=10), _product_matrix(avg=5.0), _labs(),
        _phase_capacity(available_per_day=500.0), planning_days=3,
    )
    assert cap.iloc[0]["available_minutes"] == pytest.approx(1500.0)


def test_utilization_rate_correct() -> None:
    # required = 100 × 10 = 1000; available = 2000 → util = 0.5
    cap = compute_capacity_results(
        _orders(qty=100), _product_matrix(avg=10.0), _labs(),
        _phase_capacity(available_per_day=2000.0), planning_days=1,
    )
    assert cap.iloc[0]["utilization_rate"] == pytest.approx(0.5)


def test_capacity_gap_can_be_negative() -> None:
    # required = 100 × 10 = 1000; available = 500 → gap = -500
    cap = compute_capacity_results(
        _orders(qty=100), _product_matrix(avg=10.0), _labs(),
        _phase_capacity(available_per_day=500.0), planning_days=1,
    )
    assert cap.iloc[0]["capacity_gap_minutes"] == pytest.approx(-500.0)


def test_zero_available_minutes_returns_inf_no_exception() -> None:
    cap = compute_capacity_results(
        _orders(qty=10), _product_matrix(avg=5.0), _labs(),
        _phase_capacity(available_per_day=0.0), planning_days=1,
    )
    assert math.isinf(cap.iloc[0]["utilization_rate"])
    assert bool(cap.iloc[0]["is_overloaded"]) is True


def test_overloaded_flag_uses_threshold_from_constants() -> None:
    # Construct utilization just above SAFE threshold
    # required = 100 × 1; available = required / (SAFE + 0.01)
    util_target = SAFE_UTILIZATION_THRESHOLD + 0.01
    required = 100.0
    available = required / util_target
    cap = compute_capacity_results(
        _orders(qty=100), _product_matrix(avg=1.0), _labs(),
        _phase_capacity(available_per_day=available), planning_days=1,
    )
    assert bool(cap.iloc[0]["is_overloaded"]) is True

    # Now just below threshold
    util_target = SAFE_UTILIZATION_THRESHOLD - 0.01
    available = required / util_target
    cap = compute_capacity_results(
        _orders(qty=100), _product_matrix(avg=1.0), _labs(),
        _phase_capacity(available_per_day=available), planning_days=1,
    )
    assert bool(cap.iloc[0]["is_overloaded"]) is False


def test_unknown_product_emits_row_marked_overloaded() -> None:
    """An order with a product not in the matrix should still produce a result row."""
    cap = compute_capacity_results(
        _orders(product="Ghost"), _product_matrix(product="P"), _labs(),
        _phase_capacity(),
    )
    assert len(cap) == 1
    assert math.isinf(cap.iloc[0]["utilization_rate"])
    assert bool(cap.iloc[0]["is_overloaded"]) is True
