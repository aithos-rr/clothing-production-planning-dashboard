# Capacity Aggregation Fix — Design

> **Date:** 2026-05-29
> **Status:** Approved (brainstorming)
> **Scope:** C — full fix across all utilization consumers
> **Origin:** Post-deploy feedback (Felino Marvi, 2026-05-28) — the "Total capacity
> gap = 41132h" KPI and contradictory dashboard numbers.

## Problem

`capacity_engine.compute_capacity_results` emits **one row per `(order, phase)`**.
On every such row the `available_minutes` of the `(lab, phase)` is **repeated
identically** for each order that shares it. Three KPIs then apply three different
aggregations to this inflated table, producing mutually contradictory numbers:

| KPI | Current code | Bug |
|---|---|---|
| **Total capacity gap → 41132h** | `cap["capacity_gap_minutes"].sum()` (`capacity_dashboard.py:39`) | Sums `available − required` over all rows → available counted **N times** (once per order). Inflated. |
| **Overall utilization → 36%** | `finite_util.mean()` (`capacity_dashboard.py:37-38`, also in `overview.py:55` and `scenario_testing.py:25`) | Mean of per-row ratios `required_single_order / full_phase_capacity` → each order looks tiny → diluted, meaningless. |
| **confezione capo 235.8%** | `max` per phase (`charts.py:63`, `bottleneck_engine.py:49`) | Worst-case of a **single** order, not the aggregate phase load. Real signal, mislabeled. |

The contradiction "36% overall but 235% on one phase" is exactly the symptom of
mixing per-row mean, inflated sum, and per-row max.

**Root cause:** the system never aggregates **first** by `assigned_lab + phase_name`
and **then** computes gap/utilization. The same defect also blinds the
`recommendation_engine` and `stress_engine`: three orders that together saturate a
phase to 250% each look fine in isolation (< 85%) and all get `ACCEPT`.

## Decisions (settled in brainstorming)

1. **Aggregation granularity:** `assigned_lab + phase_name` (two labs running the
   same phase have separate capacities).
2. **Gap KPI:** show the **minimum** capacity gap (worst lab-phase group) as the
   primary KPI; show the **sign** of the aggregate total gap as context.
3. **Scope:** C — fix the display KPIs, the charts, AND the downstream decision
   engines (recommendation, stress) so recommendations reflect shared capacity.
4. **Timeline:** option A — leave the per-order duration math as-is (a reasonable
   "order in isolation" estimate) and document the assumption. No scheduler.

## Core design

Introduce a **second level of truth** alongside `capacity_results`: the per
`(assigned_lab, phase_name)` aggregate, where capacity is counted **once**.

Two clearly separated concepts:

- **Solo-order load** (per-order-per-phase, already exists): *"does this order
  alone saturate the phase?"* → drives SPLIT / REJECT.
- **Aggregate load** (per lab-phase, new): *"do all orders together saturate the
  phase?"* → drives on-screen KPIs and real overload detection.

### 1. `capacity_engine.py`
- Add **`assigned_lab`** to `CAPACITY_RESULTS_COLS` and populate it (lab is already
  computed internally, just not emitted).
- New `aggregate_lab_phase(capacity_results_df) → DataFrame`, schema
  `LAB_PHASE_LOAD_COLS`:
  `assigned_lab, phase_name, total_required_minutes, available_minutes` (once),
  `utilization_rate` (= total_required / available, inf if available ≤ 0 and
  required > 0), `capacity_gap_minutes` (= available − total_required),
  `is_overloaded` (util > SAFE threshold), `num_orders`.
- New `overall_utilization(lab_phase_df) → float` = `Σ total_required / Σ available`.
  **Single source of truth** used by every page (replaces the three `mean()` copies).

### 2. `bottleneck_engine.py`
- Keep per-order `bottleneck_rank` / `is_bottleneck` (within-order ranking).
- `most_critical_phase` summary switches to **aggregate** lab-phase utilization
  (max across lab-phase groups), not per-order max.

### 3. KPIs & pages (display)
**`capacity_dashboard.py`:**
- *Overall utilization* → `overall_utilization(lab_phase)`.
- *Minimum capacity gap* → `lab_phase.capacity_gap_minutes.min()`, critical if < 0.
- *Context caption* → sign of aggregate total gap: "Aggregate gap +Xh (plan feasible
  overall)" / "−Xh (capacity shortfall)".
- *Overloaded phases* → count of lab-phase groups with aggregate util > threshold.
- *Most critical phase* → from aggregate summary.

**`overview.py`** and **`scenario_testing.py`** → use `overall_utilization` +
lab-phase `overloaded_phases`. Full consistency across pages.

**`phase_saturation.py`** → per-phase table driven by lab-phase aggregate
(aggregate util, total required, available, gap, `num_orders`, status, bottleneck).
Per-order table stays, relabeled as "order's contribution to the shared phase".

### 4. Charts (`charts.py`)
- `phase_utilization_bar(lab_phase_df)` → one bar per lab-phase group, **aggregate**
  utilization. Title "worst case across orders" → "Aggregate utilization by
  lab-phase". Keep the 100% line.
- Replace `order_capacity_gap_bar` with `lab_phase_capacity_gap_bar` (gap per
  lab-phase group, red if negative). Verify current usage during planning.

### 5. Decision consistency (`stress_engine.py` + `recommendation_engine.py`)
Eliminates the "phase at 250% but all orders ACCEPT" contradiction.

**`stress_engine.py`:**
- New `evaluate_aggregate_phase_stress(lab_phase_df, ...)` emitting
  `EVENT_UTILIZATION_CRITICAL` (≥100%) / `EVENT_PHASE_OVERLOAD` (between phase-stress
  threshold and 100%) for aggregately-overloaded lab-phase groups, **attributed to
  each participating order** so they flow into recommendations.
- Existing per-order events stay ("this order alone is infeasible"), messages
  clarified to distinguish solo vs aggregate.

**`recommendation_engine.py`:**
- `_order_utilization`: mean → **max** across the order's phases.
- At-risk branch also fires when the order **participates in an aggregately
  overloaded lab-phase** (via the new events). Result: an order at 40% on its own
  but sharing a phase collectively at 250% becomes AT_RISK / REALLOCATE, not ACCEPT.

### 6. `timeline_engine.py` (option A)
- No calculation change. Add an explicit docstring note: duration is "order in
  isolation", does not model capacity contention; `overlap_flag` remains the risk
  proxy.

### 7. Tests & docs
- Update `tests/test_capacity_engine.py`, `tests/test_recommendation_engine.py`;
  add tests for `aggregate_lab_phase`, `overall_utilization`, and the key case
  "3 orders that together saturate a phase → none ACCEPT".
- Update `docs/PRESENTATION_AUDIT.md` §7 (formulas) and `README.md` with the
  two-level model.
- Update `TASKS.md` (loop protocol).

## Out of scope
- Real scheduler / capacity-contention modeling in the timeline (option C rejected).
- KPI relabeling to Marvi's "Capacity buffer / Critical bottleneck / Orders at risk"
  set (option 3) — kept as a possible later cosmetic pass.
