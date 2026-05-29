# Capacity Aggregation Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the capacity KPIs and downstream decisions so utilization, gap, and recommendations are computed by aggregating first per `(assigned_lab, phase_name)` (capacity counted once) instead of summing/averaging inflated per-(order,phase) rows.

**Architecture:** Introduce a second level of truth — a per `(assigned_lab, phase_name)` aggregate — alongside the existing per-(order,phase) `capacity_results`. The aggregate drives all on-screen KPIs, the most-critical-phase summary, the utilization chart, and a new aggregate-overload stress signal that feeds recommendations. The per-(order,phase) table is kept for "does this order alone saturate a phase?" (SPLIT/REJECT) decisions.

**Tech Stack:** Python 3.10+, pandas, plotly, streamlit, pytest.

**Reference spec:** `docs/superpowers/specs/2026-05-29-capacity-aggregation-fix-design.md`

---

## File structure

| File | Responsibility | Change |
|---|---|---|
| `src/engines/capacity_engine.py` | per-(order,phase) results + NEW aggregate | Add `assigned_lab` col; add `aggregate_lab_phase`, `overall_utilization`, `LAB_PHASE_LOAD_COLS` |
| `src/engines/bottleneck_engine.py` | per-order ranks + global summary | `most_critical_phase` from aggregate |
| `src/engines/stress_engine.py` | stress events | NEW `evaluate_aggregate_phase_stress`; `evaluate_all_stress` gains `lab_phase_df` |
| `src/engines/recommendation_engine.py` | per-order decision | `_order_utilization` mean→max; reason text |
| `src/engines/timeline_engine.py` | per-order timeline | docstring note only |
| `src/components/charts.py` | plotly charts | `phase_utilization_bar` takes lab-phase; replace `order_capacity_gap_bar` with `lab_phase_capacity_gap_bar` |
| `src/ui/pages/capacity_dashboard.py` | KPIs + charts | rewrite KPIs from aggregate |
| `src/ui/pages/overview.py` | headline KPIs | overall util from aggregate |
| `src/ui/pages/scenario_testing.py` | baseline vs current | overall util + overloaded from aggregate |
| `src/ui/pages/phase_saturation.py` | per-phase detail | per-phase table from aggregate |
| `tests/test_capacity_engine.py` | engine tests | add aggregate + overall_util tests |
| `tests/test_aggregate_capacity.py` | NEW integration test | "3 orders saturate a phase → none ACCEPT" |
| `tests/test_recommendation_engine.py` | rec tests | add `assigned_lab` to fixtures |
| `docs/PRESENTATION_AUDIT.md`, `README.md`, `docs/TASKS.md` | docs | two-level model |

**Key fact:** `order_capacity_gap_bar` is currently dead code (defined/exported, never called) — safe to replace.

---

### Task 1: capacity_engine — `assigned_lab` column + aggregate + overall utilization

**Files:**
- Modify: `src/engines/capacity_engine.py`
- Test: `tests/test_capacity_engine.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_capacity_engine.py`:

```python
from src.engines.capacity_engine import (
    aggregate_lab_phase,
    overall_utilization,
)


def _orders_multi(qty: int, order_id: str, lab: str = "L1") -> pd.DataFrame:
    df = _orders(qty=qty, lab=lab)
    df["order_id"] = order_id
    return df


def test_capacity_results_includes_assigned_lab() -> None:
    cap = compute_capacity_results(
        _orders(qty=10, lab="L1"), _product_matrix(avg=5.0), _labs(),
        _phase_capacity(available_per_day=1000.0, lab="L1"), planning_days=1,
    )
    assert "assigned_lab" in cap.columns
    assert cap.iloc[0]["assigned_lab"] == "L1"


def test_aggregate_counts_capacity_once_across_orders() -> None:
    # Two orders, same lab+phase. available_per_day=300, planning_days=1.
    # Each order required = 120 (qty=24, avg=5). Aggregate required = 240,
    # available counted ONCE = 300 → gap = +60 (NOT 300*2 - 240 = 360).
    orders = pd.concat([
        _orders_multi(qty=24, order_id="O1"),
        _orders_multi(qty=24, order_id="O2"),
    ], ignore_index=True)
    cap = compute_capacity_results(
        orders, _product_matrix(avg=5.0), _labs(),
        _phase_capacity(available_per_day=300.0, lab="L1"), planning_days=1,
    )
    agg = aggregate_lab_phase(cap)
    assert len(agg) == 1
    row = agg.iloc[0]
    assert row["total_required_minutes"] == pytest.approx(240.0)
    assert row["available_minutes"] == pytest.approx(300.0)
    assert row["capacity_gap_minutes"] == pytest.approx(60.0)
    assert row["utilization_rate"] == pytest.approx(240.0 / 300.0)
    assert int(row["num_orders"]) == 2


def test_aggregate_detects_shared_overload() -> None:
    # 3 orders each individually under threshold but together overloaded.
    orders = pd.concat([
        _orders_multi(qty=24, order_id=f"O{i}") for i in range(3)
    ], ignore_index=True)
    cap = compute_capacity_results(
        orders, _product_matrix(avg=5.0), _labs(),
        _phase_capacity(available_per_day=300.0, lab="L1"), planning_days=1,
    )
    agg = aggregate_lab_phase(cap)
    # required = 3 × 120 = 360 > 300 → util = 1.2 → overloaded
    assert agg.iloc[0]["utilization_rate"] == pytest.approx(1.2)
    assert bool(agg.iloc[0]["is_overloaded"]) is True


def test_overall_utilization_is_weighted_not_mean() -> None:
    # lab-phase A: required 360 / available 300 ; that's the only group
    orders = pd.concat([
        _orders_multi(qty=24, order_id=f"O{i}") for i in range(3)
    ], ignore_index=True)
    cap = compute_capacity_results(
        orders, _product_matrix(avg=5.0), _labs(),
        _phase_capacity(available_per_day=300.0, lab="L1"), planning_days=1,
    )
    agg = aggregate_lab_phase(cap)
    assert overall_utilization(agg) == pytest.approx(360.0 / 300.0)


def test_aggregate_empty_returns_empty() -> None:
    agg = aggregate_lab_phase(pd.DataFrame(columns=["assigned_lab", "phase_name"]))
    assert agg.empty
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_capacity_engine.py -k "aggregate or assigned_lab or overall_utilization" -v`
Expected: FAIL — `ImportError: cannot import name 'aggregate_lab_phase'` / missing `assigned_lab`.

