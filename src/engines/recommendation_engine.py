"""Recommendation Engine — PRD §12.

Maps calculation + stress outputs into one of six labels (ACCEPT / AT_RISK /
REALLOCATE / SPLIT / POSTPONE / REJECT) with reasons and suggested actions.
"""
from __future__ import annotations

import math

import pandas as pd

from src.engines.lab_allocation_engine import find_alternative_lab
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
    REC_ACCEPT,
    REC_AT_RISK,
    REC_POSTPONE,
    REC_REALLOCATE,
    REC_REJECT,
    REC_SPLIT,
    SAFE_UTILIZATION_THRESHOLD,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
)

RECOMMENDATIONS_COLS = [
    "order_id", "recommendation", "severity", "reasons", "suggested_actions",
]


def _order_utilization(group: pd.DataFrame) -> float:
    """Worst-phase utilization for an order: max of finite, inf if any inf.

    Max (not mean) because a single phase over capacity makes the order
    infeasible even if its other phases are light.
    """
    if (~group["utilization_rate"].apply(lambda v: math.isfinite(v))).any():
        return math.inf
    return float(group["utilization_rate"].max())


def _phase_reasons(group: pd.DataFrame) -> list[str]:
    reasons: list[str] = []
    for _, row in group.iterrows():
        util = row["utilization_rate"]
        if not math.isfinite(util):
            reasons.append(f"Phase '{row['phase_name']}' has no available capacity (lab/phase unmatched)")
        elif util >= CRITICAL_UTILIZATION_THRESHOLD:
            reasons.append(f"Phase '{row['phase_name']}' at {util * 100:.0f}% utilization")
    return reasons


def generate_recommendations(
    capacity_results_df: pd.DataFrame,
    stress_events_df: pd.DataFrame,
    orders_df: pd.DataFrame | None = None,
    phase_capacity_df: pd.DataFrame | None = None,
    product_matrix_df: pd.DataFrame | None = None,
    timeline_df: pd.DataFrame | None = None,  # noqa: ARG001 — contract per PRD §9.7
) -> pd.DataFrame:
    """Generate one recommendation per order_id (PRD §7.8 schema).

    Decision order (first match wins):
      1. critical utilization OR overtime_required OR deadline_infeasible
         → REJECT / POSTPONE / SPLIT (chosen by which signal dominates)
      2. utilization 0.85–1.0 OR medium stress → AT_RISK / REALLOCATE
         (REALLOCATE iff find_alternative_lab returns non-None)
      3. otherwise → ACCEPT
    """
    if capacity_results_df.empty:
        return pd.DataFrame(columns=RECOMMENDATIONS_COLS)

    # Index helpers
    events_by_order = (
        stress_events_df.groupby("order_id") if not stress_events_df.empty else None
    )
    orders_by_id = (
        orders_df.set_index("order_id") if orders_df is not None and not orders_df.empty else None
    )

    rows: list[dict] = []

    for order_id, group in capacity_results_df.groupby("order_id"):
        util = _order_utilization(group)
        events = (
            events_by_order.get_group(order_id)
            if events_by_order is not None and order_id in events_by_order.groups
            else pd.DataFrame(columns=stress_events_df.columns if stress_events_df is not None else [])
        )

        event_types = set(events["event_type"].tolist()) if not events.empty else set()
        severities = set(events["severity"].tolist()) if not events.empty else set()

        reasons: list[str] = []
        actions: list[str] = []

        # ---- Decision tree ----
        has_overtime = EVENT_OVERTIME_REQUIRED in event_types
        has_deadline = EVENT_DEADLINE_INFEASIBLE in event_types
        has_critical_util = EVENT_UTILIZATION_CRITICAL in event_types or (
            math.isfinite(util) and util > CRITICAL_UTILIZATION_THRESHOLD
        ) or not math.isfinite(util)

        # Critical branch
        if has_deadline or has_overtime or has_critical_util:
            phase_reasons = _phase_reasons(group)
            reasons.extend(phase_reasons)
            for _, ev in events.iterrows():
                reasons.append(str(ev["message"]))

            order_row = orders_by_id.loc[order_id] if orders_by_id is not None and order_id in orders_by_id.index else None
            current_lab = str(order_row["assigned_lab"]) if order_row is not None and "assigned_lab" in order_row else None

            if has_deadline:
                recommendation = REC_POSTPONE
                actions.append("Postpone the order to a later deadline")
                alt = (
                    find_alternative_lab(order_row, current_lab, phase_capacity_df, product_matrix_df)
                    if order_row is not None and phase_capacity_df is not None and product_matrix_df is not None
                    else None
                )
                if alt:
                    actions.append(f"Or reallocate to lab '{alt}'")
            elif has_overtime:
                recommendation = REC_REJECT
                actions.append("Reject — overtime required and lab forbids overtime")
                actions.append("Negotiate deadline extension before re-attempting")
            else:
                # Critical utilization. Prefer SPLIT if quantity is large; otherwise REJECT.
                qty = int(group["quantity"].iloc[0]) if "quantity" in group else 0
                if qty >= 100:
                    recommendation = REC_SPLIT
                    actions.append("Split the order across multiple labs / chains")
                else:
                    recommendation = REC_REJECT
                    actions.append("Reject — capacity insufficient even after reallocation")

            severity = SEVERITY_HIGH

        # At-risk branch
        elif (
            (math.isfinite(util) and util > SAFE_UTILIZATION_THRESHOLD)
            or SEVERITY_MEDIUM in severities
            or EVENT_PHASE_OVERLOAD in event_types
            or EVENT_UTILIZATION_HIGH in event_types
            or EVENT_PARALLEL_OVERLOAD in event_types
            or EVENT_MACHINE_DOWNTIME in event_types
            or EVENT_WORKER_ABSENCE in event_types
        ):
            reasons.extend(_phase_reasons(group))
            if math.isfinite(util):
                reasons.append(f"Worst per-order phase utilization at {util * 100:.0f}% (this order alone)")
            for _, ev in events.iterrows():
                reasons.append(str(ev["message"]))

            order_row = orders_by_id.loc[order_id] if orders_by_id is not None and order_id in orders_by_id.index else None
            current_lab = str(order_row["assigned_lab"]) if order_row is not None and "assigned_lab" in order_row else None
            alt = (
                find_alternative_lab(order_row, current_lab, phase_capacity_df, product_matrix_df)
                if order_row is not None and phase_capacity_df is not None and product_matrix_df is not None
                else None
            )

            if alt:
                recommendation = REC_REALLOCATE
                actions.append(f"Reallocate to lab '{alt}'")
            else:
                recommendation = REC_AT_RISK
                actions.append("Monitor closely; no alternative lab with sufficient capacity")

            severity = SEVERITY_MEDIUM

        # Accept branch
        else:
            recommendation = REC_ACCEPT
            severity = SEVERITY_LOW
            reasons.append(
                f"All phases below {int(SAFE_UTILIZATION_THRESHOLD * 100)}% per-order utilization "
                f"(worst per-order phase {util * 100:.0f}%)"
            )
            reasons.append("No critical stress events detected")
            actions.append("Proceed with production as scheduled")

        # Safety: never emit empty lists
        if not reasons:
            reasons.append("No explicit reasons recorded.")
        if not actions:
            actions.append("No specific action required.")

        rows.append({
            "order_id": order_id,
            "recommendation": recommendation,
            "severity": severity,
            "reasons": reasons,
            "suggested_actions": actions,
        })

    return pd.DataFrame(rows, columns=RECOMMENDATIONS_COLS)


__all__ = ["generate_recommendations", "RECOMMENDATIONS_COLS"]
