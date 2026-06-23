"""Tests for economic input sourcing."""
from __future__ import annotations

import pandas as pd

from src.parsers.economic_inputs import load_economic_inputs


def _econ_sheet() -> pd.DataFrame:
    return pd.DataFrame({
        "order_id": ["ORD-1", "ORD-2"],
        "assigned_lab": ["L1", "L2"],
        "product_type": ["Giacca", "Pantalone"],
        "standard_hourly_cost_eur": [22.0, 18.0],
        "overtime_multiplier": [1.25, 1.30],
        "overhead_pct": [0.15, 0.12],
        "setup_cost_eur": [120.0, 60.0],
        "alternative_lab": ["L3", "L1"],
        "alternative_hourly_cost_eur": [19.0, 22.0],
    })


def test_loads_per_lab_hourly_cost_from_sheet():
    ei = load_economic_inputs({"economic_layer": _econ_sheet()})
    assert ei.hourly_cost("L1") == 22.0
    assert ei.hourly_cost("L2") == 18.0
    # alternative columns extend coverage to L3
    assert ei.hourly_cost("L3") == 19.0
    assert ei.uses_default is False


def test_per_product_overhead_and_per_order_setup():
    ei = load_economic_inputs({"economic_layer": _econ_sheet()})
    assert ei.overhead_pct("Giacca") == 0.15
    assert ei.setup_cost("ORD-1") == 120.0


def test_overtime_multiplier_per_lab():
    ei = load_economic_inputs({"economic_layer": _econ_sheet()})
    assert ei.overtime_multiplier("L2") == 1.30


def test_falls_back_to_config_when_no_sheet():
    ei = load_economic_inputs({})
    assert ei.uses_default is True
    assert ei.hourly_cost("ANY") == 18.0          # config default
    assert ei.overhead_pct("ANY") == 0.10
    assert ei.setup_cost("ANY") == 0.0
    assert ei.overtime_multiplier("ANY") == 1.25