- [ ] **Step 3: Add `assigned_lab` to the per-row schema and output**

In `src/engines/capacity_engine.py`, update `CAPACITY_RESULTS_COLS`:

```python
CAPACITY_RESULTS_COLS = [
    "order_id", "assigned_lab", "product_type", "phase_name", "quantity",
    "required_minutes", "available_minutes", "utilization_rate",
    "capacity_gap_minutes", "is_overloaded", "is_bottleneck",
]
```

In the unknown-product branch, add `"assigned_lab"` to the appended dict (lab is computed below it today — move `lab_id` resolution above the `try`):

```python
    for _, order in orders_df.iterrows():
        product_type = order.get("product_type")
        quantity = int(order.get("quantity", 0) or 0)
        lab_id = order.get("assigned_lab") or "Default Lab"
        try:
            phases = get_phases_for_product(product_matrix_df, product_type)
        except UnknownProductError:
            rows.append({
                "order_id": order["order_id"],
                "assigned_lab": lab_id,
                "product_type": product_type,
                "phase_name": "<unknown product>",
                "quantity": quantity,
                "required_minutes": 0.0,
                "available_minutes": 0.0,
                "utilization_rate": math.inf,
                "capacity_gap_minutes": 0.0,
                "is_overloaded": True,
                "is_bottleneck": False,
            })
            continue
```

Then delete the now-duplicate `quantity = ...` and `lab_id = ...` lines that previously sat after the `try` block, and add `"assigned_lab": lab_id,` to the main per-phase appended dict (right after `"order_id"`).

- [ ] **Step 4: Add the aggregate + overall-utilization functions**

Append to `src/engines/capacity_engine.py` (before `__all__`):

```python
LAB_PHASE_LOAD_COLS = [
    "assigned_lab", "phase_name", "total_required_minutes",
    "available_minutes", "utilization_rate", "capacity_gap_minutes",
    "is_overloaded", "num_orders",
]


def aggregate_lab_phase(capacity_results_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-(order,phase) rows into per-(lab,phase) capacity truth.

    Capacity is counted ONCE per (assigned_lab, phase_name) — `available_minutes`
    is identical across the orders that share a lab-phase, so we take its max.
    Required minutes are summed across all those orders.
    """
    if capacity_results_df.empty:
        return pd.DataFrame(columns=LAB_PHASE_LOAD_COLS)

    rows: list[dict] = []
    for (lab, phase), g in capacity_results_df.groupby(["assigned_lab", "phase_name"]):
        total_required = float(g["required_minutes"].sum())
        available = float(g["available_minutes"].max())
        if available <= 0:
            utilization = math.inf if total_required > 0 else 0.0
        else:
            utilization = total_required / available
        rows.append({
            "assigned_lab": lab,
            "phase_name": phase,
            "total_required_minutes": total_required,
            "available_minutes": available,
            "utilization_rate": float(utilization),
            "capacity_gap_minutes": float(available - total_required),
            "is_overloaded": bool(utilization > SAFE_UTILIZATION_THRESHOLD),
            "num_orders": int(g["order_id"].nunique()),
        })
    return pd.DataFrame(rows, columns=LAB_PHASE_LOAD_COLS)


def overall_utilization(lab_phase_df: pd.DataFrame) -> float:
    """System-wide utilization = Σ total_required / Σ available (capacity once).

    Returns inf if there is required work but zero available capacity, 0.0 if no
    work at all.
    """
    if lab_phase_df.empty:
        return 0.0
    total_required = float(lab_phase_df["total_required_minutes"].sum())
    total_available = float(lab_phase_df["available_minutes"].sum())
    if total_available <= 0:
        return math.inf if total_required > 0 else 0.0
    return total_required / total_available
```

Update `__all__`:

```python
__all__ = [
    "compute_capacity_results",
    "CAPACITY_RESULTS_COLS",
    "aggregate_lab_phase",
    "overall_utilization",
    "LAB_PHASE_LOAD_COLS",
]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_capacity_engine.py -v`
Expected: PASS (all, including the pre-existing tests — note `assigned_lab` is now present but old assertions are positional/by-name so they still hold).

- [ ] **Step 6: Commit**

