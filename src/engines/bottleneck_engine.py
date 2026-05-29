"""Bottleneck Engine — PRD §9.5 / §10.5.

Marks the most-overloaded phase per order, ranks phases within each order,
and returns a global summary identifying the most-critical phase across all
orders.
"""
from __future__ import annotations

import math

import pandas as pd


def identify_bottlenecks(
    capacity_results_df: pd.DataFrame,
    lab_phase_df: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Annotate `capacity_results_df` with bottleneck flags and ranks.

    Args:
        capacity_results_df: Per-order capacity results from compute_capacity_results.
        lab_phase_df: Optional aggregate per-(lab, phase) DataFrame from
            aggregate_lab_phase. When provided, the global most_critical_phase
            is derived from aggregate load rather than the per-order worst case,
            avoiding a single high-utilization order hijacking the headline.

    Returns:
        (df_with_flags, summary)
        summary = {
            "most_critical_phase": str | None,
            "most_critical_phase_utilization": float,
        }
    """
    if capacity_results_df.empty:
        return capacity_results_df.copy(), {
            "most_critical_phase": None,
            "most_critical_phase_utilization": 0.0,
        }

    df = capacity_results_df.copy()
    df["bottleneck_rank"] = (
        df.groupby("order_id")["utilization_rate"]
        .rank(method="first", ascending=False)
        .astype(int)
    )
    df["is_bottleneck"] = df["bottleneck_rank"] == 1

    # Global summary: the phase whose AGGREGATE (lab,phase) load is highest.
    # Aggregate is the real bottleneck; a single critical order no longer hijacks
    # the headline. Falls back to per-order worst case if no aggregate is given.
    most_phase: str
    most_util: float
    if lab_phase_df is not None and not lab_phase_df.empty:
        agg_util = lab_phase_df["utilization_rate"].replace(
            [math.inf, -math.inf], float("nan")
        )
        agg = lab_phase_df.assign(_u=agg_util).dropna(subset=["_u"])
        if not agg.empty:
            idx = agg["_u"].idxmax()
            most_phase = str(agg.loc[idx, "phase_name"])
            most_util = float(agg.loc[idx, "_u"])
        else:
            most_phase = str(lab_phase_df["phase_name"].iloc[0])
            most_util = float(lab_phase_df["utilization_rate"].iloc[0])
    else:
        util = df["utilization_rate"].replace([math.inf, -math.inf], float("nan"))
        finite_df = df.assign(_finite_util=util).dropna(subset=["_finite_util"])
        if finite_df.empty:
            most_phase = df["phase_name"].iloc[0]
            most_util = float(df["utilization_rate"].iloc[0])
        else:
            per_phase = finite_df.groupby("phase_name")["_finite_util"].max()
            most_phase = str(per_phase.idxmax())
            most_util = float(per_phase.max())

    summary = {
        "most_critical_phase": most_phase,
        "most_critical_phase_utilization": most_util,
    }
    df["bottleneck_phase_global"] = most_phase
    return df, summary


__all__ = ["identify_bottlenecks"]
