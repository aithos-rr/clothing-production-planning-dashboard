"""Page 1 — Overview (TASK-029)."""
from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from src.components.kpi_cards import kpi_row
from src.engines.bottleneck_engine import identify_bottlenecks
from src.engines.capacity_engine import compute_capacity_results
from src.engines.scenario_engine import apply_scenario
from src.engines.stress_engine import evaluate_all_stress
from src.utils.formatting import fmt_int, fmt_pct, utilization_status


def _dataset_status() -> tuple[str, str]:
    """Return (label, status_color_key)."""
    data = st.session_state.get("data")
    if data is None:
        return "No data — upload a file or enable demo mode", "neutral"
    used_mock = data.get("used_mock", {})
    if any(used_mock.values()):
        sheets = ", ".join(k for k, v in used_mock.items() if v)
        return f"Demo mode — using sample data for: {sheets}", "at_risk"
    return "Live data loaded", "safe"


def _compute_overview_kpis() -> list[dict]:
    data = st.session_state.get("data")
    if data is None:
        return [
            {"label": "Orders", "value": "—", "status": "neutral"},
            {"label": "Product types", "value": "—", "status": "neutral"},
            {"label": "Overall utilization", "value": "—", "status": "neutral"},
            {"label": "Critical alerts", "value": "—", "status": "neutral"},
        ]

    orders_df = data["orders"]
    pm_df = data["product_matrix"]
    labs_df = data["labs"]
    pc_df = data["phase_capacity"]
    scenario = st.session_state["scenario"]
    planning_days = st.session_state["planning_days"]

    orders_scn, pc_scn = apply_scenario(orders_df, pc_df, scenario)
    cap = compute_capacity_results(orders_scn, pm_df, labs_df, pc_scn, planning_days=planning_days)
    cap, _ = identify_bottlenecks(cap)
    stress = evaluate_all_stress(orders_scn, cap, labs_df, pc_scn, scenario)

    n_orders = len(orders_df)
    n_products = pm_df["product_type"].nunique() if not pm_df.empty else 0

    finite = cap["utilization_rate"].replace([math.inf, -math.inf], math.nan).dropna()
    overall_util = float(finite.mean()) if not finite.empty else math.inf
    crit_alerts = int((stress["severity"] == "high").sum()) if not stress.empty else 0

    return [
        {"label": "Orders", "value": fmt_int(n_orders), "status": "neutral"},
        {"label": "Product types", "value": fmt_int(n_products), "status": "neutral"},
        {
            "label": "Overall utilization",
            "value": fmt_pct(overall_util) if math.isfinite(overall_util) else "∞",
            "status": utilization_status(overall_util),
        },
        {
            "label": "Critical alerts",
            "value": fmt_int(crit_alerts),
            "status": "critical" if crit_alerts > 0 else "safe",
        },
    ]


def render() -> None:
    st.title("Marvi — Operational Planning")
    st.write(
        "Lightweight operational planning platform for fashion manufacturing. "
        "Replaces fragmented Excel workflows with a centralized dashboard that "
        "computes capacity, identifies bottlenecks, monitors operational stress, "
        "and produces clear recommendations."
    )
    st.write(
        "This MVP is rule-based and deterministic. Advanced AI features "
        "(predictive delays, optimization, forecasting) live on the "
        "Future AI Layer page as planned extensions."
    )

    label, status_key = _dataset_status()
    kpi_row([{"label": "Dataset status", "value": label, "status": status_key}])

    st.subheader("Headline KPIs")
    kpi_row(_compute_overview_kpis())
