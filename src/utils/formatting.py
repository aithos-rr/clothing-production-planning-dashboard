"""Display formatting helpers used by the UI layer.

Keeps Streamlit pages free of inline formatting logic.
"""
from __future__ import annotations

import math

from src.utils.constants import (
    CRITICAL_UTILIZATION_THRESHOLD,
    SAFE_UTILIZATION_THRESHOLD,
    STATUS_AT_RISK,
    STATUS_COLORS,
    STATUS_CRITICAL,
    STATUS_NEUTRAL,
    STATUS_SAFE,
)


def fmt_pct(value: float, decimals: int = 1) -> str:
    """Format a fraction as `'85.0%'`. NaN/inf rendered as `'—'`."""
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        return "—"
    return f"{value * 100:.{decimals}f}%"


def fmt_minutes(minutes: float) -> str:
    """Format minutes as `'2h 30m'` or `'45m'`. Negative values rendered with leading minus."""
    if minutes is None or (isinstance(minutes, float) and (math.isnan(minutes) or math.isinf(minutes))):
        return "—"
    total = int(round(minutes))
    sign = "-" if total < 0 else ""
    total = abs(total)
    hours, rest = divmod(total, 60)
    if hours == 0:
        return f"{sign}{rest}m"
    return f"{sign}{hours}h {rest}m"


def fmt_int(value: float) -> str:
    """Format an integer with thousand separators."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    return f"{int(round(value)):,}"


def status_color(status: str) -> str:
    """Return the hex color for a status label; falls back to neutral."""
    return STATUS_COLORS.get(status, STATUS_COLORS[STATUS_NEUTRAL])


def utilization_status(utilization: float) -> str:
    """Map a utilization fraction to one of safe / at_risk / critical."""
    if utilization is None or (isinstance(utilization, float) and math.isnan(utilization)):
        return STATUS_NEUTRAL
    if utilization >= CRITICAL_UTILIZATION_THRESHOLD:
        return STATUS_CRITICAL
    if utilization >= SAFE_UTILIZATION_THRESHOLD:
        return STATUS_AT_RISK
    return STATUS_SAFE


__all__ = ["fmt_pct", "fmt_minutes", "fmt_int", "status_color", "utilization_status"]
