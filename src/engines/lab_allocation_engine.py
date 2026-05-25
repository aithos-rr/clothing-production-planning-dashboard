"""Lab / Chain Allocation Engine — PRD §5.1 (gap-filled by TASK-018B).

Decides which lab processes each order when `assigned_lab` is missing, and
provides `find_alternative_lab(...)` used by the recommendation engine for
the REALLOCATE branch.
"""
from __future__ import annotations

import pandas as pd

from src.utils.constants import SEVERITY_MEDIUM
from src.utils.validation import ValidationWarning


def _phases_for_product(
    product_matrix_df: pd.DataFrame,
    product_type: str,
) -> list[str]:
    if product_matrix_df.empty or "product_type" not in product_matrix_df.columns:
        return []
    return (
        product_matrix_df[product_matrix_df["product_type"] == product_type]["phase_name"]
        .dropna()
        .unique()
        .tolist()
    )


def _aggregate_capacity(
    phase_capacity_df: pd.DataFrame,
    lab_id: str,
    phases: list[str],
) -> float:
    """Sum available_minutes_per_day across the given phases for a lab."""
    if phase_capacity_df.empty or not phases:
        return 0.0
    rows = phase_capacity_df[
        (phase_capacity_df["lab_id"] == lab_id)
        & (phase_capacity_df["phase_name"].isin(phases))
    ]
    if rows.empty:
        return 0.0
    return float(rows["available_minutes_per_day"].sum())


def _candidate_labs(phase_capacity_df: pd.DataFrame) -> list[str]:
    if phase_capacity_df.empty:
        return []
    return sorted(phase_capacity_df["lab_id"].dropna().unique().tolist())


def allocate_orders(
    orders_df: pd.DataFrame,
    phase_capacity_df: pd.DataFrame,
    product_matrix_df: pd.DataFrame,
) -> tuple[pd.DataFrame, list[ValidationWarning]]:
    """Fill missing assigned_lab / assigned_chain. Never mutates input."""
    warnings: list[ValidationWarning] = []
    if orders_df.empty:
        return orders_df.copy(), warnings

    out = orders_df.copy()
    labs = _candidate_labs(phase_capacity_df)

    def needs_lab(v) -> bool:
        return v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() in ("", "Default Lab")

    def needs_chain(v) -> bool:
        return v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == ""

    for idx, row in out.iterrows():
        if "assigned_lab" in out.columns and needs_lab(row.get("assigned_lab")):
            if not labs:
                warnings.append(
                    ValidationWarning(
                        "assigned_lab",
                        f"No labs available to allocate order {row.get('order_id')}.",
                        SEVERITY_MEDIUM,
                    )
                )
                continue
            phases = _phases_for_product(product_matrix_df, row.get("product_type"))
            scored = [(lab, _aggregate_capacity(phase_capacity_df, lab, phases)) for lab in labs]
            # Highest capacity wins; deterministic tie-break by lab_id.
            scored.sort(key=lambda x: (-x[1], x[0]))
            out.at[idx, "assigned_lab"] = scored[0][0]

        if "assigned_chain" in out.columns and needs_chain(row.get("assigned_chain")):
            out.at[idx, "assigned_chain"] = "Default Chain"

    return out, warnings


def find_alternative_lab(
    order_row: pd.Series,
    current_lab: str,
    phase_capacity_df: pd.DataFrame,
    product_matrix_df: pd.DataFrame,
) -> str | None:
    """Return the lab id with the most residual capacity excluding `current_lab`."""
    labs = [lab for lab in _candidate_labs(phase_capacity_df) if lab != current_lab]
    if not labs:
        return None
    phases = _phases_for_product(product_matrix_df, order_row.get("product_type"))
    scored = [(lab, _aggregate_capacity(phase_capacity_df, lab, phases)) for lab in labs]
    scored.sort(key=lambda x: (-x[1], x[0]))
    if not scored or scored[0][1] <= 0:
        return None
    return scored[0][0]


__all__ = ["allocate_orders", "find_alternative_lab"]
