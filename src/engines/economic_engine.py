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
    ECON_ACCEPT,
    ECON_ACCEPT_OVERTIME,
    ECON_POSTPONE,
    ECON_REALLOCATE,
    ECON_REJECT,
    EVENT_DEADLINE_INFEASIBLE,
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


__all__ = [
    "standard_labour_cost",
    "excess_hours",
    "overtime_cost",
    "overhead_cost",
    "total_estimated_cost",
    "compute_economic_results",
    "ECONOMIC_RESULTS_COLS",
]
