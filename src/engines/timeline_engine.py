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
    planning_days: int = 5,
) -> pd.DataFrame:
    """Build the per-order timeline DataFrame (PRD §7.6 schema).

    Duration is computed as the **sum** of per-phase durations because phases
    run sequentially along the production chain (PRD §3.3, phase_order). Each
    phase's duration is `ceil(required_minutes / available_minutes_per_day)`
    for that specific (lab, phase) pair — *not* the lab's total daily capacity,
    which would over-allocate by pretending all phases run in parallel.
    """
    if orders_df.empty:
        return pd.DataFrame(columns=TIMELINE_COLS)

    today = today or date.today()

    # Build (lab, phase) → available_minutes_per_day lookup for sequential math.
    phase_avail: dict[tuple[str, str], float] = {}
    if phase_capacity_df is not None and not phase_capacity_df.empty:
        for _, row in phase_capacity_df.iterrows():
            phase_avail[(row["lab_id"], row["phase_name"])] = float(row["available_minutes_per_day"])

    # Index capacity rows by order_id so we can iterate phases per order.
    cap_by_order = (
        {oid: g for oid, g in capacity_results_df.groupby("order_id")}
        if not capacity_results_df.empty
        else {}
    )

    rows: list[dict] = []
    for _, order in orders_df.iterrows():
        order_id = order["order_id"]
        lab = order.get("assigned_lab") or "Default Lab"
        product_type = order.get("product_type")
        start = order.get("start_date") or today
        deadline = order.get("deadline")

        order_cap = cap_by_order.get(order_id)
        if order_cap is None or order_cap.empty:
            duration_days = 1
        else:
            # Sequential phases → sum of ceil(required / available_per_day) per phase.
            # Fallback: derive available_per_day from capacity_results_df itself
            # (available_minutes is already × planning_days).
            phase_durations: list[int] = []
            for _, prow in order_cap.iterrows():
                required = float(prow["required_minutes"])
                if required <= 0:
                    continue
                avail_per_day = phase_avail.get((lab, prow["phase_name"]), 0.0)
                if avail_per_day <= 0 and prow["available_minutes"] > 0 and planning_days > 0:
                    avail_per_day = float(prow["available_minutes"]) / planning_days
                if avail_per_day <= 0:
                    # Phase unmatched → treat as a hard blocker, add a large penalty
                    phase_durations.append(999)
                    continue
                phase_durations.append(math.ceil(required / avail_per_day))
            duration_days = max(1, sum(phase_durations)) if phase_durations else 1

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
