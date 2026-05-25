"""Operational Stress Engine — PRD §9.6 / §11.

Rule-based event generation. Two entry points:
  - evaluate_utilization_stress(capacity_results_df) → utilization-driven events
  - evaluate_scenario_stress(...) → scenario / deadline / parallel events
  - evaluate_all_stress(...) concatenates both.
"""
from __future__ import annotations

import math
import uuid
from datetime import date, timedelta

import pandas as pd

from src.engines.scenario_engine import ScenarioInputs
from src.utils.constants import (
    CRITICAL_UTILIZATION_THRESHOLD,
    EVENT_DEADLINE_INFEASIBLE,
    EVENT_MACHINE_DOWNTIME,
    EVENT_OVERTIME_REQUIRED,
    EVENT_PARALLEL_OVERLOAD,
    EVENT_PHASE_OVERLOAD,
    EVENT_UTILIZATION_CRITICAL,
    EVENT_UTILIZATION_HIGH,
    EVENT_WORKER_ABSENCE,
    MAX_PARALLEL_ORDERS_PER_LAB,
    PHASE_STRESS_THRESHOLD,
    SAFE_UTILIZATION_THRESHOLD,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
)

STRESS_EVENTS_COLS = [
    "event_id", "order_id", "event_type", "severity",
    "message", "triggered_by", "recommended_action",
]


def _new_event_id() -> str:
    return f"STR-{uuid.uuid4().hex[:8]}"


def _make_event(
    order_id: str,
    event_type: str,
    severity: str,
    message: str,
    triggered_by: str,
    recommended_action: str,
) -> dict:
    return {
        "event_id": _new_event_id(),
        "order_id": order_id,
        "event_type": event_type,
        "severity": severity,
        "message": message,
        "triggered_by": triggered_by,
        "recommended_action": recommended_action,
    }


# ---------- TASK-020 ----------
def evaluate_utilization_stress(capacity_results_df: pd.DataFrame) -> pd.DataFrame:
    """Emit events for utilization-based triggers (PRD §9.6 a-c)."""
    events: list[dict] = []
    if capacity_results_df.empty:
        return pd.DataFrame(columns=STRESS_EVENTS_COLS)

    # Per-order aggregate utilization (mean of finite phase utilizations)
    finite_util = capacity_results_df["utilization_rate"].replace([math.inf, -math.inf], math.nan)
    df = capacity_results_df.assign(_util=finite_util)

    for order_id, group in df.groupby("order_id"):
        finite = group["_util"].dropna()
        order_util = float(finite.mean()) if not finite.empty else math.inf

        # any phase at >= critical threshold (or inf)
        critical_phases = group[
            (group["utilization_rate"] >= CRITICAL_UTILIZATION_THRESHOLD)
            | (~group["utilization_rate"].apply(lambda v: math.isfinite(v)))
        ]
        if not critical_phases.empty:
            phase_names = ", ".join(critical_phases["phase_name"].astype(str).tolist())
            events.append(_make_event(
                order_id,
                EVENT_UTILIZATION_CRITICAL,
                SEVERITY_HIGH,
                f"Order {order_id} exceeds capacity on phase(s): {phase_names}.",
                triggered_by="utilization > 100%",
                recommended_action="Consider postpone",
            ))
        elif order_util > SAFE_UTILIZATION_THRESHOLD:
            events.append(_make_event(
                order_id,
                EVENT_UTILIZATION_HIGH,
                SEVERITY_MEDIUM,
                f"Order {order_id} aggregate utilization at {order_util * 100:.0f}%.",
                triggered_by=f"utilization > {int(SAFE_UTILIZATION_THRESHOLD * 100)}%",
                recommended_action="Consider split",
            ))

        # Phase-level overload (per-phase only; distinct from order-level critical)
        phase_overload = group[
            (group["utilization_rate"] > PHASE_STRESS_THRESHOLD)
            & (group["utilization_rate"] < CRITICAL_UTILIZATION_THRESHOLD)
        ]
        for _, row in phase_overload.iterrows():
            events.append(_make_event(
                order_id,
                EVENT_PHASE_OVERLOAD,
                SEVERITY_HIGH,
                f"Phase '{row['phase_name']}' at {row['utilization_rate'] * 100:.0f}% on order {order_id}.",
                triggered_by=f"phase utilization > {int(PHASE_STRESS_THRESHOLD * 100)}%",
                recommended_action="Reallocate to another lab",
            ))

    return pd.DataFrame(events, columns=STRESS_EVENTS_COLS)


# ---------- TASK-021 ----------
def _orders_overlap(a_start: date, a_end: date, b_start: date, b_end: date) -> bool:
    return a_start <= b_end and b_start <= a_end