```bash
git add src/engines/capacity_engine.py tests/test_capacity_engine.py
git commit -m "feat(capacity): aggregate lab-phase truth + weighted overall utilization

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: bottleneck_engine — most-critical phase from aggregate

**Files:**
- Modify: `src/engines/bottleneck_engine.py`
- Test: `tests/test_capacity_engine.py` (engine has no dedicated test file; co-locate)

- [ ] **Step 1: Write failing test**

Append to `tests/test_capacity_engine.py`:

```python
from src.engines.bottleneck_engine import identify_bottlenecks


def test_most_critical_phase_uses_aggregate_not_single_order() -> None:
    # phase "low" has ONE order at 150% (worst-case-per-order would pick it).
    # phase "shared" has THREE orders each 40% but aggregate 120%.
    # Aggregate logic must pick "shared" (the real bottleneck), not "low".
    def row(order_id, phase, required, available):
        return {
            "order_id": order_id, "assigned_lab": "L1", "product_type": "P",
            "phase_name": phase, "quantity": 10,
            "required_minutes": required, "available_minutes": available,
            "utilization_rate": (required / available) if available else float("inf"),
            "capacity_gap_minutes": available - required,
            "is_overloaded": (required / available) > 0.85 if available else True,
            "is_bottleneck": False,
        }
    cap = pd.DataFrame([
        row("A", "low", 150, 100),       # single order 150%
        row("B", "shared", 40, 100),
        row("C", "shared", 40, 100),
        row("D", "shared", 40, 100),     # aggregate shared = 120/100 = 120%
    ])
    agg = aggregate_lab_phase(cap)
    _, summary = identify_bottlenecks(cap, agg)
    assert summary["most_critical_phase"] == "shared"
    assert summary["most_critical_phase_utilization"] == pytest.approx(1.2)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_capacity_engine.py::test_most_critical_phase_uses_aggregate_not_single_order -v`
Expected: FAIL — `identify_bottlenecks() takes 1 positional argument but 2 were given`.

- [ ] **Step 3: Add the optional `lab_phase_df` param**

In `src/engines/bottleneck_engine.py`, change the signature and global-summary block:

```python
def identify_bottlenecks(
    capacity_results_df: pd.DataFrame,
    lab_phase_df: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, dict]:
```

Keep the per-order rank block unchanged. Replace the global-summary block (the part starting at `# Global summary:`) with:

```python
    # Global summary: the phase whose AGGREGATE (lab,phase) load is highest.
    # Aggregate is the real bottleneck; a single critical order no longer hijacks
    # the headline. Falls back to per-order worst case if no aggregate is given.
    most_phase: str
    most_util: float
    if lab_phase_df is not None and not lab_phase_df.empty:
        agg_util = lab_phase_df["utilization_rate"].replace(
            [math.inf, -math.inf], float("nan")
        )
        agg = lab_phase_df.assign(_u=agg_util).dropna(subset=["_u"])
        if not agg.empty:
            idx = agg["_u"].idxmax()
            most_phase = str(agg.loc[idx, "phase_name"])
            most_util = float(agg.loc[idx, "_u"])
        else:
            most_phase = str(lab_phase_df["phase_name"].iloc[0])
            most_util = float(lab_phase_df["utilization_rate"].iloc[0])
    else:
        util = df["utilization_rate"].replace([math.inf, -math.inf], float("nan"))
        finite_df = df.assign(_finite_util=util).dropna(subset=["_finite_util"])
        if finite_df.empty:
            most_phase = df["phase_name"].iloc[0]
            most_util = float(df["utilization_rate"].iloc[0])
        else:
            per_phase = finite_df.groupby("phase_name")["_finite_util"].max()
            most_phase = str(per_phase.idxmax())
            most_util = float(per_phase.max())
```

(The `summary = {...}` and `df["bottleneck_phase_global"] = most_phase` lines below stay unchanged.)

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_capacity_engine.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/engines/bottleneck_engine.py tests/test_capacity_engine.py
git commit -m "feat(bottleneck): most-critical phase from aggregate lab-phase load

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: stress_engine — aggregate phase-overload events

**Files:**
- Modify: `src/engines/stress_engine.py`
- Test: `tests/test_stress_engine.py` (NEW)

- [ ] **Step 1: Write failing test**

Create `tests/test_stress_engine.py`:

```python
"""Unit tests for aggregate phase-overload stress events."""
from __future__ import annotations

import pandas as pd

from src.engines.stress_engine import evaluate_aggregate_phase_stress
from src.utils.constants import EVENT_PHASE_OVERLOAD


def _cap(order_id: str, lab: str, phase: str, required: float, available: float) -> dict:
    util = (required / available) if available else float("inf")
    return {
        "order_id": order_id, "assigned_lab": lab, "product_type": "P",
        "phase_name": phase, "quantity": 10,
        "required_minutes": required, "available_minutes": available,
        "utilization_rate": util, "capacity_gap_minutes": available - required,
        "is_overloaded": util > 0.85, "is_bottleneck": False,
    }


def test_aggregate_overload_emits_event_per_participating_order() -> None:
    from src.engines.capacity_engine import aggregate_lab_phase
    cap = pd.DataFrame([
        _cap("O1", "L1", "shared", 40, 100),
        _cap("O2", "L1", "shared", 40, 100),
        _cap("O3", "L1", "shared", 40, 100),  # aggregate 120% on L1/shared
    ])
    agg = aggregate_lab_phase(cap)
    events = evaluate_aggregate_phase_stress(cap, agg)
    assert not events.empty
    assert set(events["event_type"]) == {EVENT_PHASE_OVERLOAD}
    # one event per participating order
    assert set(events["order_id"]) == {"O1", "O2", "O3"}


def test_no_aggregate_event_when_phase_healthy() -> None:
    from src.engines.capacity_engine import aggregate_lab_phase
    cap = pd.DataFrame([_cap("O1", "L1", "ph", 10, 100)])  # 10%
    agg = aggregate_lab_phase(cap)
    events = evaluate_aggregate_phase_stress(cap, agg)
    assert events.empty
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_stress_engine.py -v`
Expected: FAIL — `cannot import name 'evaluate_aggregate_phase_stress'`.

