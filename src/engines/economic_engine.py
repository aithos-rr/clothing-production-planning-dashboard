"""Economic Engine — PRD v2 (cost-focused; margin intentionally excluded).

Pure formula functions (validated to the cent against the economic_layer
workbook) + `compute_economic_results` which plugs into the live capacity
pipeline. required_hours derives from capacity_results_df (the dashboard's own
truth), NOT from an SMV column, so the layer reacts to scenarios.
"""
from __future__ import annotations

import math

import pandas as pd

from src.engines.lab_allocation_engine import find_alternative_lab
from src.parsers.economic_inputs import EconomicInputs
from src.utils.config import get_default
from src.utils.constants import (
    CRITICAL_UTILIZATION_THRESHOLD,
    ECON_ACCEPT,
    ECON_ACCEPT_OVERTIME,
    ECON_POSTPONE,
    ECON_REALLOCATE,
    ECON_REJECT,
    EVENT_DEADLINE_INFEASIBLE,
    REC_POSTPONE,
    REC_REJECT,
)

ECONOMIC_RESULTS_COLS = [
    "order_id", "assigned_lab", "product_type", "quantity",
    "required_hours", "available_hours",
    "standard_labour_cost", "overtime_hours", "overtime_cost",
    "setup_cost", "overhead_cost", "total_estimated_cost",
    "cost_per_garment_internal",
    "alternative_lab", "alternative_total_cost", "cost_delta_if_reallocated",
    "economic_recommendation", "economic_reason", "uses_default_costs",
]


# ---- Pure formula functions (PRD §8) ----
def standard_labour_cost(required_hours: float, hourly_cost: float) -> float:
    return float(required_hours) * float(hourly_cost)


def excess_hours(required_hours: float, available_hours: float) -> float:
    return max(0.0, float(required_hours) - float(available_hours))


def overtime_cost(excess_h: float, hourly_cost: float, overtime_multiplier: float) -> float:
    return float(excess_h) * float(hourly_cost) * float(overtime_multiplier)


def overhead_cost(labour: float, overtime: float, setup: float, overhead_pct: float) -> float:
    return (float(labour) + float(overtime) + float(setup)) * float(overhead_pct)


def total_estimated_cost(labour: float, overtime: float, setup: float, overhead: float) -> float:
    return float(labour) + float(overtime) + float(setup) + float(overhead)


def _order_cost_on_lab(
    required_hours: float,
    available_hours: float,
    lab_id: str,
    product_type: str,
    order_id: str,
    econ: EconomicInputs,
    overtime_allowed: bool,
) -> tuple[float, float, float, float, float, float]:
    """Return (labour, excess_h, ot_cost, setup, overhead, total) for an order on a lab."""
    hourly = econ.hourly_cost(lab_id)
    labour = standard_labour_cost(required_hours, hourly)
    exc = excess_hours(required_hours, available_hours)
    ot = overtime_cost(exc, hourly, econ.overtime_multiplier(lab_id)) if (exc > 0 and overtime_allowed) else 0.0
    setup = econ.setup_cost(order_id)
    oh = overhead_cost(labour, ot, setup, econ.overhead_pct(product_type))
    total = total_estimated_cost(labour, ot, setup, oh)
    return labour, exc, ot, setup, oh, total


def _overtime_allowed_for_lab(labs_df: pd.DataFrame | None, lab_id: str) -> bool:
    if labs_df is None or labs_df.empty or "lab_id" not in labs_df.columns:
        return False
    match = labs_df[labs_df["lab_id"].astype(str) == str(lab_id)]
    if match.empty or "overtime_allowed" not in match.columns:
        return False
    return bool(match.iloc[0]["overtime_allowed"])


def _available_hours_for_order(group: pd.DataFrame) -> float:
    """Sum available_minutes across the order's phases / 60. inf-safe."""
    vals = [v for v in group["available_minutes"].tolist() if math.isfinite(v)]
    return sum(vals) / 60.0 if vals else 0.0


def _lab_available_hours(
    phase_capacity_df: pd.DataFrame,
    product_matrix_df: pd.DataFrame,
    lab_id: str,
    product_type: str,
    planning_days: int,
) -> float:
    """Available hours for a lab across the product's phases (its OWN capacity).

    Mirrors the capacity engine: available_minutes_per_day summed over the
    product's phases for `lab_id`, scaled by planning_days, converted to hours.
    """
    if phase_capacity_df is None or phase_capacity_df.empty or product_matrix_df is None or product_matrix_df.empty:
        return 0.0
    phases = (
        product_matrix_df[product_matrix_df["product_type"] == product_type]["phase_name"]
        .dropna().unique().tolist()
    )
    if not phases:
        return 0.0
    rows = phase_capacity_df[
        (phase_capacity_df["lab_id"].astype(str) == str(lab_id))
        & (phase_capacity_df["phase_name"].isin(phases))
    ]
    if rows.empty:
        return 0.0
    return float(rows["available_minutes_per_day"].sum()) * float(planning_days) / 60.0


