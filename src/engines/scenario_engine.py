"""Scenario Engine — PRD §9.9.

Pure transformation: apply user-controlled modifiers to *copies* of the input
DataFrames before the calculation engines run. Originals are never mutated.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ScenarioInputs:
    demand_multiplier: float = 1.0
    efficiency_drop: float = 0.0
    absent_workers: int = 0
    machine_downtime: float = 0.0
    urgent_order_flag: bool = False

    def is_identity(self) -> bool:
        return (
            self.demand_multiplier == 1.0
            and self.efficiency_drop == 0.0
            and self.absent_workers == 0
            and self.machine_downtime == 0.0
            and not self.urgent_order_flag
        )


def _recompute_available_minutes(row: pd.Series) -> float:
    # available_minutes_per_day = workers_assigned × (hours_per_day × 60) × efficiency × uptime
    # We don't have hours_per_day in phase_capacity_df, but we can derive it
    # from the original available_minutes_per_day if needed. Cleanest: keep a
    # ratio relative to the original workers_assigned × efficiency × uptime.
    raise NotImplementedError  # not used; see apply_scenario


def apply_scenario(
    orders_df: pd.DataFrame,
    phase_capacity_df: pd.DataFrame,
    scenario: ScenarioInputs,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return scaled copies of (orders_df, phase_capacity_df). Inputs untouched."""
    orders_out = orders_df.copy()
    cap_out = phase_capacity_df.copy()

    if scenario.is_identity():
        return orders_out, cap_out

    # --- orders adjustments ---
    if scenario.demand_multiplier != 1.0 and not orders_out.empty:
        orders_out["quantity"] = (
            (orders_out["quantity"].astype(float) * scenario.demand_multiplier)
            .round()
            .clip(lower=1)
            .astype(int)
        )

    if scenario.urgent_order_flag and not orders_out.empty and "priority" in orders_out.columns:
        orders_out.loc[orders_out["priority"] == "normal", "priority"] = "urgent"

    # --- phase capacity adjustments ---
    if cap_out.empty:
        return orders_out, cap_out

    # Snapshot original factors so we can rescale available_minutes_per_day.
    eff_orig = cap_out["efficiency"].astype(float).copy()
    upt_orig = cap_out["uptime"].astype(float).copy()
    wa_orig = cap_out["workers_assigned"].astype(int).copy()
    avail_orig = cap_out["available_minutes_per_day"].astype(float).copy()

    new_eff = (eff_orig - scenario.efficiency_drop).clip(lower=0.0)
    new_upt = (upt_orig - scenario.machine_downtime).clip(lower=0.0)
    new_wa = (wa_orig - scenario.absent_workers).clip(lower=0)

    # Scale available_minutes_per_day proportionally:
    #   new_avail = avail_orig × (new_wa/wa_orig) × (new_eff/eff_orig) × (new_upt/upt_orig)
    def safe_ratio(num: pd.Series, den: pd.Series) -> pd.Series:
        denom = den.replace(0, pd.NA)
        return (num / denom).fillna(0.0)

    scale = (
        safe_ratio(new_wa.astype(float), wa_orig.astype(float))
        * safe_ratio(new_eff, eff_orig)
        * safe_ratio(new_upt, upt_orig)
    )
    cap_out["workers_assigned"] = new_wa.astype(int)
    cap_out["efficiency"] = new_eff.astype(float)
    cap_out["uptime"] = new_upt.astype(float)
    cap_out["available_minutes_per_day"] = (avail_orig * scale).astype(float)

    return orders_out, cap_out


__all__ = ["ScenarioInputs", "apply_scenario"]