- [ ] **Step 3: Implement `evaluate_aggregate_phase_stress` and wire into `evaluate_all_stress`**

In `src/engines/stress_engine.py`, add (after `evaluate_utilization_stress`):

```python
def evaluate_aggregate_phase_stress(
    capacity_results_df: pd.DataFrame,
    lab_phase_df: pd.DataFrame,
) -> pd.DataFrame:
    """Emit a PHASE_OVERLOAD event for each order that participates in a
    lab-phase whose AGGREGATE load exceeds the phase-stress threshold.

    This is the shared-capacity signal: three orders that each look fine alone
    but together saturate a phase all get flagged, so recommendations can react.
    Severity is MEDIUM so these flow into the at-risk branch (REALLOCATE/AT_RISK)
    rather than forcing REJECT.
    """
    events: list[dict] = []
    if lab_phase_df.empty or capacity_results_df.empty:
        return pd.DataFrame(columns=STRESS_EVENTS_COLS)

    overloaded = lab_phase_df[
        lab_phase_df["utilization_rate"] > PHASE_STRESS_THRESHOLD
    ]
    for _, lp in overloaded.iterrows():
        lab = lp["assigned_lab"]
        phase = lp["phase_name"]
        util = lp["utilization_rate"]
        util_txt = f"{util * 100:.0f}%" if math.isfinite(util) else "∞"
        members = capacity_results_df[
            (capacity_results_df["assigned_lab"] == lab)
            & (capacity_results_df["phase_name"] == phase)
        ]
        for order_id in members["order_id"].unique():
            events.append(_make_event(
                str(order_id),
                EVENT_PHASE_OVERLOAD,
                SEVERITY_MEDIUM,
                f"Lab '{lab}' phase '{phase}' is aggregately at {util_txt} "
                f"across {int(lp['num_orders'])} order(s) — shared capacity exceeded.",
                triggered_by=f"aggregate lab-phase utilization > {int(PHASE_STRESS_THRESHOLD * 100)}%",
                recommended_action="Reallocate or split orders sharing this phase",
            ))
    return pd.DataFrame(events, columns=STRESS_EVENTS_COLS)
```

Change `evaluate_all_stress` to accept and use the aggregate:

```python
def evaluate_all_stress(
    orders_df: pd.DataFrame,
    capacity_results_df: pd.DataFrame,
    labs_df: pd.DataFrame,
    phase_capacity_df: pd.DataFrame,
    scenario: ScenarioInputs,
    today: date | None = None,
    lab_phase_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Concatenate utilization + scenario / deadline + aggregate-phase stress."""
    today = today or date.today()
    util_events = evaluate_utilization_stress(capacity_results_df)
    scen_events = evaluate_scenario_stress(
        orders_df, capacity_results_df, labs_df, phase_capacity_df, scenario, today
    )
    agg_events = (
        evaluate_aggregate_phase_stress(capacity_results_df, lab_phase_df)
        if lab_phase_df is not None
        else pd.DataFrame(columns=STRESS_EVENTS_COLS)
    )
    frames = [f for f in (util_events, scen_events, agg_events) if not f.empty]
    if not frames:
        return pd.DataFrame(columns=STRESS_EVENTS_COLS)
    return pd.concat(frames, ignore_index=True)
```

Add `"evaluate_aggregate_phase_stress",` to `__all__`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_stress_engine.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/engines/stress_engine.py tests/test_stress_engine.py
git commit -m "feat(stress): aggregate lab-phase overload events per participating order

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: recommendation_engine — order utilization max + fixture lab

**Files:**
- Modify: `src/engines/recommendation_engine.py`
- Test: `tests/test_recommendation_engine.py`

- [ ] **Step 1: Update fixture to include `assigned_lab` and write failing test**

In `tests/test_recommendation_engine.py`, add `"assigned_lab"` to `_cap_row` (so fixtures match the new schema):

```python
def _cap_row(order_id: str, util: float, qty: int = 50, phase: str = "ph1", lab: str = "L1") -> dict:
    return {
        "order_id": order_id, "assigned_lab": lab, "product_type": "P", "phase_name": phase,
        "quantity": qty,
        "required_minutes": util * 100.0, "available_minutes": 100.0,
        "utilization_rate": util, "capacity_gap_minutes": 100.0 - util * 100.0,
        "is_overloaded": util > 0.85, "is_bottleneck": False,
    }
```

Add this test (max, not mean):

