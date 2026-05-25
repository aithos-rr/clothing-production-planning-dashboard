"""Timeline Engine — PRD §9.8.

Compute order-level start, end, duration, overlap flag, and status for the
Gantt-style visualization.
"""
from __future__ import annotations

import math
from datetime import date, timedelta

import pandas as pd

from src.utils.constants import TIMELINE_AT_RISK, TIMELINE_LATE, TIMELINE_ON_TRACK

TIMELINE_COLS = [
    "order_id", "product_type", "assigned_lab", "start_date", "end_date",
    "deadline", "duration_days", "overlap_flag", "status",
]


def _add_business_days(start: date, days: int, working_days_per_week: int = 5) -> date:
    """Add `days` business days to `start`. Skip weekends if working_days_per_week == 5."""
    if working_days_per_week >= 7 or days <= 0:
        return start + timedelta(days=days)
    current = start
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < working_days_per_week:
            added += 1
    return current


def _ranges_overlap(a_start: date, a_end: date, b_start: date, b_end: date) -> bool:
    return a_start <= b_end and b_start <= a_end


def build_timeline(
    orders_df: pd.DataFrame,
    capacity_results_df: pd.DataFrame,
    phase_capacity_df: pd.DataFrame | None = None,
    working_days_per_week: int = 5,
    today: date | None = None,
) -> pd.DataFrame:
    """Build the per-order timeline DataFrame (PRD §7.6 schema)."""
    if orders_df.empty:
        return pd.DataFrame(columns=TIMELINE_COLS)

    today = today or date.today()

    # Pre-aggregate required minutes per order
    required_per_order = (
        capacity_results_df.groupby("order_id")["required_minutes"].sum().to_dict()
        if not capacity_results_df.empty
        else {}
    )

    # Lab daily capacity = sum of phase availabilities (rough heuristic for duration)
    lab_capacity_per_day = (
        phase_capacity_df.groupby("lab_id")["available_minutes_per_day"].sum().to_dict()
        if phase_capacity_df is not None and not phase_capacity_df.empty
        else {}
    )

    rows: list[dict] = []
    for _, order in orders_df.iterrows():
        order_id = order["order_id"]
        lab = order.get("assigned_lab") or "Default Lab"
        product_type = order.get("product_type")
        start = order.get("start_date") or today
        deadline = order.get("deadline")

        required = float(required_per_order.get(order_id, 0.0))
        cap_per_day = float(lab_capacity_per_day.get(lab, 0.0))

        if required <= 0 or cap_per_day <= 0:
            duration_days = 1
        else:
            duration_days = max(1, math.ceil(required / cap_per_day))

        end_date = _add_business_days(start, duration_days, working_days_per_week)

        if deadline is None or pd.isna(deadline):
            status = TIMELINE_ON_TRACK
        else:
            try:
                days_to_deadline = (deadline - end_date).days
            except TypeError:
                days_to_deadline = 0
            if end_date > deadline:
                status = TIMELINE_LATE
            elif days_to_deadline <= 2:
                status = TIMELINE_AT_RISK
            else:
                status = TIMELINE_ON_TRACK

        rows.append({
            "order_id": order_id,
            "product_type": product_type,
            "assigned_lab": lab,
            "start_date": start,
            "end_date": end_date,
            "deadline": deadline,
            "duration_days": duration_days,
            "overlap_flag": False,  # filled below
            "status": status,
        })

    timeline = pd.DataFrame(rows, columns=TIMELINE_COLS)

    # Overlap detection per lab
    if not timeline.empty:
        for lab_id, group in timeline.groupby("assigned_lab"):
            records = group[["order_id", "start_date", "end_date"]].to_dict("records")
            for i, r in enumerate(records):
                if any(
                    _ranges_overlap(r["start_date"], r["end_date"], s["start_date"], s["end_date"])
                    for j, s in enumerate(records)
                    if i != j
                ):
                    timeline.loc[timeline["order_id"] == r["order_id"], "overlap_flag"] = True

    return timeline


__all__ = ["build_timeline", "TIMELINE_COLS"]
