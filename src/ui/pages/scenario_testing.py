"""Page 6 — Scenario Testing (TASK-034)."""
from __future__ import annotations

import math

import streamlit as st

from src.engines.bottleneck_engine import identify_bottlenecks
from src.engines.capacity_engine import compute_capacity_results
from src.engines.recommendation_engine import generate_recommendations
from src.engines.scenario_engine import ScenarioInputs, apply_scenario
from src.engines.stress_engine import evaluate_all_stress
from src.utils.constants import REC_ACCEPT


def _snapshot(orders, pm, labs, pc, scenario, planning_days) -> dict:
    orders_scn, pc_scn = apply_scenario(orders, pc, scenario)
    cap = compute_capacity_results(orders_scn, pm, labs, pc_scn, planning_days=planning_days)
    cap, _ = identify_bottlenecks(cap)
    stress = evaluate_all_stress(orders_scn, cap, labs, pc_scn, scenario)
    recs = generate_recommendations(cap, stress, orders_scn, pc_scn, pm)

    finite = cap["utilization_rate"].replace([math.inf, -math.inf], math.nan).dropna()
    return {
        "overall_utilization": float(finite.mean()) if not finite.empty else math.inf,
        "overloaded_phases": int(cap[cap["is_overloaded"]]["phase_name"].nunique()),
        "critical_events": int((stress["severity"] == "high").sum()) if not stress.empty else 0,
        "accepted_orders": int((recs["recommendation"] == REC_ACCEPT).sum()) if not recs.empty else 0,
    }


def _format_snapshot(s: dict) -> dict:
    util = s["overall_utilization"]
    return {
        "Overall utilization": f"{util * 100:.0f}%" if math.isfinite(util) else "∞",
        "Overloaded phases": str(s["overloaded_phases"]),
        "Critical events": str(s["critical_events"]),
        "Accepted orders": str(s["accepted_orders"]),
    }


def render() -> None:
    st.title("Scenario Testing")
    data = st.session_state["data"]
    planning_days = st.session_state["planning_days"]

    orders = data["orders"]
    pm = data["product_matrix"]
    labs = data["labs"]
    pc = data["phase_capacity"]

    current: ScenarioInputs = st.session_state["scenario"]

    with st.form("scenario_form"):
        st.write("Adjust scenario modifiers and press Apply to update downstream pages.")
        col1, col2 = st.columns(2)
        with col1:
            demand_multiplier = st.slider("Demand multiplier", 0.5, 2.0, current.demand_multiplier, 0.1)
            efficiency_drop = st.slider("Efficiency drop", 0.0, 0.5, current.efficiency_drop, 0.05)
        with col2:
            absent_workers = st.slider("Absent workers", 0, 5, current.absent_workers, 1)
            machine_downtime = st.slider("Machine downtime", 0.0, 0.5, current.machine_downtime, 0.05)
        urgent_flag = st.checkbox("Mark normal orders as urgent", value=current.urgent_order_flag)

        col_apply, col_reset = st.columns(2)
        submitted = col_apply.form_submit_button("Apply scenario")
        reset = col_reset.form_submit_button("Reset to defaults")

    if submitted:
        st.session_state["scenario"] = ScenarioInputs(
            demand_multiplier=demand_multiplier,
            efficiency_drop=efficiency_drop,
            absent_workers=absent_workers,
            machine_downtime=machine_downtime,
            urgent_order_flag=urgent_flag,
        )
    if reset:
        st.session_state["scenario"] = ScenarioInputs()

    # Before / after comparison
    baseline = _snapshot(orders, pm, labs, pc, ScenarioInputs(), planning_days)
    current_scn = _snapshot(orders, pm, labs, pc, st.session_state["scenario"], planning_days)

    st.subheader("Baseline vs Current scenario")
    base_fmt = _format_snapshot(baseline)
    curr_fmt = _format_snapshot(current_scn)
    rows = [{"Metric": k, "Baseline": base_fmt[k], "Current": curr_fmt[k]} for k in base_fmt]
    st.table(rows)