```python
def test_order_utilization_uses_worst_phase_not_mean() -> None:
    # Two phases: one at 30%, one at 120%. Mean = 75% (ACCEPT-ish);
    # max = 120% → must NOT be ACCEPT.
    cap = pd.DataFrame([
        _cap_row("O1", util=0.3, phase="ph1"),
        _cap_row("O1", util=1.2, phase="ph2"),
    ])
    recs = generate_recommendations(cap, _empty_stress(), _orders(), _pc(), _pm())
    assert recs.iloc[0]["recommendation"] != REC_ACCEPT
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_recommendation_engine.py::test_order_utilization_uses_worst_phase_not_mean -v`
Expected: FAIL — current `mean()` = 0.75 < 1.0 routes to at-risk/ACCEPT depending on labs; assertion may pass by luck on REALLOCATE but with single lab `_pc()` it's AT_RISK... Re-verify: mean 0.75 > 0.85? No. So it hits ACCEPT branch → returns REC_ACCEPT → test FAILS as intended.

- [ ] **Step 3: Change `_order_utilization` from mean to max**

In `src/engines/recommendation_engine.py`:

```python
def _order_utilization(group: pd.DataFrame) -> float:
    """Worst-phase utilization for an order: max of finite, inf if any inf.

    Max (not mean) because a single phase over capacity makes the order
    infeasible even if its other phases are light.
    """
    if (~group["utilization_rate"].apply(lambda v: math.isfinite(v))).any():
        return math.inf
    return float(group["utilization_rate"].max())
```

Update the two reason strings that say "Aggregate utilization"/"aggregate" to "Worst-phase utilization"/"worst phase" for accuracy:
- Line in at-risk branch: `reasons.append(f"Worst-phase utilization at {util * 100:.0f}%")`
- Line in accept branch: `f"All phases below {int(SAFE_UTILIZATION_THRESHOLD * 100)}% utilization (worst phase {util * 100:.0f}%)"`

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_recommendation_engine.py -v`
Expected: PASS (all). Single-phase fixtures: mean == max, so existing tests are unaffected.

- [ ] **Step 5: Commit**

```bash
git add src/engines/recommendation_engine.py tests/test_recommendation_engine.py
git commit -m "feat(recommendation): order utilization uses worst phase, not diluted mean

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Integration test — shared overload → no ACCEPT

**Files:**
- Test: `tests/test_aggregate_capacity.py` (NEW)

- [ ] **Step 1: Write the failing integration test**

Create `tests/test_aggregate_capacity.py`:

```python
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
from src.utils.constants import REC_ACCEPT


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
    # 3 orders × (40 × 5) = 200 each → aggregate 600 vs available 300 → 200%.
    # Each order ALONE is 200/300 = 67% (< 85% → would be ACCEPT individually).
    orders = _orders(3)
    cap = compute_capacity_results(orders, _pm(), _labs(), _pc(300.0), planning_days=1)
    agg = aggregate_lab_phase(cap)
    cap, _ = identify_bottlenecks(cap, agg)
    stress = evaluate_all_stress(
        orders, cap, _labs(), _pc(300.0), ScenarioInputs(),
        today=date(2026, 6, 1), lab_phase_df=agg,
    )
    recs = generate_recommendations(cap, stress, orders, _pc(300.0), _pm())
    # The shared phase is aggregately overloaded → no order should be ACCEPT.
    assert (recs["recommendation"] != REC_ACCEPT).all()
```

- [ ] **Step 2: Run test to verify it passes (engines already changed)**

Run: `pytest tests/test_aggregate_capacity.py -v`
Expected: PASS — each order gets an `EVENT_PHASE_OVERLOAD` from the aggregate stress, routing it to the at-risk branch (AT_RISK, single lab → no alternative).

- [ ] **Step 3: Commit**

