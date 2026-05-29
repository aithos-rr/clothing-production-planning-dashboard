"""Page 5 — Timeline (TASK-033)."""
from __future__ import annotations

import streamlit as st

from src.components.timeline import render_timeline_chart
from src.engines.capacity_engine import compute_capacity_results
from src.engines.scenario_engine import apply_scenario
from src.engines.timeline_engine import build_timeline
from src.utils.constants import (
    STATUS_COLORS,
    TIMELINE_AT_RISK,
    TIMELINE_BLOCKED,
    TIMELINE_LATE,
    TIMELINE_ON_TRACK,
)


def render() -> None:
    st.title("Timeline")
    data = st.session_state["data"]
    scenario = st.session_state["scenario"]
    planning_days = st.session_state["planning_days"]

    orders_df = data["orders"]
    pm_df = data["product_matrix"]
    labs_df = data["labs"]
    pc_df = data["phase_capacity"]

    orders_scn, pc_scn = apply_scenario(orders_df, pc_df, scenario)
    cap = compute_capacity_results(orders_scn, pm_df, labs_df, pc_scn, planning_days=planning_days)
    timeline = build_timeline(orders_scn, cap, pc_scn, planning_days=planning_days)

    if timeline.empty:
        st.info("No orders to display in the timeline yet.")
        return

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        lab_options = sorted(timeline["assigned_lab"].dropna().unique().tolist())
        sel_labs = st.multiselect("Lab", lab_options, default=lab_options)
    with col2:
        status_options = [TIMELINE_ON_TRACK, TIMELINE_AT_RISK, TIMELINE_LATE, TIMELINE_BLOCKED]
        sel_status = st.multiselect("Status", status_options, default=status_options)

    filtered = timeline[
        timeline["assigned_lab"].isin(sel_labs) & timeline["status"].isin(sel_status)
    ]
    st.plotly_chart(render_timeline_chart(filtered), width="stretch")

    # Legend
    legend_html = (
        f"<span style='color:{STATUS_COLORS['safe']}'>● on_track</span> &nbsp; "
        f"<span style='color:{STATUS_COLORS['at_risk']}'>● at_risk</span> &nbsp; "
        f"<span style='color:{STATUS_COLORS['critical']}'>● late</span> &nbsp; "
        f"<span style='color:{STATUS_COLORS['neutral']}'>● blocked (no capacity defined)</span>"
    )
    st.markdown(legend_html, unsafe_allow_html=True)
