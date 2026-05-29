"""Capacity Engine — PRD §9.4 / §10.

For every (order, phase) pair, compute required & available minutes,
utilization rate, and capacity gap. Output schema = PRD §7.5.
"""
from __future__ import annotations

import math
from typing import Iterable

import pandas as pd

from src.engines.product_matrix_engine import (
    UnknownProductError,
    get_phases_for_product,
)
from src.utils.constants import SAFE_UTILIZATION_THRESHOLD

CAPACITY_RESULTS_COLS = [
    "order_id", "assigned_lab", "product_type", "phase_name", "quantity",
    "required_minutes", "available_minutes", "utilization_rate",
    "capacity_gap_minutes", "is_overloaded", "is_bottleneck",
]


def _available_minutes(
    phase_capacity_df: pd.DataFrame,
    lab_id: str,
    phase_name: str,
    planning_days: int,
) -> float:
    """Lookup available_minutes_per_day for (lab, phase) × planning_days."""
    if phase_capacity_df.empty:
        return 0.0
    match = phase_capacity_df[
        (phase_capacity_df["lab_id"] == lab_id)
        & (phase_capacity_df["phase_name"] == phase_name)
    ]
    if match.empty:
        return 0.0
    return float(match.iloc[0]["available_minutes_per_day"]) * planning_days


def compute_capacity_results(
    orders_df: pd.DataFrame,
    product_matrix_df: pd.DataFrame,
    labs_df: pd.DataFrame,  # noqa: ARG001 — kept for API stability (PRD §9.4 contract)
    phase_capacity_df: pd.DataFrame,
    planning_days: int = 5,
) -> pd.DataFrame:
    """Compute per (order, phase) capacity metrics.

    Formulas (PRD §10):
      required_minutes = quantity × avg_time + setup_time
      available_minutes = phase_capacity.available_minutes_per_day × planning_days
      utilization_rate  = required_minutes / available_minutes  (inf if avail == 0)
      capacity_gap_minutes = available_minutes - required_minutes
    """
    rows: list[dict] = []

    if orders_df.empty:
        return pd.DataFrame(columns=CAPACITY_RESULTS_COLS)

    for _, order in orders_df.iterrows():
        product_type = order.get("product_type")
        quantity = int(order.get("quantity", 0) or 0)
        lab_id = order.get("assigned_lab") or "Default Lab"
        try:
            phases = get_phases_for_product(product_matrix_df, product_type)
        except UnknownProductError:
            # Emit a single row marking the order as unresolvable
            rows.append({
                "order_id": order["order_id"],
                "assigned_lab": lab_id,
                "product_type": product_type,
                "phase_name": "<unknown product>",
                "quantity": quantity,
                "required_minutes": 0.0,
                "available_minutes": 0.0,
                "utilization_rate": math.inf,
                "capacity_gap_minutes": 0.0,
                "is_overloaded": True,
                "is_bottleneck": False,
            })
            continue

        for _, phase in phases.iterrows():
            avg = float(phase["avg_time_minutes"]) if pd.notna(phase["avg_time_minutes"]) else 0.0
            setup = float(phase["setup_time_minutes"]) if pd.notna(phase["setup_time_minutes"]) else 0.0
            required = quantity * avg + setup
            available = _available_minutes(phase_capacity_df, lab_id, phase["phase_name"], planning_days)

            if available <= 0:
                utilization = math.inf if required > 0 else 0.0
            else:
                utilization = required / available

            gap = available - required

            rows.append({
                "order_id": order["order_id"],
                "assigned_lab": lab_id,
                "product_type": product_type,
                "phase_name": phase["phase_name"],
                "quantity": quantity,
                "required_minutes": float(required),
                "available_minutes": float(available),
                "utilization_rate": float(utilization),
                "capacity_gap_minutes": float(gap),
                "is_overloaded": bool(utilization > SAFE_UTILIZATION_THRESHOLD),
                "is_bottleneck": False,  # filled by bottleneck engine
            })

    return pd.DataFrame(rows, columns=CAPACITY_RESULTS_COLS)


LAB_PHASE_LOAD_COLS = [
    "assigned_lab", "phase_name", "total_required_minutes",
    "available_minutes", "utilization_rate", "capacity_gap_minutes",
    "is_overloaded", "num_orders",
]


def aggregate_lab_phase(capacity_results_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-(order,phase) rows into per-(lab,phase) capacity truth.

    Capacity is counted ONCE per (assigned_lab, phase_name) — `available_minutes`
    is identical across the orders that share a lab-phase, so we take its max.
    Required minutes are summed across all those orders.
    Note: rows with phase_name == "<unknown product>" (placeholder for orders whose
    product is not in the matrix) are excluded before aggregation.
    """
    if capacity_results_df.empty:
        return pd.DataFrame(columns=LAB_PHASE_LOAD_COLS)

    work = capacity_results_df[capacity_results_df["phase_name"] != "<unknown product>"]
    if work.empty:
        return pd.DataFrame(columns=LAB_PHASE_LOAD_COLS)

    rows: list[dict] = []
    for (lab, phase), g in work.groupby(["assigned_lab", "phase_name"]):
        total_required = float(g["required_minutes"].sum())
        available = float(g["available_minutes"].max())
        if available <= 0:
            utilization = math.inf if total_required > 0 else 0.0
        else:
            utilization = total_required / available
        rows.append({
            "assigned_lab": lab,
            "phase_name": phase,
            "total_required_minutes": total_required,
            "available_minutes": available,
            "utilization_rate": float(utilization),
            "capacity_gap_minutes": float(available - total_required),
            "is_overloaded": bool(utilization > SAFE_UTILIZATION_THRESHOLD),
            "num_orders": int(g["order_id"].nunique()),
        })
    return pd.DataFrame(rows, columns=LAB_PHASE_LOAD_COLS)


def overall_utilization(lab_phase_df: pd.DataFrame) -> float:
    """System-wide utilization = sum total_required / sum available (capacity once).

    Returns inf if there is required work but zero available capacity, 0.0 if no
    work at all.
    """
    if lab_phase_df.empty:
        return 0.0
    total_required = float(lab_phase_df["total_required_minutes"].sum())
    total_available = float(lab_phase_df["available_minutes"].sum())
    if total_available <= 0:
        return math.inf if total_required > 0 else 0.0
    return total_required / total_available


__all__ = [
    "compute_capacity_results",
    "CAPACITY_RESULTS_COLS",
    "aggregate_lab_phase",
    "overall_utilization",
    "LAB_PHASE_LOAD_COLS",
]