```bash
git add tests/test_aggregate_capacity.py
git commit -m "test: shared lab-phase overload blocks blanket ACCEPT

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: charts — aggregate utilization bar + lab-phase gap bar

**Files:**
- Modify: `src/components/charts.py`

- [ ] **Step 1: Replace `phase_utilization_bar` body to consume the aggregate**

In `src/components/charts.py`, replace the function with:

```python
def phase_utilization_bar(lab_phase_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of AGGREGATE utilization per lab-phase, colored by status.

    Aggregate (Σ required / available per lab-phase) is the real capacity picture —
    it reflects all orders sharing a phase, not a single worst-case order.
    """
    if lab_phase_df.empty:
        return _empty_figure("No capacity data yet")

    finite_util = lab_phase_df["utilization_rate"].replace(
        [float("inf"), float("-inf")], float("nan")
    )
    work = (
        lab_phase_df.assign(_u=finite_util)
        .dropna(subset=["_u"])
        .copy()
    )
    if work.empty:
        return _empty_figure("All phases have undefined capacity")
    work["_label"] = work["phase_name"].astype(str) + " · " + work["assigned_lab"].astype(str)
    work = work.sort_values("_u", ascending=True)

    colors = [STATUS_COLORS[utilization_status(v)] for v in work["_u"].values]
    fig = go.Figure(
        go.Bar(
            x=work["_u"].values,
            y=work["_label"].values,
            orientation="h",
            marker=dict(color=colors),
            hovertemplate="%{y}: %{x:.0%}<extra></extra>",
        )
    )
    fig.add_vline(
        x=CRITICAL_UTILIZATION_THRESHOLD,
        line=dict(color="#9CA3AF", width=1, dash="dash"),
    )
    fig = _base_layout(fig, title="Aggregate utilization by lab-phase")
    fig.update_xaxes(tickformat=".0%", range=[0, max(1.2, float(work["_u"].max()) * 1.1)])
    return fig
```

- [ ] **Step 2: Replace `order_capacity_gap_bar` with `lab_phase_capacity_gap_bar`**

Replace the `order_capacity_gap_bar` function and `__all__` with:

```python
def lab_phase_capacity_gap_bar(lab_phase_df: pd.DataFrame) -> go.Figure:
    """Bar chart of AGGREGATE capacity gap per lab-phase. Negative (deficit) in red.

    Gap = available − Σ required, capacity counted once per lab-phase. Replaces the
    old per-order gap chart that inflated capacity by crediting it to each order.
    """
    if lab_phase_df.empty:
        return _empty_figure("No capacity data yet")

    work = lab_phase_df.copy()
    work["_label"] = work["phase_name"].astype(str) + " · " + work["assigned_lab"].astype(str)
    work = work.sort_values("capacity_gap_minutes")
    colors = [
        STATUS_COLORS["critical"] if v < 0 else STATUS_COLORS["safe"]
        for v in work["capacity_gap_minutes"].values
    ]
    fig = go.Figure(
        go.Bar(
            x=work["_label"].values,
            y=work["capacity_gap_minutes"].values,
            marker=dict(color=colors),
            hovertemplate="%{x}: %{y:.0f} min<extra></extra>",
        )
    )
    fig.add_hline(y=0, line=dict(color="#9CA3AF", width=1))
    fig = _base_layout(fig, title="Capacity gap by lab-phase (minutes)")
    return fig


__all__ = ["phase_utilization_bar", "lab_phase_capacity_gap_bar"]
```

- [ ] **Step 3: Smoke-check imports**

Run: `python -c "from src.components.charts import phase_utilization_bar, lab_phase_capacity_gap_bar; print('ok')"`
Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add src/components/charts.py
git commit -m "feat(charts): aggregate lab-phase utilization + gap bars

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: capacity_dashboard page — KPIs from aggregate

**Files:**
- Modify: `src/ui/pages/capacity_dashboard.py`

- [ ] **Step 1: Rewrite the engine wiring + KPI block**

Replace the imports and the body from the `# --- KPIs ---` section through the chart line. New imports near the top:

```python
from src.components.charts import lab_phase_capacity_gap_bar, phase_utilization_bar
from src.engines.capacity_engine import (
    aggregate_lab_phase,
    compute_capacity_results,
    overall_utilization,
)
from src.utils.formatting import fmt_int, fmt_minutes, fmt_pct, utilization_status
```

Replace the wiring (after `cap = compute_capacity_results(...)`) with:

```python
    cap = compute_capacity_results(orders_scn, pm_df, labs_df, pc_scn, planning_days=planning_days)
    lab_phase = aggregate_lab_phase(cap)
    cap, summary = identify_bottlenecks(cap, lab_phase)
    stress = evaluate_all_stress(
        orders_scn, cap, labs_df, pc_scn, scenario, lab_phase_df=lab_phase
    )
    recs = generate_recommendations(cap, stress, orders_scn, pc_scn, pm_df)

    # --- KPIs (aggregated per lab-phase: capacity counted once) ---
    overall_util = overall_utilization(lab_phase)
    if lab_phase.empty:
        min_gap = 0.0
        total_gap = 0.0
        overloaded_phases = 0
    else:
        min_gap = float(lab_phase["capacity_gap_minutes"].min())
        total_gap = float(lab_phase["capacity_gap_minutes"].sum())
        overloaded_phases = int(lab_phase[lab_phase["is_overloaded"]].shape[0])

    kpi_row([
        {
            "label": "Overall utilization",
            "value": fmt_pct(overall_util) if math.isfinite(overall_util) else "∞",
            "status": utilization_status(overall_util),
        },
        {
            "label": "Minimum capacity gap",
            "value": fmt_minutes(min_gap),
            "status": "critical" if min_gap < 0 else "safe",
        },
        {"label": "Planning window", "value": f"{planning_days} day(s)", "status": "neutral"},
        {
            "label": "Overloaded phases",
            "value": fmt_int(overloaded_phases),
            "status": "critical" if overloaded_phases else "safe",
        },
    ])

    gap_sign = "feasible overall" if total_gap >= 0 else "capacity shortfall"
    st.caption(
        f"Aggregate gap across all lab-phases: **{fmt_minutes(total_gap)}** ({gap_sign}). "
        "The KPI above shows the single most critical lab-phase."
    )

    if summary.get("most_critical_phase"):
        st.caption(
            f"Most critical phase across orders: **{summary['most_critical_phase']}** "
            f"({fmt_pct(summary['most_critical_phase_utilization'])})"
        )

    # --- Chart ---
    st.subheader("Phase utilization")
    st.plotly_chart(phase_utilization_bar(lab_phase), width="stretch")

    st.subheader("Capacity gap by lab-phase")
    st.plotly_chart(lab_phase_capacity_gap_bar(lab_phase), width="stretch")
```

(Leave the Operational stress / Recommendations sections below unchanged.)

- [ ] **Step 2: Smoke-check import**

Run: `python -c "import src.ui.pages.capacity_dashboard as m; print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add src/ui/pages/capacity_dashboard.py
git commit -m "feat(dashboard): KPIs from aggregate lab-phase truth + min-gap KPI

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: overview + scenario_testing pages — shared overall-utilization

**Files:**
- Modify: `src/ui/pages/overview.py`, `src/ui/pages/scenario_testing.py`

- [ ] **Step 1: overview.py — use the aggregate helper**

Replace imports + the compute block in `_compute_overview_kpis`:

```python
from src.engines.capacity_engine import (
    aggregate_lab_phase,
    compute_capacity_results,
    overall_utilization,
)
```

Replace:

```python
    cap = compute_capacity_results(orders_scn, pm_df, labs_df, pc_scn, planning_days=planning_days)
    lab_phase = aggregate_lab_phase(cap)
    cap, _ = identify_bottlenecks(cap, lab_phase)
    stress = evaluate_all_stress(
        orders_scn, cap, labs_df, pc_scn, scenario, lab_phase_df=lab_phase
    )

    n_orders = len(orders_df)
    n_products = pm_df["product_type"].nunique() if not pm_df.empty else 0

    overall_util = overall_utilization(lab_phase)
    crit_alerts = int((stress["severity"] == "high").sum()) if not stress.empty else 0
```

(Remove the now-unused `finite = cap[...]...mean()` lines.)

- [ ] **Step 2: scenario_testing.py — use the aggregate helper**

Replace imports:

```python
from src.engines.capacity_engine import (
    aggregate_lab_phase,
    compute_capacity_results,
    overall_utilization,
)
```

Replace the `_snapshot` body:

```python
def _snapshot(orders, pm, labs, pc, scenario, planning_days) -> dict:
    orders_scn, pc_scn = apply_scenario(orders, pc, scenario)
    cap = compute_capacity_results(orders_scn, pm, labs, pc_scn, planning_days=planning_days)
    lab_phase = aggregate_lab_phase(cap)
    cap, _ = identify_bottlenecks(cap, lab_phase)
    stress = evaluate_all_stress(
        orders_scn, cap, labs, pc_scn, scenario, lab_phase_df=lab_phase
    )
    recs = generate_recommendations(cap, stress, orders_scn, pc_scn, pm)

    return {
        "overall_utilization": overall_utilization(lab_phase),
        "overloaded_phases": int(lab_phase[lab_phase["is_overloaded"]].shape[0]) if not lab_phase.empty else 0,
        "critical_events": int((stress["severity"] == "high").sum()) if not stress.empty else 0,
        "accepted_orders": int((recs["recommendation"] == REC_ACCEPT).sum()) if not recs.empty else 0,
    }
```

- [ ] **Step 3: Smoke-check imports**

Run: `python -c "import src.ui.pages.overview, src.ui.pages.scenario_testing; print('ok')"`
Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add src/ui/pages/overview.py src/ui/pages/scenario_testing.py
git commit -m "feat(pages): overview + scenario use weighted aggregate utilization

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: phase_saturation page — per-phase table from aggregate

**Files:**
- Modify: `src/ui/pages/phase_saturation.py`

- [ ] **Step 1: Rewrite wiring + per-phase table to use the aggregate**

Replace imports:

```python
from src.components.charts import phase_utilization_bar
from src.engines.capacity_engine import aggregate_lab_phase, compute_capacity_results
```

Replace the wiring + the per-phase table block:

```python
    cap = compute_capacity_results(orders_scn, pm_df, labs_df, pc_scn, planning_days=planning_days)
    lab_phase = aggregate_lab_phase(cap)
    cap, summary = identify_bottlenecks(cap, lab_phase)

    most_phase = summary.get("most_critical_phase") or "—"
    most_util = summary.get("most_critical_phase_utilization", 0.0)
    kpi_card(
        label="Most critical phase",
        value=f"{most_phase} · {fmt_pct(most_util) if math.isfinite(most_util) else '∞'}",
        status=utilization_status(most_util),
    )

    overloaded_count = int(lab_phase[lab_phase["is_overloaded"]].shape[0]) if not lab_phase.empty else 0
    kpi_row([
        {
            "label": "Phases overloaded",
            "value": fmt_int(overloaded_count),
            "status": "critical" if overloaded_count else "safe",
        },
        {
            "label": "Lab-phases evaluated",
            "value": fmt_int(int(lab_phase.shape[0])),
            "status": "neutral",
        },
    ])

    st.subheader("Utilization by lab-phase")
    st.plotly_chart(phase_utilization_bar(lab_phase), width="stretch")

    # Per lab-phase table — AGGREGATE load (capacity counted once).
    st.subheader("Detail per lab-phase")
    if lab_phase.empty:
        st.info("No capacity data yet.")
    else:
        lp = lab_phase.copy()
        lp["status"] = lp["utilization_rate"].apply(utilization_status)
        lp["utilization"] = lp["utilization_rate"].apply(
            lambda v: fmt_pct(v) if math.isfinite(v) else "∞"
        )
        lp["total_required"] = lp["total_required_minutes"].apply(fmt_minutes)
        lp["available"] = lp["available_minutes"].apply(fmt_minutes)
        lp["capacity_gap"] = lp["capacity_gap_minutes"].apply(fmt_minutes)
        st.dataframe(
            lp[[
                "assigned_lab", "phase_name", "utilization",
                "total_required", "available", "capacity_gap", "num_orders", "status",
            ]].sort_values(["status", "assigned_lab"]),
            width="stretch",
        )
```

- [ ] **Step 2: Update the per-order detail table header + relabel**

Replace the per-order block's intro comment and subheader so it reads as a contribution view (keep the existing groupby logic that follows, but it now has `assigned_lab` available — leave the aggregation code as-is):

```python
    # Per-order detail — each order's CONTRIBUTION to the shared lab-phase.
    # (A single order can look light here yet the lab-phase is overloaded in
    # aggregate — see the table above.)
    st.subheader("Detail per order (contribution to shared phase)")
    finite = cap.copy()
    finite["_util"] = finite["utilization_rate"].replace([math.inf, -math.inf], math.nan)
    per_order = (
        finite.groupby(["order_id", "product_type", "phase_name"])
        .agg(
            utilization=("_util", "max"),
            required_minutes=("required_minutes", "sum"),
            available_minutes=("available_minutes", "max"),
            capacity_gap_minutes=("capacity_gap_minutes", "sum"),
        )
        .reset_index()
    )
```

(The display-formatting + `st.dataframe(...)` that follow stay unchanged. Delete the OLD per-phase `per_phase = finite.groupby("phase_name")...` block and its `st.dataframe` — it is fully replaced by the lab-phase table in Step 1.)

- [ ] **Step 3: Smoke-check import**

Run: `python -c "import src.ui.pages.phase_saturation as m; print('ok')"`
Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add src/ui/pages/phase_saturation.py
git commit -m "feat(phase-saturation): aggregate lab-phase table; per-order as contribution

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 10: timeline_engine docstring note

**Files:**
- Modify: `src/engines/timeline_engine.py`

- [ ] **Step 1: Add the assumption note to `build_timeline` docstring**

Append to the existing docstring (after the current text):

```python
    NOTE (capacity contention): duration is computed per order *in isolation* —
    it assumes the order has the full daily lab-phase capacity to itself. It does
    NOT model queuing when multiple orders share a lab-phase. `overlap_flag`
    surfaces concurrent orders in the same lab as the proxy for that risk. A true
    contention/scheduling model is intentionally out of scope (deterministic MVP).
```

- [ ] **Step 2: Smoke-check import**

Run: `python -c "import src.engines.timeline_engine as m; print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add src/engines/timeline_engine.py
git commit -m "docs(timeline): document order-in-isolation duration assumption

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 11: Full test run + manual smoke

**Files:** none (verification)

- [ ] **Step 1: Run the whole suite**

Run: `pytest tests/ -v`
Expected: PASS (all). If any pre-existing test references `order_capacity_gap_bar` or the old `phase_utilization_bar(cap)` signature, update it to the new lab-phase API.

- [ ] **Step 2: Manual smoke of the app in demo mode**

Run: `streamlit run app.py` (or rely on the `/run` skill). In the browser: enable demo mode, open **Capacity Dashboard** and confirm:
- "Overall utilization" is a sensible weighted % (no longer a diluted 36% vs 235% contradiction),
- "Minimum capacity gap" shows the worst lab-phase (small, readable number — NOT 41132h),
- the aggregate-gap caption shows the total-gap sign,
- "Phase utilization" bars are labeled `phase · lab` and reflect aggregate load.

Confirm **Overview**, **Phase Saturation**, **Scenario Testing** show consistent utilization.

- [ ] **Step 3: Commit any test fixups from Step 1 (if needed)**

```bash
git add -A && git commit -m "test: align remaining tests with lab-phase aggregate API

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 12: Docs + TASKS.md

**Files:**
- Modify: `docs/PRESENTATION_AUDIT.md`, `README.md`, `docs/TASKS.md`

- [ ] **Step 1: Update the formulas section (`docs/PRESENTATION_AUDIT.md` §7)**

Add, under the existing formula block, an "Aggregate (lab-phase) layer" subsection:

```
# Aggregate layer — the capacity truth (per assigned_lab + phase_name)
total_required(lab,phase)  = Σ required_minutes over orders in that lab-phase
available(lab,phase)       = available_minutes_per_day × planning_days   (counted ONCE)
utilization(lab,phase)     = total_required / available
capacity_gap(lab,phase)    = available − total_required

overall_utilization = Σ total_required / Σ available   (over all lab-phases)

KPI "Minimum capacity gap" = min capacity_gap across lab-phases (worst bottleneck)
Most critical phase        = lab-phase with the highest aggregate utilization
```

Add one sentence explaining the two-level model: per-(order,phase) answers "does one order alone saturate a phase?"; the aggregate answers "do all orders together saturate it?".

- [ ] **Step 2: Add a "How capacity is computed" note to `README.md`**

Add a short subsection summarizing the two-level model and that on-screen KPIs aggregate per lab-phase (capacity counted once), preventing inflated gap figures.

- [ ] **Step 3: Update `docs/TASKS.md`**

Per the project loop protocol at the bottom of TASKS.md: add the tasks implemented here (capacity aggregation fix) marked `Status: DONE`, referencing this plan and the design spec.

- [ ] **Step 4: Commit**

```bash
git add docs/PRESENTATION_AUDIT.md README.md docs/TASKS.md
git commit -m "docs: two-level capacity model (aggregate lab-phase truth)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Self-review notes
- **Spec coverage:** §1 capacity_engine → Task 1; §2 bottleneck → Task 2; §3 KPIs/pages → Tasks 7,8,9; §4 charts → Task 5(charts is Task 6); §5 stress+recommendation → Tasks 3,4 (+ integration Task 5); §6 timeline → Task 10; §7 tests/docs → Tasks 1–5,11,12. All covered.
- **Type consistency:** `aggregate_lab_phase` / `overall_utilization` / `LAB_PHASE_LOAD_COLS` names used identically across tasks; `identify_bottlenecks(cap, lab_phase)` and `evaluate_all_stress(..., lab_phase_df=...)` signatures consistent across all call sites (capacity_dashboard, overview, scenario_testing, phase_saturation).
- **Dead-code note:** `order_capacity_gap_bar` confirmed unused before replacement.
