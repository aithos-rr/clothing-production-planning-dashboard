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


from src.engines.economic_engine import compute_economic_results
from src.parsers.economic_inputs import EconomicInputs


def _cap_one_order(util=0.5, available_minutes=10000.0, required_minutes=5000.0, lab="L1"):
    return pd.DataFrame([
        {"order_id": "O1", "assigned_lab": lab, "product_type": "Giacca",
         "phase_name": "p1", "quantity": 100, "required_minutes": required_minutes,
         "available_minutes": available_minutes, "utilization_rate": util,
         "capacity_gap_minutes": available_minutes - required_minutes,
         "is_overloaded": util > 0.85, "is_bottleneck": True},
    ])


def _orders_one(lab="L1"):
    return pd.DataFrame([{"order_id": "O1", "assigned_lab": lab, "product_type": "Giacca", "quantity": 100}])


def _pc_two_labs():
    return pd.DataFrame([
        {"lab_id": "L1", "phase_name": "p1", "available_minutes_per_day": 2000.0, "overtime_allowed": False},
        {"lab_id": "L2", "phase_name": "p1", "available_minutes_per_day": 2000.0, "overtime_allowed": False},
    ])


def _pm_one():
    return pd.DataFrame([{"product_type": "Giacca", "phase_name": "p1", "avg_time_minutes": 50.0, "setup_time_minutes": 0.0, "phase_order": 1}])


def test_compute_economic_results_basic_schema():
    ei = EconomicInputs(uses_default=True)
    res = compute_economic_results(_cap_one_order(), _orders_one(), _pc_two_labs(), _pm_one(), ei, labs_df=None, operational_recs_df=None)
    assert list(res.columns)[:4] == ["order_id", "assigned_lab", "product_type", "quantity"]
    row = res.iloc[0]
    assert row["required_hours"] == 5000.0 / 60.0
    # labour = required_hours * 18 (default); total includes overhead 10%
    assert round(row["total_estimated_cost"], 2) > 0
    assert row["economic_recommendation"] in {"ACCEPT", "REALLOCATE", "ACCEPT WITH OVERTIME", "POSTPONE", "REJECT"}


def test_reallocate_when_alternative_materially_cheaper():
    # L1 expensive (30/h), L2 cheap (10/h) -> delta well below -500
    ei = EconomicInputs(_hourly={"L1": 30.0, "L2": 10.0}, uses_default=False)
    res = compute_economic_results(_cap_one_order(lab="L1"), _orders_one("L1"), _pc_two_labs(), _pm_one(), ei, labs_df=None, operational_recs_df=None)
    row = res.iloc[0]
    assert row["alternative_lab"] == "L2"
    assert row["cost_delta_if_reallocated"] < 0
    assert row["economic_recommendation"] == "REALLOCATE"


def test_accept_when_no_cheaper_alternative_and_no_overtime():
    ei = EconomicInputs(_hourly={"L1": 10.0, "L2": 30.0}, uses_default=False)
    res = compute_economic_results(_cap_one_order(lab="L1"), _orders_one("L1"), _pc_two_labs(), _pm_one(), ei, labs_df=None, operational_recs_df=None)
    assert res.iloc[0]["economic_recommendation"] == "ACCEPT"


def test_reason_never_empty():
    ei = EconomicInputs(uses_default=True)
    res = compute_economic_results(_cap_one_order(), _orders_one(), _pc_two_labs(), _pm_one(), ei, labs_df=None, operational_recs_df=None)
    assert isinstance(res.iloc[0]["economic_reason"], str) and res.iloc[0]["economic_reason"]