def evaluate_scenario_stress(
    orders_df: pd.DataFrame,
    capacity_results_df: pd.DataFrame,
    labs_df: pd.DataFrame,
    phase_capacity_df: pd.DataFrame,
    scenario: ScenarioInputs,
    today: date,
) -> pd.DataFrame:
    """Emit events for scenario-driven and deadline-related triggers."""
    events: list[dict] = []

    if not orders_df.empty:
        order_ids = orders_df["order_id"].astype(str).tolist()
        first_id = order_ids[0] if order_ids else "ALL"

        # Scenario-wide alerts (attached to first order so they always appear once)
        if scenario.machine_downtime > 0:
            events.append(_make_event(
                first_id,
                EVENT_MACHINE_DOWNTIME,
                SEVERITY_HIGH,
                f"Machine downtime reduces available capacity by {scenario.machine_downtime * 100:.0f}%.",
                triggered_by="scenario.machine_downtime > 0",
                recommended_action="Reallocate to another lab",
            ))
        if scenario.absent_workers > 0:
            events.append(_make_event(
                first_id,
                EVENT_WORKER_ABSENCE,
                SEVERITY_HIGH,
                f"{scenario.absent_workers} worker(s) absent — phase capacity reduced.",
                triggered_by="scenario.absent_workers > 0",
                recommended_action="Consider postpone",
            ))

    # Overtime required: any phase where required > available AND lab.overtime_allowed False
    lab_overtime = (
        labs_df.set_index("lab_id")["overtime_allowed"].to_dict()
        if not labs_df.empty and "lab_id" in labs_df.columns
        else {}
    )
    order_to_lab = (
        orders_df.set_index("order_id")["assigned_lab"].to_dict()
        if not orders_df.empty and "assigned_lab" in orders_df.columns
        else {}
    )
    if not capacity_results_df.empty:
        for _, row in capacity_results_df.iterrows():
            if row["required_minutes"] > row["available_minutes"]:
                lab = order_to_lab.get(row["order_id"])
                if not bool(lab_overtime.get(lab, False)):
                    events.append(_make_event(
                        row["order_id"],
                        EVENT_OVERTIME_REQUIRED,
                        SEVERITY_HIGH,
                        f"Phase '{row['phase_name']}' on order {row['order_id']} requires overtime; "
                        f"lab '{lab}' has overtime disabled.",
                        triggered_by="required > available AND overtime_allowed=False",
                        recommended_action="Consider postpone",
                    ))

    # Parallel overload: > MAX_PARALLEL_ORDERS_PER_LAB overlapping orders in same lab
    if not orders_df.empty and {"assigned_lab", "start_date", "deadline"}.issubset(orders_df.columns):
        for lab_id, group in orders_df.groupby("assigned_lab"):
            rows = group[["order_id", "start_date", "deadline"]].dropna().to_dict("records")
            n = len(rows)
            if n <= MAX_PARALLEL_ORDERS_PER_LAB:
                continue
            # For each order count overlapping siblings (including itself)
            for i, r in enumerate(rows):
                overlaps = sum(
                    1
                    for j, s in enumerate(rows)
                    if i != j and _orders_overlap(r["start_date"], r["deadline"], s["start_date"], s["deadline"])
                )
                if overlaps + 1 > MAX_PARALLEL_ORDERS_PER_LAB:
                    events.append(_make_event(
                        str(r["order_id"]),
                        EVENT_PARALLEL_OVERLOAD,
                        SEVERITY_MEDIUM,
                        f"Lab '{lab_id}' has {overlaps + 1} overlapping orders in order {r['order_id']}'s window.",
                        triggered_by=f"parallel orders > {MAX_PARALLEL_ORDERS_PER_LAB}",
                        recommended_action="Reallocate to another lab",
                    ))

    # Deadline infeasible: days_to_deadline × lab_capacity_per_day < total required for that order
    if not capacity_results_df.empty and not orders_df.empty:
        total_required_per_order = (
            capacity_results_df.groupby("order_id")["required_minutes"].sum().to_dict()
        )
        lab_capacity_per_day = (
            phase_capacity_df.groupby("lab_id")["available_minutes_per_day"].sum().to_dict()
            if not phase_capacity_df.empty
            else {}
        )
        for _, order in orders_df.iterrows():
            order_id = order["order_id"]
            deadline = order.get("deadline")
            if deadline is None or pd.isna(deadline):
                continue
            try:
                days = (deadline - today).days
            except TypeError:
                continue
            required = float(total_required_per_order.get(order_id, 0.0))
            lab = order.get("assigned_lab")
            cap_per_day = float(lab_capacity_per_day.get(lab, 0.0))
            if days <= 0 and required > 0:
                events.append(_make_event(
                    str(order_id),
                    EVENT_DEADLINE_INFEASIBLE,
                    SEVERITY_HIGH,
                    f"Order {order_id} deadline already past (today={today}, deadline={deadline}).",
                    triggered_by="deadline <= today",
                    recommended_action="Consider postpone",
                ))
                continue
            if cap_per_day > 0 and days * cap_per_day < required:
                events.append(_make_event(
                    str(order_id),
                    EVENT_DEADLINE_INFEASIBLE,
                    SEVERITY_HIGH,
                    f"Order {order_id} cannot fit before deadline "
                    f"({days} day(s) × {cap_per_day:.0f} min/day = "
                    f"{days * cap_per_day:.0f} < required {required:.0f}).",
                    triggered_by="days × capacity < required",
                    recommended_action="Consider postpone",
                ))

    return pd.DataFrame(events, columns=STRESS_EVENTS_COLS)


def evaluate_all_stress(
    orders_df: pd.DataFrame,
    capacity_results_df: pd.DataFrame,
    labs_df: pd.DataFrame,
    phase_capacity_df: pd.DataFrame,
    scenario: ScenarioInputs,
    today: date | None = None,
) -> pd.DataFrame:
    """Concatenate utilization + scenario / deadline stress events."""
    today = today or date.today()
    util_events = evaluate_utilization_stress(capacity_results_df)
    scen_events = evaluate_scenario_stress(
        orders_df, capacity_results_df, labs_df, phase_capacity_df, scenario, today
    )
    if util_events.empty and scen_events.empty:
        return pd.DataFrame(columns=STRESS_EVENTS_COLS)
    return pd.concat([util_events, scen_events], ignore_index=True)


__all__ = [
    "evaluate_utilization_stress",
    "evaluate_scenario_stress",
    "evaluate_all_stress",
    "STRESS_EVENTS_COLS",
]
