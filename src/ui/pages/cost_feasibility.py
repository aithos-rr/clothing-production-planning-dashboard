"""Page 7 — Cost Feasibility Dashboard (Economic Layer v2, cost-focused)."""
from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from src.components.alerts import render_recommendation_panel
from src.components.charts import cost_vs_risk_scatter
from src.components.kpi_cards import kpi_row
from src.engines.bottleneck_engine import identify_bottlenecks
from src.engines.capacity_engine import aggregate_lab_phase, compute_capacity_results
from src.engines.economic_engine import compute_economic_results
from src.engines.recommendation_engine import generate_recommendations
from src.engines.scenario_engine import apply_scenario
from src.engines.stress_engine import evaluate_all_stress
from src.parsers.economic_inputs import EconomicInputs
from src.utils.config import get_default
from src.utils.formatting import fmt_int


def _eur(v: float) -> str:
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return "—"
    return f"€{v:,.0f}"


def render() -> None:
    st.title("Cost Feasibility Dashboard")
    st.caption(
        "Economic layer — estimates production cost, overtime cost and the cost "
        "impact of reallocation. Cost-focused: margin/profitability are out of scope."
    )

    data = st.session_state["data"]
    scenario = st.session_state["scenario"]
    planning_days = st.session_state["planning_days"]

    orders_df = data["orders"]
    pm_df = data["product_matrix"]
    labs_df = data["labs"]
    pc_df = data["phase_capacity"]
    econ: EconomicInputs = data.get("economic_inputs") or EconomicInputs(uses_default=True)

    orders_scn, pc_scn = apply_scenario(orders_df, pc_df, scenario)
    cap = compute_capacity_results(orders_scn, pm_df, labs_df, pc_scn, planning_days=planning_days)
    lab_phase = aggregate_lab_phase(cap)
    cap, _ = identify_bottlenecks(cap, lab_phase)
    stress = evaluate_all_stress(orders_scn, cap, labs_df, pc_scn, scenario, lab_phase_df=lab_phase)
    op_recs = generate_recommendations(cap, stress, orders_scn, pc_scn, pm_df)

    econ_df = compute_economic_results(cap, orders_scn, pc_scn, pm_df, econ, labs_df=labs_df, operational_recs_df=op_recs)

    if econ_df.empty:
        st.info("No economic results — load data on the Upload page.")
        return

    if econ.uses_default:
        st.warning("Some cost values are estimated using default assumptions.")

    # --- Aggregate KPIs (cost-focused) ---
    total_cost = float(econ_df["total_estimated_cost"].sum())
    total_overtime = float(econ_df["overtime_cost"].sum())
    total_labour = float(econ_df["standard_labour_cost"].sum())
    realloc_saving = float(
        econ_df.loc[econ_df["cost_delta_if_reallocated"] < 0, "cost_delta_if_reallocated"].sum()
    )
    kpi_row([
        {"label": "Total estimated production cost", "value": _eur(total_cost), "status": "neutral"},
        {"label": "Overtime cost", "value": _eur(total_overtime), "status": "critical" if total_overtime > 0 else "safe"},
        {"label": "Standard labour cost", "value": _eur(total_labour), "status": "neutral"},
        {"label": "Cost impact of reallocation", "value": _eur(realloc_saving), "status": "at_risk" if realloc_saving < 0 else "safe"},
    ])

    # --- Order selector ---
    order_ids = econ_df["order_id"].tolist()
    sel = st.selectbox("Focus order", order_ids)
    row = econ_df[econ_df["order_id"] == sel].iloc[0]

    # --- Cost breakdown table ---
    st.subheader("Order cost breakdown")
    total = row["total_estimated_cost"] or 0.0
    components = [
        ("Standard labour", row["standard_labour_cost"]),
        ("Overtime", row["overtime_cost"]),
        ("Setup", row["setup_cost"]),
        ("Overhead", row["overhead_cost"]),
        ("Total estimated cost", total),
    ]
    breakdown = pd.DataFrame(
        [
            {"Cost component": name, "Amount (€)": f"{amt:,.2f}",
             "% of total": (f"{(amt / total * 100):.1f}%" if total and name != "Total estimated cost" else ("100.0%" if name == "Total estimated cost" else "—"))}
            for name, amt in components
        ]
    )
    st.dataframe(breakdown, hide_index=True, width="stretch")

    # --- Lab comparison ---
    st.subheader("Lab comparison")
    cur_lab = row["assigned_lab"]
    alt_lab = row["alternative_lab"]
    lab_rows = [{"Lab": cur_lab, "Estimated cost (€)": f"{row['total_estimated_cost']:,.0f}",
                 "Role": "current", "Cost delta (€)": "—"}]
    if alt_lab and isinstance(alt_lab, str):
        lab_rows.append({"Lab": alt_lab, "Estimated cost (€)": f"{row['alternative_total_cost']:,.0f}",
                         "Role": "alternative", "Cost delta (€)": f"{row['cost_delta_if_reallocated']:,.0f}"})
    st.dataframe(pd.DataFrame(lab_rows), hide_index=True, width="stretch")

    # --- Cost vs risk chart (current vs alternative) ---
    st.subheader("Cost vs operational risk")
    util_lookup = (
        lab_phase.groupby("assigned_lab")["utilization_rate"]
        .max().replace([math.inf], 1.5).to_dict()
        if not lab_phase.empty else {}
    )
    pts = [{"label": str(cur_lab), "estimated_cost": float(row["total_estimated_cost"]), "utilization": float(util_lookup.get(cur_lab, 0.0))}]
    if alt_lab and isinstance(alt_lab, str):
        pts.append({"label": str(alt_lab), "estimated_cost": float(row["alternative_total_cost"]), "utilization": float(util_lookup.get(alt_lab, 0.0))})
    st.plotly_chart(cost_vs_risk_scatter(pd.DataFrame(pts)), width="stretch")

    # --- Economic alerts ---
    st.subheader("Economic alerts")
    alerts_shown = False
    if row["overtime_cost"] and row["overtime_cost"] > 0:
        st.warning(f"Overtime increases production cost by {_eur(row['overtime_cost'])}.")
        alerts_shown = True
    if isinstance(alt_lab, str) and math.isfinite(row["cost_delta_if_reallocated"]) and row["cost_delta_if_reallocated"] < 0:
        st.info(f"Alternative lab '{alt_lab}' reduces estimated cost by {_eur(-row['cost_delta_if_reallocated'])}.")
        alerts_shown = True
    if row["uses_default_costs"]:
        st.warning("Cost values for this order use default assumptions.")
        alerts_shown = True
    if not alerts_shown:
        st.success("No economic alerts for this order.")

    # --- Combined recommendation ---
    st.subheader("Recommendation (operational + economic)")
    op_row = op_recs[op_recs["order_id"] == sel]
    op_label = str(op_row.iloc[0]["recommendation"]) if not op_row.empty else "—"
    st.markdown(f"**Operational:** {op_label}  ·  **Economic:** {row['economic_recommendation']}")
    combined = pd.DataFrame([{
        "order_id": sel,
        "recommendation": row["economic_recommendation"],
        "severity": "low" if row["economic_recommendation"] == "ACCEPT" else "medium",
        "reasons": [row["economic_reason"], f"Operational layer: {op_label}"],
        "suggested_actions": [
            f"Reallocate to '{alt_lab}'" if row["economic_recommendation"] == "REALLOCATE" and isinstance(alt_lab, str)
            else "Proceed as scheduled" if row["economic_recommendation"] == "ACCEPT"
            else row["economic_recommendation"].title()
        ],
    }])
    render_recommendation_panel(combined)
