"""Product Matrix Engine — PRD §9.3.

Given the canonical `product_matrix_df`, return the ordered list of phases
required for a given product type with their average + setup timing.
"""
from __future__ import annotations

import pandas as pd


class UnknownProductError(KeyError):
    """Raised when a product is not present in the product matrix."""


def list_product_types(product_matrix_df: pd.DataFrame) -> list[str]:
    """Return the unique product types present in the matrix, sorted."""
    if product_matrix_df.empty or "product_type" not in product_matrix_df.columns:
        return []
    return sorted(product_matrix_df["product_type"].dropna().unique().tolist())


def get_phases_for_product(
    product_matrix_df: pd.DataFrame,
    product_type: str,
) -> pd.DataFrame:
    """Return the phases for `product_type` sorted by `phase_order`.

    Columns: phase_name, avg_time_minutes, setup_time_minutes, phase_order.
    Raises `UnknownProductError` if the product is not present.
    """
    if product_matrix_df.empty or "product_type" not in product_matrix_df.columns:
        raise UnknownProductError(f"Product matrix is empty; cannot resolve '{product_type}'.")
    subset = product_matrix_df[product_matrix_df["product_type"] == product_type]
    if subset.empty:
        raise UnknownProductError(f"Product type '{product_type}' not found in product matrix.")
    out = subset.sort_values("phase_order").reset_index(drop=True)
    return out[["phase_name", "avg_time_minutes", "setup_time_minutes", "phase_order"]]


__all__ = ["get_phases_for_product", "list_product_types", "UnknownProductError"]
