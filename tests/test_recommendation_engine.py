"""Unit tests for `src/engines/recommendation_engine.py` — TASK-037."""
from __future__ import annotations

import math

import pandas as pd
import pytest

from src.engines.recommendation_engine import generate_recommendations
from src.utils.constants import (
    EVENT_DEADLINE_INFEASIBLE,
    EVENT_OVERTIME_REQUIRED,
    EVENT_UTILIZATION_HIGH,
    REC_ACCEPT,
    REC_AT_RISK,
    REC_POSTPONE,
    REC_REALLOCATE,
    REC_REJECT,
    REC_SPLIT,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
)


def _cap_row(order_id: str, util: float, qty: int = 50, phase: str = "ph1", lab: str = "L1") -> dict:
    return {
        "order_id": order_id, "assigned_lab": lab, "product_type": "P", "phase_name": phase,
        "quantity": qty,
        "required_minutes": util * 100.0, "available_minutes": 100.0,
        "utilization_rate": util, "capacity_gap_minutes": 100.0 - util * 100.0,
        "is_overloaded": util > 0.85, "is_bottleneck": False,
    }


def _empty_stress() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "event_id", "order_id", "event_type", "severity",
        "message", "triggered_by", "recommended_action",
    ])


def _orders(order_id: str = "O1", lab: str = "L1") -> pd.DataFrame:
    return pd.DataFrame([{"order_id": order_id, "product_type": "P", "assigned_lab": lab}])


def _pc(labs=("L1",)) -> pd.DataFrame:
    return pd.DataFrame([
        {"lab_id": lab, "phase_name": "ph1", "available_minutes_per_day": 500.0,
         "workers_total": 1, "workers_assigned": 1, "machines_total": 0,
         "efficiency": 1.0, "uptime": 1.0}
        for lab in labs
    ])


def _pm() -> pd.DataFrame:
    return pd.DataFrame([{
        "product_type": "P", "phase_name": "ph1",
        "min_time_minutes": 1.0, "max_time_minutes": 1.0,
        "avg_time_minutes": 1.0, "setup_time_minutes": 0.0, "phase_order": 1,
    }])


def test_accept_when_low_utilization_and_no_stress() -> None:
    cap = pd.DataFrame([_cap_row("O1", util=0.5)])
    recs = generate_recommendations(cap, _empty_stress(), _orders(), _pc(), _pm())
    assert recs.iloc[0]["recommendation"] == REC_ACCEPT
    assert recs.iloc[0]["severity"] == "low"
    assert len(recs.iloc[0]["reasons"]) >= 1


def test_reject_or_split_when_utilization_above_one() -> None:
    cap = pd.DataFrame([_cap_row("O1", util=1.2, qty=50)])
    recs = generate_recommendations(cap, _empty_stress(), _orders(), _pc(), _pm())
    assert recs.iloc[0]["recommendation"] in {REC_REJECT, REC_SPLIT, REC_POSTPONE}
    assert recs.iloc[0]["recommendation"] != REC_ACCEPT


def test_split_when_large_overloaded_order() -> None:
    cap = pd.DataFrame([_cap_row("O1", util=1.2, qty=500)])
    recs = generate_recommendations(cap, _empty_stress(), _orders(), _pc(), _pm())
    assert recs.iloc[0]["recommendation"] == REC_SPLIT


def test_at_risk_between_85_and_100() -> None:
    cap = pd.DataFrame([_cap_row("O1", util=0.92)])
    # Single-lab system → no alternative → AT_RISK
    recs = generate_recommendations(cap, _empty_stress(), _orders(), _pc(labs=("L1",)), _pm())
    assert recs.iloc[0]["recommendation"] == REC_AT_RISK


def test_reallocate_when_alternative_lab_available() -> None:
    cap = pd.DataFrame([_cap_row("O1", util=0.92)])
    recs = generate_recommendations(cap, _empty_stress(), _orders(lab="L1"), _pc(labs=("L1", "L2")), _pm())
    assert recs.iloc[0]["recommendation"] == REC_REALLOCATE
    actions = recs.iloc[0]["suggested_actions"]
    assert any("L2" in a for a in actions)


def test_overtime_event_blocks_accept() -> None:
    cap = pd.DataFrame([_cap_row("O1", util=0.5)])
    stress = pd.DataFrame([{
        "event_id": "STR-1", "order_id": "O1", "event_type": EVENT_OVERTIME_REQUIRED,
        "severity": SEVERITY_HIGH, "message": "Overtime required",
        "triggered_by": "test", "recommended_action": "Consider postpone",
    }])
    recs = generate_recommendations(cap, stress, _orders(), _pc(), _pm())
    assert recs.iloc[0]["recommendation"] != REC_ACCEPT
    assert recs.iloc[0]["recommendation"] == REC_REJECT


def test_deadline_infeasible_produces_postpone() -> None:
    cap = pd.DataFrame([_cap_row("O1", util=0.5)])
    stress = pd.DataFrame([{
        "event_id": "STR-1", "order_id": "O1", "event_type": EVENT_DEADLINE_INFEASIBLE,
        "severity": SEVERITY_HIGH, "message": "Deadline too close",
        "triggered_by": "test", "recommended_action": "Postpone",
    }])
    recs = generate_recommendations(cap, stress, _orders(), _pc(), _pm())
    assert recs.iloc[0]["recommendation"] == REC_POSTPONE


def test_reasons_list_never_empty() -> None:
    cap = pd.DataFrame([_cap_row("O1", util=0.4)])
    recs = generate_recommendations(cap, _empty_stress(), _orders(), _pc(), _pm())
    assert len(recs.iloc[0]["reasons"]) > 0


def test_suggested_actions_list_never_empty() -> None:
    cap = pd.DataFrame([_cap_row("O1", util=0.4)])
    recs = generate_recommendations(cap, _empty_stress(), _orders(), _pc(), _pm())
    assert len(recs.iloc[0]["suggested_actions"]) > 0


def test_medium_severity_alone_triggers_at_risk_or_reallocate() -> None:
    cap = pd.DataFrame([_cap_row("O1", util=0.5)])
    stress = pd.DataFrame([{
        "event_id": "STR-1", "order_id": "O1", "event_type": EVENT_UTILIZATION_HIGH,
        "severity": SEVERITY_MEDIUM, "message": "High utilization",
        "triggered_by": "test", "recommended_action": "Split",
    }])
    recs = generate_recommendations(cap, stress, _orders(), _pc(labs=("L1", "L2")), _pm())
    assert recs.iloc[0]["recommendation"] in {REC_AT_RISK, REC_REALLOCATE}


def test_order_utilization_uses_worst_phase_not_mean() -> None:
    # Two phases: one at 30%, one at 120%. Mean = 75% (would be ACCEPT);
    # max = 120% -> must NOT be ACCEPT.
    cap = pd.DataFrame([
        _cap_row("O1", util=0.3, phase="ph1"),
        _cap_row("O1", util=1.2, phase="ph2"),
    ])
    recs = generate_recommendations(cap, _empty_stress(), _orders(), _pc(), _pm())
    assert recs.iloc[0]["recommendation"] != REC_ACCEPT