def compute_economic_results(
    capacity_results_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    phase_capacity_df: pd.DataFrame,
    product_matrix_df: pd.DataFrame,
    econ: EconomicInputs,
    labs_df: pd.DataFrame | None = None,
    operational_recs_df: pd.DataFrame | None = None,
    planning_days: int = 5,
) -> pd.DataFrame:
    if capacity_results_df is None or capacity_results_df.empty:
        return pd.DataFrame(columns=ECONOMIC_RESULTS_COLS)

    threshold = float(get_default("reallocation_material_threshold_eur"))
    orders_by_id = orders_df.set_index("order_id") if orders_df is not None and not orders_df.empty else None
    rec_by_order = (
        operational_recs_df.set_index("order_id")
        if operational_recs_df is not None and not operational_recs_df.empty
        else None
    )
    work = capacity_results_df[capacity_results_df["phase_name"] != "<unknown product>"]

    rows: list[dict] = []
    for order_id, group in work.groupby("order_id"):
        lab = str(group["assigned_lab"].iloc[0])
        product_type = str(group["product_type"].iloc[0])
        quantity = int(group["quantity"].iloc[0]) if "quantity" in group else 0
        # Prefer the standard-minutes-per-garment (SMV) basis when the workbook
        # provides it: required_hours = quantity * smv / 60. This is the apparel
        # costing standard and reconciles with the source workbook's economics.
        # Falls back to the per-phase capacity-engine hours when no SMV is given.
        smv = econ.smv(order_id)
        if smv is not None and smv > 0:
            required_hours = quantity * float(smv) / 60.0
        else:
            required_hours = float(group["required_minutes"].sum()) / 60.0
        available_hours = _available_hours_for_order(group)
        ot_allowed = _overtime_allowed_for_lab(labs_df, lab)

        labour, exc, ot, setup, oh, total = _order_cost_on_lab(
            required_hours, available_hours, lab, product_type, str(order_id), econ, ot_allowed
        )
        cpg = (total / quantity) if quantity > 0 else float("nan")

        # Alternative lab cost
        order_row = orders_by_id.loc[order_id] if orders_by_id is not None and order_id in orders_by_id.index else None
        alt_lab = (
            find_alternative_lab(order_row, lab, phase_capacity_df, product_matrix_df)
            if order_row is not None else None
        )
        if alt_lab:
            alt_available_hours = _lab_available_hours(
                phase_capacity_df, product_matrix_df, alt_lab, product_type, planning_days
            )
            _, _, _, _, _, alt_total = _order_cost_on_lab(
                required_hours, alt_available_hours, alt_lab, product_type, str(order_id), econ,
                _overtime_allowed_for_lab(labs_df, alt_lab),
            )
            cost_delta = alt_total - total
        else:
            alt_total = float("nan")
            cost_delta = float("nan")

        # Operational signals
        op_rec = str(rec_by_order.loc[order_id]["recommendation"]) if rec_by_order is not None and order_id in rec_by_order.index else None
        infeasible = (
            (op_rec == REC_REJECT)
            or (~group["utilization_rate"].apply(math.isfinite)).any()
        )
        has_deadline_issue = op_rec in {REC_POSTPONE} or (group["utilization_rate"].replace([math.inf], 9e9) > CRITICAL_UTILIZATION_THRESHOLD).any()

        # ---- Decision tree (5 cost-driven types) ----
        if infeasible and not alt_lab:
            rec = ECON_REJECT
            reason = "Operationally infeasible and no alternative lab with capacity."
        elif exc > 0 and has_deadline_issue:
            rec = ECON_POSTPONE
            if ot_allowed:
                reason = f"Overtime of {exc:.1f}h required to hit the deadline; postponing avoids the premium."
            else:
                reason = f"Required hours exceed capacity by {exc:.1f}h and this lab cannot use overtime; postpone to avoid infeasibility."
        elif exc > 0 and ot_allowed and not (alt_lab and cost_delta <= -threshold):
            rec = ECON_ACCEPT_OVERTIME
            reason = f"Overtime of {exc:.1f}h required (+€{ot:,.0f}); lab permits overtime."
        elif alt_lab and math.isfinite(cost_delta) and cost_delta <= -threshold:
            rec = ECON_REALLOCATE
            reason = f"Lab '{alt_lab}' is materially cheaper (€{cost_delta:,.0f} vs current)."
        else:
            rec = ECON_ACCEPT
            reason = f"Estimated cost €{total:,.0f}; no materially cheaper lab and no overtime."

        rows.append({
            "order_id": order_id,
            "assigned_lab": lab,
            "product_type": product_type,
            "quantity": quantity,
            "required_hours": required_hours,
            "available_hours": available_hours,
            "standard_labour_cost": labour,
            "overtime_hours": exc if ot_allowed else 0.0,
            "overtime_cost": ot,
            "setup_cost": setup,
            "overhead_cost": oh,
            "total_estimated_cost": total,
            "cost_per_garment_internal": cpg,
            "alternative_lab": alt_lab,
            "alternative_total_cost": alt_total,
            "cost_delta_if_reallocated": cost_delta,
            "economic_recommendation": rec,
            "economic_reason": reason,
            "uses_default_costs": bool(econ.uses_default),
        })

    return pd.DataFrame(rows, columns=ECONOMIC_RESULTS_COLS)


__all__ = [
    "standard_labour_cost",
    "excess_hours",
    "overtime_cost",
    "overhead_cost",
    "total_estimated_cost",
    "compute_economic_results",
    "ECONOMIC_RESULTS_COLS",
]