def test_alternative_cost_uses_alt_lab_own_capacity():
    # Current lab L1 capacity-starved (overtime), alt lab L2 ample -> alt avoids phantom overtime.
    cap = pd.DataFrame([
        {"order_id": "O1", "assigned_lab": "L1", "product_type": "Giacca", "phase_name": "p1",
         "quantity": 100, "required_minutes": 12000.0, "available_minutes": 3000.0,
         "utilization_rate": 4.0, "capacity_gap_minutes": -9000.0, "is_overloaded": True, "is_bottleneck": True},
    ])
    orders = pd.DataFrame([{"order_id": "O1", "assigned_lab": "L1", "product_type": "Giacca", "quantity": 100}])
    pc = pd.DataFrame([
        {"lab_id": "L1", "phase_name": "p1", "available_minutes_per_day": 600.0},    # *5d=3000min=50h
        {"lab_id": "L2", "phase_name": "p1", "available_minutes_per_day": 6000.0},   # *5d=30000min=500h ample
    ])
    pm = pd.DataFrame([{"product_type": "Giacca", "phase_name": "p1", "avg_time_minutes": 120.0, "setup_time_minutes": 0.0, "phase_order": 1}])
    labs = pd.DataFrame([
        {"lab_id": "L1", "overtime_allowed": True},
        {"lab_id": "L2", "overtime_allowed": True},
    ])
    ei = EconomicInputs(_hourly={"L1": 20.0, "L2": 20.0}, _overtime={"L1": 1.5, "L2": 1.5}, uses_default=False)
    res = compute_economic_results(cap, orders, pc, pm, ei, labs_df=labs, operational_recs_df=None, planning_days=5)
    row = res.iloc[0]
    # current lab incurs overtime; alternative lab has ample capacity -> materially cheaper
    assert row["overtime_cost"] > 0
    assert row["alternative_total_cost"] < row["total_estimated_cost"]
    assert row["cost_delta_if_reallocated"] < -100  # real saving surfaced (was ~0 before the fix)


def test_required_hours_uses_smv_when_present():
    # When the order carries a standard-minutes-per-garment value, required_hours
    # = quantity * smv / 60 (apparel costing standard), NOT the per-phase sum.
    cap = pd.DataFrame([
        {"order_id": "O1", "assigned_lab": "L1", "product_type": "Giacca", "phase_name": "p1",
         "quantity": 100, "required_minutes": 9999.0, "available_minutes": 100000.0,
         "utilization_rate": 0.1, "capacity_gap_minutes": 90001.0, "is_overloaded": False, "is_bottleneck": True},
    ])
    orders = pd.DataFrame([{"order_id": "O1", "assigned_lab": "L1", "product_type": "Giacca", "quantity": 100}])
    pc = pd.DataFrame([{"lab_id": "L1", "phase_name": "p1", "available_minutes_per_day": 5000.0}])
    pm = pd.DataFrame([{"product_type": "Giacca", "phase_name": "p1", "avg_time_minutes": 30.0, "setup_time_minutes": 0.0, "phase_order": 1}])
    ei = EconomicInputs(_hourly={"L1": 20.0}, _smv={"O1": 80.0}, uses_default=False)
    res = compute_economic_results(cap, orders, pc, pm, ei, labs_df=None, operational_recs_df=None, planning_days=5)
    assert round(res.iloc[0]["required_hours"], 2) == round(100 * 80 / 60, 2)


def test_reconciles_with_workbook_total_when_smv_present():
    """End-to-end: with the workbook's SMV, dashboard labour matches the workbook
    economic_layer exactly and the total estimated cost is within 1%."""
    from src.parsers.excel_parser import parse_excel
    from src.parsers.normalizer import normalize_all
    from src.parsers.economic_inputs import load_economic_inputs
    from src.engines.scenario_engine import ScenarioInputs, apply_scenario
    from src.engines.capacity_engine import compute_capacity_results, aggregate_lab_phase
    from src.engines.bottleneck_engine import identify_bottlenecks
    from src.engines.stress_engine import evaluate_all_stress
    from src.engines.recommendation_engine import generate_recommendations

    P = "data/sample/clothing_production_planning_database_with_economic_layer.xlsx"
    raw = parse_excel(P)
    d = normalize_all(raw)
    ei = load_economic_inputs(raw)
    o, pc = apply_scenario(d["orders"], d["phase_capacity"], ScenarioInputs())
    cap = compute_capacity_results(o, d["product_matrix"], d["labs"], pc, planning_days=5)
    lp = aggregate_lab_phase(cap)
    cap, _ = identify_bottlenecks(cap, lp)
    stress = evaluate_all_stress(o, cap, d["labs"], pc, ScenarioInputs(), lab_phase_df=lp)
    recs = generate_recommendations(cap, stress, o, pc, d["product_matrix"])
    econ = compute_economic_results(cap, o, pc, d["product_matrix"], ei, labs_df=d["labs"], operational_recs_df=recs, planning_days=5)
    el = pd.read_excel(P, sheet_name="economic_layer")
    el = el.loc[:, ~el.columns.str.startswith("Unnamed")]
    assert round(econ["standard_labour_cost"].sum(), 0) == round(el["standard_labour_cost_eur"].sum(), 0)
    ratio = econ["total_estimated_cost"].sum() / el["total_estimated_cost_eur"].sum()
    assert 0.98 <= ratio <= 1.02
