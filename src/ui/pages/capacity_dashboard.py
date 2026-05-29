"""Page 3 — Capacity Dashboard (TASK-031)."""
from __future__ import annotations

import math

import streamlit as st

from src.components.alerts import render_alerts, render_recommendation_panel
from src.components.charts import lab_phase_capacity_gap_bar, phase_utilization_bar
from src.components.kpi_cards import kpi_row
from src.engines.bottleneck_engine import identify_bottlenecks
from src.engines.capacity_engine import (
    aggregate_lab_phase,
    compute_capacity_results,
    overall_utilization,
)
from src.engines.recommendation_engine import generate_recommendations
from src.engines.scenario_engine import apply_scenario
from src.engines.stress_engine import evaluate_all_stress
from src.utils.formatting import fmt_int, fmt_minutes, fmt_pct, utilization_status


def render() -> None:
    st.title("Capacity Dashboard")
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
    stress = evaluate_all_stress(
        orders_scn, cap, labs_df, pc_scn, scenario, lab_phase_df=lab_phase
    )
    recs = generate_recommendations(cap, stress, orders_scn, pc_scn, pm_df)

    # --- KPIs (aggregated per lab-phase: capacity counted once) ---
    overall_util = overall_utilization(lab_phase)
    if lab_phase.empty:
        min_gap = 0.0
        total_gap = 0.0
        overloaded_phases = 0
    else:
        min_gap = float(lab_phase["capacity_gap_minutes"].min())
        total_gap = float(lab_phase["capacity_gap_minutes"].sum())
        overloaded_phases = int(lab_phase[lab_phase["is_overloaded"]].shape[0])

    kpi_row([
        {
            "label": "Overall utilization",
            "value": fmt_pct(overall_util) if math.isfinite(overall_util) else "∞",
            "status": utilization_status(overall_util),
        },
        {
            "label": "Minimum capacity gap",
            "value": fmt_minutes(min_gap),
            "status": "critical" if min_gap < 0 else "safe",
        },
        {"label": "Planning window", "value": f"{planning_days} day(s)", "status": "neutral"},
        {
            "label": "Overloaded phases",
            "value": fmt_int(overloaded_phases),
            "status": "critical" if overloaded_phases else "safe",
        },
    ])

    gap_sign = "feasible overall" if total_gap >= 0 else "capacity shortfall"
    st.caption(
        f"Aggregate gap across all lab-phases: **{fmt_minutes(total_gap)}** ({gap_sign}). "
        "The KPI above shows the single most critical lab-phase."
    )

    if summary.get("most_critical_phase"):
        st.caption(
            f"Most critical phase across orders: **{summary['most_critical_phase']}** "
            f"({fmt_pct(summary['most_critical_phase_utilization'])})"
        )

    # --- Chart ---
    st.subheader("Phase utilization")
    st.plotly_chart(phase_utilization_bar(lab_phase), width="stretch")

    st.subheader("Capacity gap by lab-phase")
    st.plotly_chart(lab_phase_capacity_gap_bar(lab_phase), width="stretch")

    # --- Alerts ---
    st.subheader("Operational stress")
    render_alerts(stress, max_items=5)

    # --- Recommendations ---
    st.subheader("Recommendations")
    render_recommendation_panel(recs)
