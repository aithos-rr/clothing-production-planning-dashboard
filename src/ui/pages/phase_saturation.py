"""Page 4 — Phase Saturation (TASK-032)."""
from __future__ import annotations

import math

import streamlit as st

from src.components.charts import phase_utilization_bar
from src.components.kpi_cards import kpi_card, kpi_row
from src.engines.bottleneck_engine import identify_bottlenecks
from src.engines.capacity_engine import compute_capacity_results
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
    cap, summary = identify_bottlenecks(cap)

    # Prominent "most critical phase" card
    most_phase = summary.get("most_critical_phase") or "—"
    most_util = summary.get("most_critical_phase_utilization", 0.0)
    kpi_card(
        label="Most critical phase",
        value=f"{most_phase} · {fmt_pct(most_util) if math.isfinite(most_util) else '∞'}",
        status=utilization_status(most_util),
    )

    # Workers-at-risk indicator
    overloaded_count = int(cap[cap["is_overloaded"]]["phase_name"].nunique())
    kpi_row([
        {
            "label": "Phases overloaded",
            "value": fmt_int(overloaded_count),
            "status": "critical" if overloaded_count else "safe",
        },
        {
            "label": "Total phases evaluated",
            "value": fmt_int(int(cap["phase_name"].nunique())),
            "status": "neutral",
        },
    ])

    st.subheader("Utilization by phase")
    st.plotly_chart(phase_utilization_bar(cap), width="stretch")

    # Per-phase table.
    # Status is driven by the WORST case (max utilization) — a single overloaded
    # order is enough to make a phase operationally critical, even if the mean
    # across orders looks healthy.
    finite = cap.copy()
    finite["_util"] = finite["utilization_rate"].replace([math.inf, -math.inf], math.nan)
    per_phase = (
        finite.groupby("phase_name")
        .agg(
            avg_utilization=("_util", "mean"),
            max_utilization=("_util", "max"),
            bottleneck=("is_bottleneck", "any"),
            capacity_gap_minutes=("capacity_gap_minutes", "sum"),
        )
        .reset_index()
    )
    per_phase["status"] = per_phase["max_utilization"].apply(utilization_status)
    per_phase["bottleneck"] = per_phase["bottleneck"].map({True: "✓", False: ""})
    per_phase["avg_utilization"] = per_phase["avg_utilization"].apply(
        lambda v: fmt_pct(v) if v is not None and math.isfinite(v) else "∞"
    )
    per_phase["max_utilization"] = per_phase["max_utilization"].apply(
        lambda v: fmt_pct(v) if v is not None and math.isfinite(v) else "∞"
    )
    per_phase["capacity_gap"] = per_phase["capacity_gap_minutes"].apply(fmt_minutes)
    st.subheader("Detail per phase")
    st.dataframe(
        per_phase[
            ["phase_name", "avg_utilization", "max_utilization", "bottleneck", "capacity_gap", "status"]
        ],
        width="stretch",
    )

    # Per-order detail — surfaces which order is dragging a phase into the red.
    st.subheader("Detail per order")
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
