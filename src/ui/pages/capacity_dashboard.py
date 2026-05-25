"""Page 3 — Capacity Dashboard (TASK-031)."""
from __future__ import annotations

import math

import streamlit as st

from src.components.alerts import render_alerts, render_recommendation_panel
from src.components.charts import phase_utilization_bar
from src.components.kpi_cards import kpi_row
from src.engines.bottleneck_engine import identify_bottlenecks
from src.engines.capacity_engine import compute_capacity_results
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
    cap, summary = identify_bottlenecks(cap)
    stress = evaluate_all_stress(orders_scn, cap, labs_df, pc_scn, scenario)
    recs = generate_recommendations(cap, stress, orders_scn, pc_scn, pm_df)

    # --- KPIs ---
    finite_util = cap["utilization_rate"].replace([math.inf, -math.inf], math.nan).dropna()
    overall_util = float(finite_util.mean()) if not finite_util.empty else math.inf
    total_gap = float(cap["capacity_gap_minutes"].sum())
    overloaded_phases = int(cap[cap["is_overloaded"]]["phase_name"].nunique())

    kpi_row([
        {
            "label": "Overall utilization",
            "value": fmt_pct(overall_util) if math.isfinite(overall_util) else "∞",
            "status": utilization_status(overall_util),
        },
        {
            "label": "Total capacity gap",
            "value": fmt_minutes(total_gap),
            "status": "critical" if total_gap < 0 else "safe",
        },
        {"label": "Planning window", "value": f"{planning_days} day(s)", "status": "neutral"},
        {
            "label": "Overloaded phases",
            "value": fmt_int(overloaded_phases),
            "status": "critical" if overloaded_phases else "safe",
        },
    ])

    if summary.get("most_critical_phase"):
        st.caption(
            f"Most critical phase across orders: **{summary['most_critical_phase']}** "
            f"({fmt_pct(summary['most_critical_phase_utilization'])})"
        )

    # --- Chart ---
    st.subheader("Phase utilization")
    st.plotly_chart(phase_utilization_bar(cap), width="stretch")

    # --- Alerts ---
    st.subheader("Operational stress")
    render_alerts(stress, max_items=5)

    # --- Recommendations ---
    st.subheader("Recommendations")
    render_recommendation_panel(recs)
