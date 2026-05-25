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
) -> tuple[pd.DataFrame, dict]:
    """Annotate `capacity_results_df` with bottleneck flags and ranks.

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

    # Global summary: phase with the highest *mean* utilization across orders.
    # Replace inf with a large finite value so groupby.mean() doesn't degenerate.
    util = df["utilization_rate"].replace([math.inf, -math.inf], float("nan"))
    finite_df = df.assign(_finite_util=util).dropna(subset=["_finite_util"])
    if finite_df.empty:
        most_phase = df["phase_name"].iloc[0]
        most_util = float(df["utilization_rate"].iloc[0])
    else:
        per_phase = finite_df.groupby("phase_name")["_finite_util"].mean()
        most_phase = str(per_phase.idxmax())
        most_util = float(per_phase.max())

    summary = {
        "most_critical_phase": most_phase,
        "most_critical_phase_utilization": most_util,
    }
    df["bottleneck_phase_global"] = most_phase
    return df, summary


__all__ = ["identify_bottlenecks"]
