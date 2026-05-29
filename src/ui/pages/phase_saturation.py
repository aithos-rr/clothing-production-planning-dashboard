"""Page 4 — Phase Saturation (TASK-032)."""
from __future__ import annotations

import math

import streamlit as st

from src.components.charts import phase_utilization_bar
from src.components.kpi_cards import kpi_card, kpi_row
from src.engines.bottleneck_engine import identify_bottlenecks
from src.engines.capacity_engine import aggregate_lab_phase, compute_capacity_results
from src.engines.scenario_engine import apply_scenario
from src.utils.formatting import fmt_int, fmt_minutes, fmt_pct, utilization_status


def render() -> None:
    st.title("Phase Saturation")
    data = st.session_state["data"]
    scenario = st.session_state["scenario"]
    planning_days = st.session_state["planning_days"]

    orders_df = data["orders"]
    pm_df = data["product_matrix"]
    labs_df = data["labs"]
    pc_df = data["phase_capacity"]

    orders_scn, pc_scn = apply_scenario(orders_df, pc_df, scenario)
    cap = compute_capacity_results(orders_scn, pm_df, labs_df, pc_scn, planning_days=planning_days)
    lab_phase = aggregate_lab_phase(cap)
    cap, summary = identify_bottlenecks(cap, lab_phase)

    most_phase = summary.get("most_critical_phase") or "—"
    most_util = summary.get("most_critical_phase_utilization", 0.0)
    kpi_card(
        label="Most critical phase",
        value=f"{most_phase} · {fmt_pct(most_util) if math.isfinite(most_util) else '∞'}",
        status=utilization_status(most_util),
    )

    overloaded_count = int(lab_phase[lab_phase["is_overloaded"]].shape[0]) if not lab_phase.empty else 0
    kpi_row([
        {
            "label": "Phases overloaded",
            "value": fmt_int(overloaded_count),
            "status": "critical" if overloaded_count else "safe",
        },
        {
            "label": "Lab-phases evaluated",
            "value": fmt_int(int(lab_phase.shape[0])),
            "status": "neutral",
        },
    ])

    st.subheader("Utilization by lab-phase")
    st.plotly_chart(phase_utilization_bar(lab_phase), width="stretch")

    # Per lab-phase table — AGGREGATE load (capacity counted once).
    st.subheader("Detail per lab-phase")
    if lab_phase.empty:
        st.info("No capacity data yet.")
    else:
        lp = lab_phase.copy()
        lp["status"] = lp["utilization_rate"].apply(utilization_status)
        lp["utilization"] = lp["utilization_rate"].apply(
            lambda v: fmt_pct(v) if math.isfinite(v) else "∞"
        )
        lp["total_required"] = lp["total_required_minutes"].apply(fmt_minutes)
        lp["available"] = lp["available_minutes"].apply(fmt_minutes)
        lp["capacity_gap"] = lp["capacity_gap_minutes"].apply(fmt_minutes)
        st.dataframe(
            lp[[
                "assigned_lab", "phase_name", "utilization",
                "total_required", "available", "capacity_gap", "num_orders", "status",
            ]].sort_values(["status", "assigned_lab"]),
            width="stretch",
        )

    # Per-order detail — each order's CONTRIBUTION to the shared lab-phase.
    # (A single order can look light here yet the lab-phase is overloaded in
    # aggregate — see the table above.)
    st.subheader("Detail per order (contribution to shared phase)")
    finite = cap.copy()
    finite["_util"] = finite["utilization_rate"].replace([math.inf, -math.inf], math.nan)
    per_order = (
        finite.groupby(["order_id", "product_type", "phase_name"])
        .agg(
            utilization=("_util", "max"),
            required_minutes=("required_minutes", "sum"),
            available_minutes=("available_minutes", "max"),
            capacity_gap_minutes=("capacity_gap_minutes", "sum"),
        )
        .reset_index()
    )
    per_order["status"] = per_order["utilization"].apply(utilization_status)
    per_order_display = per_order.copy()
    per_order_display["utilization"] = per_order_display["utilization"].apply(
        lambda v: fmt_pct(v) if v is not None and math.isfinite(v) else "∞"
    )
    per_order_display["required_minutes"] = per_order_display["required_minutes"].apply(fmt_minutes)
    per_order_display["available_minutes"] = per_order_display["available_minutes"].apply(fmt_minutes)
    per_order_display["capacity_gap"] = per_order_display["capacity_gap_minutes"].apply(fmt_minutes)
    st.dataframe(
        per_order_display[
            [
                "order_id", "product_type", "phase_name",
                "utilization", "required_minutes", "available_minutes",
                "capacity_gap", "status",
            ]
        ].sort_values(["status", "order_id"], ascending=[True, True]),
        width="stretch",
    )
