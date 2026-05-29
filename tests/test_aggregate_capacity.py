"""Integration: orders that individually look fine but together saturate a
shared lab-phase must NOT all be ACCEPTed (the 250%-but-all-ACCEPT bug)."""
from __future__ import annotations

from datetime import date

import pandas as pd

from src.engines.bottleneck_engine import identify_bottlenecks
from src.engines.capacity_engine import (
    aggregate_lab_phase,
    compute_capacity_results,
)
from src.engines.recommendation_engine import generate_recommendations
from src.engines.scenario_engine import ScenarioInputs
from src.engines.stress_engine import evaluate_all_stress
from src.utils.constants import REC_ACCEPT, REC_AT_RISK


def _orders(n: int, lab: str = "L1") -> pd.DataFrame:
    return pd.DataFrame([{
        "order_id": f"O{i}", "client": "C", "product_type": "P",
        "quantity": 40, "start_date": date(2026, 6, 1), "deadline": date(2026, 7, 1),
        "assigned_lab": lab, "assigned_chain": "C1",
        "progress_percentage": 0.0, "priority": "normal",
    } for i in range(n)])


def _pm() -> pd.DataFrame:
    return pd.DataFrame([{
        "product_type": "P", "phase_name": "shared",
        "min_time_minutes": 5.0, "max_time_minutes": 5.0,
        "avg_time_minutes": 5.0, "setup_time_minutes": 0.0, "phase_order": 1,
    }])


def _labs() -> pd.DataFrame:
    return pd.DataFrame([{
        "lab_id": "L1", "lab_name": "L1", "working_hours_per_day": 8.0,
        "working_days_per_week": 5, "default_efficiency": 1.0, "machine_uptime": 1.0,
        "max_weekly_hours": 48.0, "overtime_allowed": False,
    }])


def _pc(available_per_day: float = 300.0) -> pd.DataFrame:
    return pd.DataFrame([{
        "lab_id": "L1", "phase_name": "shared", "workers_total": 1,
        "workers_assigned": 1, "machines_total": 1,
        "available_minutes_per_day": available_per_day, "efficiency": 1.0, "uptime": 1.0,
    }])


def test_shared_overload_blocks_blanket_accept() -> None:
    # 3 orders x (40 x 5) = 200 each -> aggregate 600 vs available 300 -> 200%.
    # Each order ALONE is 200/300 = 67% (< 85% -> would be ACCEPT individually).
    #
    # NOTE: with n=3, the parallel-overload rule (MAX_PARALLEL_ORDERS_PER_LAB=2)
    # ALSO independently blocks ACCEPT, so this test does NOT isolate the aggregate
    # signal — it passes even without lab_phase_df.  The n=2 test below is the one
    # that proves the aggregate signal is load-bearing.
    orders = _orders(3)
    cap = compute_capacity_results(orders, _pm(), _labs(), _pc(300.0), planning_days=1)
    agg = aggregate_lab_phase(cap)
    cap, _ = identify_bottlenecks(cap, agg)
    stress = evaluate_all_stress(
        orders, cap, _labs(), _pc(300.0), ScenarioInputs(),
        today=date(2026, 6, 1), lab_phase_df=agg,
    )
    recs = generate_recommendations(cap, stress, orders, _pc(300.0), _pm())
    assert (recs["recommendation"] != REC_ACCEPT).all()


def test_two_order_shared_overload_requires_aggregate_signal() -> None:
    # 2 orders x (40 x 5) = 200 each. available = 300.
    # Per-order util = 200/300 = 67% (< 85%). Aggregate = 400/300 = 133%.
    # n=2 == MAX_PARALLEL_ORDERS_PER_LAB, so parallel-overload does NOT fire:
    # the ONLY thing that can block ACCEPT here is the aggregate signal.
    orders = _orders(2)
    cap = compute_capacity_results(orders, _pm(), _labs(), _pc(300.0), planning_days=1)
    agg = aggregate_lab_phase(cap)
    cap_b, _ = identify_bottlenecks(cap, agg)

    # Baseline (pre-fix behavior): WITHOUT the aggregate signal, both orders ACCEPT.
    stress_without = evaluate_all_stress(
        orders, cap_b, _labs(), _pc(300.0), ScenarioInputs(), today=date(2026, 6, 1),
    )
    recs_without = generate_recommendations(cap_b, stress_without, orders, _pc(300.0), _pm())
    assert (recs_without["recommendation"] == REC_ACCEPT).all(), (
        "baseline premise broken: orders should be ACCEPT without the aggregate signal"
    )

    # With the aggregate signal: both orders are flagged (not ACCEPT).
    stress_with = evaluate_all_stress(
        orders, cap_b, _labs(), _pc(300.0), ScenarioInputs(), today=date(2026, 6, 1),
        lab_phase_df=agg,
    )
    recs_with = generate_recommendations(cap_b, stress_with, orders, _pc(300.0), _pm())
    assert (recs_with["recommendation"] != REC_ACCEPT).all()
    assert (recs_with["recommendation"] == REC_AT_RISK).all()
