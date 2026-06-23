"""Tests for the economic engine (PRD v2 economic layer)."""
from __future__ import annotations

import math

import pandas as pd

from src.utils.config import get_default
from src.utils import constants as C


def test_economic_config_defaults_present():
    assert float(get_default("standard_hourly_cost")) == 18.0
    assert float(get_default("overtime_multiplier")) == 1.25
    assert float(get_default("fixed_setup_cost")) == 0.0
    assert float(get_default("overhead_percentage")) == 0.10
    assert float(get_default("reallocation_material_threshold_eur")) == 500.0


def test_econ_recommendation_labels_exist():
    assert C.ECON_ACCEPT == "ACCEPT"
    assert C.ECON_REALLOCATE == "REALLOCATE"
    assert len(C.ALL_ECON_RECOMMENDATIONS) == 5


from src.engines.economic_engine import (
    standard_labour_cost,
    excess_hours,
    overtime_cost,
    overhead_cost,
    total_estimated_cost,
)


def test_standard_labour_cost():
    assert standard_labour_cost(118.5, 17.8) == 118.5 * 17.8  # 2109.30


def test_excess_hours_clamped_at_zero():
    assert excess_hours(100.0, 120.0) == 0.0
    assert excess_hours(120.0, 100.0) == 20.0


def test_overtime_cost():
    assert overtime_cost(10.0, 18.0, 1.25) == 10.0 * 18.0 * 1.25  # 225.0


def test_overhead_cost():
    # (labour + overtime + setup) * pct
    assert round(overhead_cost(2109.3, 0.0, 180.0, 0.15), 6) == round(343.395, 6)


def test_total_estimated_cost():
    assert round(total_estimated_cost(2109.3, 0.0, 180.0, 343.395), 6) == round(2632.695, 6)


def test_golden_reproduces_workbook_to_the_cent():
    """Feed the workbook's own required_hours + params into the pure formulas;
    assert total_estimated_cost matches economic_layer for all overtime-free rows."""
    import pandas as pd
    path = "data/sample/clothing_production_planning_database_with_economic_layer.xlsx"
    el = pd.read_excel(path, sheet_name="economic_layer")
    el = el.loc[:, ~el.columns.str.startswith("Unnamed")]
    checked = 0
    for _, r in el.iterrows():
        labour = standard_labour_cost(float(r["required_hours"]), float(r["standard_hourly_cost_eur"]))
        oh = overhead_cost(labour, float(r["overtime_cost_eur"]), float(r["setup_cost_eur"]), float(r["overhead_pct"]))
        total = total_estimated_cost(labour, float(r["overtime_cost_eur"]), float(r["setup_cost_eur"]), oh)
        assert round(total, 2) == round(float(r["total_estimated_cost_eur"]), 2)
        assert round(labour, 2) == round(float(r["standard_labour_cost_eur"]), 2)
        assert round(oh, 2) == round(float(r["overhead_cost_eur"]), 2)
        checked += 1
    assert checked == 60
