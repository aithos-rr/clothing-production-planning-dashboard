"""Generic DataFrame validation helpers.

Each helper returns a list of `ValidationWarning` rather than raising — the
caller (normalizer / UI) decides how to surface them.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd

from src.utils.constants import SEVERITY_HIGH, SEVERITY_LOW, SEVERITY_MEDIUM


@dataclass(frozen=True)
class ValidationWarning:
    field: str
    message: str
    severity: str  # one of SEVERITY_LOW | SEVERITY_MEDIUM | SEVERITY_HIGH


def check_required_columns(
    df: pd.DataFrame,
    required: Iterable[str],
    context: str,
) -> list[ValidationWarning]:
    """Emit one high-severity warning per missing required column."""
    cols = set(df.columns)
    return [
        ValidationWarning(
            field=col,
            message=f"Required column '{col}' missing in {context}.",
            severity=SEVERITY_HIGH,
        )
        for col in required
        if col not in cols
    ]


def check_no_nulls(
    df: pd.DataFrame,
    columns: Iterable[str],
    context: str,
    severity: str = SEVERITY_MEDIUM,
) -> list[ValidationWarning]:
    """Emit one warning per column that contains nulls."""
    warnings: list[ValidationWarning] = []
    for col in columns:
        if col not in df.columns:
            continue
        null_count = int(df[col].isna().sum())
        if null_count:
            warnings.append(
                ValidationWarning(
                    field=col,
                    message=f"Column '{col}' has {null_count} null value(s) in {context}.",
                    severity=severity,
                )
            )
    return warnings


def check_positive(
    df: pd.DataFrame,
    columns: Iterable[str],
    context: str,
) -> list[ValidationWarning]:
    """Emit a warning when a numeric column contains values <= 0."""
    warnings: list[ValidationWarning] = []
    for col in columns:
        if col not in df.columns:
            continue
        # Coerce to numeric; non-numeric counts separately
        numeric = pd.to_numeric(df[col], errors="coerce")
        non_positive = int((numeric <= 0).sum())
        if non_positive:
            warnings.append(
                ValidationWarning(
                    field=col,
                    message=f"Column '{col}' has {non_positive} value(s) <= 0 in {context}.",
                    severity=SEVERITY_HIGH,
                )
            )
    return warnings


def check_date_valid(
    df: pd.DataFrame,
    columns: Iterable[str],
    context: str,
) -> list[ValidationWarning]:
    """Emit a warning when a date column has unparseable values."""
    warnings: list[ValidationWarning] = []
    for col in columns:
        if col not in df.columns:
            continue
        parsed = pd.to_datetime(df[col], errors="coerce")
        invalid = int(parsed.isna().sum()) - int(df[col].isna().sum())
        if invalid > 0:
            warnings.append(
                ValidationWarning(
                    field=col,
                    message=f"Column '{col}' has {invalid} unparseable date value(s) in {context}.",
                    severity=SEVERITY_MEDIUM,
                )
            )
    return warnings


__all__ = [
    "ValidationWarning",
    "check_required_columns",
    "check_no_nulls",
    "check_positive",
    "check_date_valid",
    "SEVERITY_LOW",
    "SEVERITY_MEDIUM",
    "SEVERITY_HIGH",
]
