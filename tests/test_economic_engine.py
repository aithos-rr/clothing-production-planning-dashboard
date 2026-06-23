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
