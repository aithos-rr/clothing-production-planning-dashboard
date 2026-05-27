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


def test_sheet_alias_labs_factories_resolves_to_labs() -> None:
    """Workbooks using `labs_factories` should still populate the labs table."""
    raw = {
        "orders": pd.DataFrame([{
            "order_id": "O1", "product_type": "P", "quantity": 5,
            "deadline": date(2030, 1, 1), "assigned_lab": "L3",
        }]),
        "product_matrix": pd.DataFrame([{
            "product_type": "P", "phase_name": "ph",
            "avg_time_minutes": 5.0, "phase_order": 1,
        }]),
        "labs_factories": pd.DataFrame([{
            "lab_id": "L3", "lab_name": "Centro",
            "working_hours_per_day": 8, "default_efficiency": 0.8,
            "machine_uptime": 0.9, "overtime_allowed": "No",
        }]),
        "phase_capacity": pd.DataFrame([{
            "lab_id": "L3", "phase_name": "ph",
            "workers_total": 3, "workers_assigned": 3,
        }]),
    }
    result = normalize_all(raw, use_mock_fallback=False)
    assert "L3" in result["labs"]["lab_id"].tolist()
    assert result["labs"].iloc[0]["overtime_allowed"] is False or result["labs"].iloc[0]["overtime_allowed"] == False  # noqa: E712


def test_unknown_lab_referenced_by_phase_capacity_does_not_warn() -> None:
    """Lab ids in phase_capacity but missing from labs are added silently."""
    raw = {
        "orders": pd.DataFrame([{
            "order_id": "O1", "product_type": "P", "quantity": 5,
            "deadline": date(2030, 1, 1), "assigned_lab": "L7",
        }]),
        "product_matrix": pd.DataFrame([{
            "product_type": "P", "phase_name": "ph",
            "avg_time_minutes": 5.0, "phase_order": 1,
        }]),
        "labs": pd.DataFrame([{
            "lab_id": "L1", "lab_name": "Nord",
            "working_hours_per_day": 8, "default_efficiency": 0.8,
            "machine_uptime": 0.9, "overtime_allowed": False,
        }]),
        "phase_capacity": pd.DataFrame([
            {"lab_id": "L1", "phase_name": "ph", "workers_total": 2, "workers_assigned": 2},
            {"lab_id": "L7", "phase_name": "ph", "workers_total": 2, "workers_assigned": 2},
            {"lab_id": "L7", "phase_name": "ph2", "workers_total": 1, "workers_assigned": 1},
        ]),
    }
    result = normalize_all(raw, use_mock_fallback=False)
    assert "L7" in result["labs"]["lab_id"].tolist()
    unknown_lab_warnings = [w for w in result["warnings"] if "unknown lab_id" in w.message]
    assert unknown_lab_warnings == []


def test_overtime_allowed_parses_yes_no_strings() -> None:
    """Defensive: bool('No') == True, so Yes/No strings must be parsed explicitly."""
    raw = pd.DataFrame([
        {"lab_id": "L1", "overtime_allowed": "Yes"},
        {"lab_id": "L2", "overtime_allowed": "No"},
        {"lab_id": "L3", "overtime_allowed": True},
        {"lab_id": "L4", "overtime_allowed": False},
    ])
    df, _ = normalize_labs(raw)
    assert df.set_index("lab_id")["overtime_allowed"].to_dict() == {
        "L1": True, "L2": False, "L3": True, "L4": False,
    }
