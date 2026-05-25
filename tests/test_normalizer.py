"""Unit tests for `src/parsers/normalizer.py` — TASK-038."""
from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from src.parsers.normalizer import (
    normalize_all,
    normalize_labs,
    normalize_orders,
    normalize_phase_capacity,
    normalize_product_matrix,
)


def test_orders_fills_missing_client_with_unknown() -> None:
    raw = pd.DataFrame([{
        "product_type": "P", "quantity": 10, "deadline": date(2030, 1, 1),
    }])
    df, _ = normalize_orders(raw)
    assert df.iloc[0]["client"] == "Unknown Client"


def test_orders_generates_order_id_when_missing() -> None:
    raw = pd.DataFrame([
        {"product_type": "P", "quantity": 10, "deadline": date(2030, 1, 1)},
        {"product_type": "P", "quantity": 12, "deadline": date(2030, 2, 1)},
    ])
    df, _ = normalize_orders(raw)
    assert df["order_id"].tolist() == ["ORD-0001", "ORD-0002"]


def test_orders_progress_percentage_in_fraction_scale() -> None:
    raw = pd.DataFrame([{
        "product_type": "P", "quantity": 10, "deadline": date(2030, 1, 1),
        "progress_percentage": 50,  # user supplied as 0..100
    }])
    df, _ = normalize_orders(raw)
    assert df.iloc[0]["progress_percentage"] == pytest.approx(0.5)


def test_product_matrix_computes_avg_from_min_max() -> None:
    raw = pd.DataFrame([{
        "product_type": "P", "phase_name": "ph",
        "min_time_minutes": 10, "max_time_minutes": 20,
    }])
    df, _ = normalize_product_matrix(raw)
    assert df.iloc[0]["avg_time_minutes"] == pytest.approx(15.0)


def test_product_matrix_phase_order_inferred() -> None:
    raw = pd.DataFrame([
        {"product_type": "P", "phase_name": "a", "avg_time_minutes": 1.0},
        {"product_type": "P", "phase_name": "b", "avg_time_minutes": 1.0},
        {"product_type": "P", "phase_name": "c", "avg_time_minutes": 1.0},
    ])
    df, _ = normalize_product_matrix(raw)
    assert df["phase_order"].tolist() == [1, 2, 3]


def test_labs_fills_efficiency_from_config_default() -> None:
    raw = pd.DataFrame([{"lab_id": "L1"}])
    df, _ = normalize_labs(raw)
    assert df.iloc[0]["default_efficiency"] == pytest.approx(0.75)
    assert df.iloc[0]["machine_uptime"] == pytest.approx(0.90)
    assert df.iloc[0]["working_hours_per_day"] == pytest.approx(8.0)


def test_phase_capacity_warns_on_unknown_lab_id() -> None:
    labs = pd.DataFrame([{
        "lab_id": "L1", "lab_name": "L1",
        "working_hours_per_day": 8.0, "working_days_per_week": 5,
        "default_efficiency": 0.75, "machine_uptime": 0.9,
        "max_weekly_hours": 48.0, "overtime_allowed": False,
    }])
    raw_pc = pd.DataFrame([{
        "lab_id": "GHOST", "phase_name": "ph",
        "workers_total": 3, "workers_assigned": 3,
        "efficiency": 0.75, "uptime": 0.9,
    }])
    _, warnings = normalize_phase_capacity(raw_pc, labs)
    assert any("GHOST" in w.message for w in warnings)


def test_phase_capacity_available_minutes_computed() -> None:
    labs = pd.DataFrame([{
        "lab_id": "L1", "lab_name": "L1",
        "working_hours_per_day": 8.0, "working_days_per_week": 5,
        "default_efficiency": 0.75, "machine_uptime": 0.9,
        "max_weekly_hours": 48.0, "overtime_allowed": False,
    }])
    raw_pc = pd.DataFrame([{
        "lab_id": "L1", "phase_name": "ph",
        "workers_total": 4, "workers_assigned": 4,
        "efficiency": 0.75, "uptime": 0.9,
    }])
    df, _ = normalize_phase_capacity(raw_pc, labs)
    # 4 × (8 × 60) × 0.75 × 0.9 = 1296
    assert df.iloc[0]["available_minutes_per_day"] == pytest.approx(1296.0)


def test_normalize_all_returns_empty_when_no_fallback() -> None:
    result = normalize_all({}, use_mock_fallback=False)
    assert result["orders"].empty
    assert any(w.severity == "high" for w in result["warnings"])
