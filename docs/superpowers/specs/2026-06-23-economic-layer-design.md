# Design — Cost Feasibility Dashboard (Economic Layer v2)

> Status: approved design (brainstorming output)
> Date: 2026-06-23
> Supersedes/extends: `PRD — Cost Feasibility Dashboard` (compagna v2 brief),
> reconciled against the live codebase and the ground-truth workbook
> `clothing_production_planning_database_with_economic_layer.xlsx`.

## 1. Purpose

Add an **economic layer** to the existing operational planning dashboard: a new
page that answers "the order is technically feasible, but is it economically
sustainable?" by estimating **production cost**, **overtime cost**, **overhead**,
and the **cost impact of reallocating** an order to an alternative lab — then
emitting a cost-driven **economic recommendation** that complements the existing
operational recommendation.

The MVP is **cost-focused, not margin-focused** (see §8 exclusions).

## 2. Context & ground truth

The codebase is a rule-based Streamlit dashboard (`app.py` radio router → per-page
`render()` under `src/ui/pages/`). Engines under `src/engines/` are pure
functions returning DataFrames. 43 tests green at baseline.

The compagna delivered an updated workbook with an `economic_layer` sheet (60
orders, 33 columns) of **already-computed economics**. It is the source of truth
for the **formulas** and the **input parameters**. Verified facts:

- Formulas match PRD §8 exactly (validated to the cent for labour, overhead,
  total, reallocation delta).
- `required_hours = total_standard_minutes / 60` (SMV-based, order-level) — per
  `data_dictionary`.
- `standard_hourly_cost` is **per-lab** (L1=22.0, L7=17.8, L9=18.0, …).
- `overhead_pct` is **per-product** (Cappotto=0.15, T-shirt=0.10, …).
- `overtime_multiplier` is **per-lab** (1.25–1.40); overtime is **inactive** in
  this dataset (no compressed deadlines → all overtime hours = 0).
- Real recommendations: **ACCEPT (46)** and **CONSIDER REALLOCATION (14)**;
  `cost_status` all HEALTHY. The real logic is **cost/reallocation-driven**, which
  is why excluding margin does not break the recommendation.
- The workbook **already parses cleanly** through the live pipeline
  (`normalize_all`): 60 orders, 91 product_matrix rows, 10 labs, 373
  phase_capacity rows, **0 high-severity warnings**.

## 3. Architecture (match existing patterns; no deviation)

| Unit | File | Responsibility |
|---|---|---|
| Economic engine | `src/engines/economic_engine.py` | Pure formula functions + `compute_economic_results(...)` returning `economic_results_df` |
| Economic input loader | extend `src/parsers/normalizer.py` (+ small `economic` block) | Source per-lab/per-product/per-order economic params from the `economic_layer` sheet when present; else config defaults |
| Page | `src/ui/pages/cost_feasibility.py` (`render()`) | KPIs, breakdown, lab comparison, cost-vs-risk chart, alerts, combined recommendation |
| Constants | extend `src/utils/constants.py` | Economic recommendation labels, cost-status, reallocation threshold key |
| Config | extend `config/defaults.yaml` | All economic defaults (0 hardcode) |
| Charts | extend `src/components/charts.py` | `cost_vs_risk_scatter(...)` |
| Demo data | extend `scripts/build_sample_data.py` | Add economic columns to `sample_planning.xlsx` (derived, realistic) |
| Nav | `app.py` | Register page between Scenario Testing and Future AI Layer |

Reused as-is: `kpi_row`/`kpi_card`, `render_alerts`, `find_alternative_lab`,
`apply_scenario`, `compute_capacity_results` → `aggregate_lab_phase`,
`generate_recommendations` (operational), `fmt_*` formatters.

## 4. Data flow

1. Page runs the **live operational pipeline** (scenario → capacity → aggregate →
   bottleneck → stress → operational recommendation) exactly like Capacity
   Dashboard.
2. `required_hours` for each order = `Σ required_minutes / 60` from
   `capacity_results_df` (the dashboard's own truth), **not** the SMV column —
   keeps the economic layer consistent and scenario-reactive.
   *Documented caveat:* integrated totals differ slightly from the Excel's
   `economic_layer` (which used SMV without per-phase setup). Expected and more
   internally consistent.
3. Economic input params come from the input loader (§5).
4. `compute_economic_results` produces `economic_results_df` (§6).
5. Page renders KPIs, breakdown, lab comparison, cost-vs-risk, alerts, and the
   combined operational+economic recommendation panel.

## 5. Economic input sourcing (0 hardcode)

The loader produces, with this precedence:

1. **From `economic_layer` sheet** (when the uploaded workbook has it): per-lab
   `standard_hourly_cost` & `overtime_multiplier`, per-product `overhead_pct`,
   per-order `setup_cost`.
2. **From `config/defaults.yaml`** otherwise (fallback, flagged "estimated"):
   `standard_hourly_cost: 18.0`, `overtime_multiplier: 1.25`,
   `fixed_setup_cost: 0.0`, `overhead_percentage: 0.10`, `currency: "EUR"`,
   plus `reallocation_material_threshold_eur` for the REALLOCATE trigger, and
   per-product `reference_price_per_garment` used only to derive realistic demo
   values in the sample dataset (never to display margin).

No numeric literal lives in engine or page code; every default is a config key.
The page shows a clear banner when any value is a default ("Some cost values are
estimated using default assumptions.").

## 6. `economic_results_df` schema (output)

`order_id, assigned_lab, required_hours, available_hours, standard_labour_cost,
overtime_hours, overtime_cost, setup_cost, overhead_cost, total_estimated_cost,
cost_per_garment_internal, alternative_lab, alternative_total_cost,
cost_delta_if_reallocated, economic_recommendation, economic_reason,
uses_default_costs`

`cost_per_garment_internal` is computed for internal lab-comparison ranking but
**not surfaced as a KPI** (per exclusion of §8.11 / KPI2). Margin / revenue
columns are **not** produced.

## 7. Core formulas (PRD §8, margin formulas excluded)

```
required_hours          = sum(required_minutes per order) / 60      # from capacity engine
standard_labour_cost    = required_hours * standard_hourly_cost(lab)
excess_hours            = max(0, required_hours - available_hours)
overtime_hourly_cost    = standard_hourly_cost(lab) * overtime_multiplier(lab)
overtime_cost           = excess_hours * overtime_hourly_cost        # 0 unless overtime_allowed & compressed
setup_cost              = fixed_setup_cost(order/product)
overhead_cost           = (standard_labour_cost + overtime_cost + setup_cost) * overhead_pct(product)
total_estimated_cost    = standard_labour_cost + overtime_cost + setup_cost + overhead_cost
cost_impact_realloc     = total_cost(alternative_lab) - total_cost(current_lab)
```

**Excluded** (user request): §8.9 estimated_margin, §8.10 margin_percentage,
§8.11 average_cost_per_garment (as a surfaced metric), KPI2, KPI3.

## 8. Economic recommendation (5 cost-driven types)

First match wins, evaluated per order, combined with the operational signal:

1. **REJECT** — operationally infeasible (operational REJECT / utilization ∞ /
   no available capacity) **and** no viable alternative lab.
2. **POSTPONE** — overtime required (excess_hours > 0) and the operational layer
   flags a deadline issue → postponing avoids the overtime premium.
3. **ACCEPT WITH OVERTIME** — overtime required, lab allows overtime, no cheaper
   alternative → accept and surface the overtime cost premium.
4. **REALLOCATE** — an alternative lab is *materially cheaper*
   (`cost_delta_if_reallocated <= -reallocation_material_threshold_eur`) **or**
   reduces operational risk → suggest the named alternative lab + the € delta.
5. **ACCEPT** — feasible, no overtime, no materially cheaper alternative.

`RENEGOTIATE PRICE` is intentionally dropped (price/margin-based). Each row gets
a human `economic_reason` and is never empty.

## 9. Page layout & components (full MVP)

- **Header** + estimated-values banner (when defaults used).
- **KPI row (4, cost-focused):** Total Estimated Production Cost · Overtime Cost ·
  Standard Labour Cost · Cost Impact of Reallocation.
- **Cost Breakdown table:** component, amount, % of total (labour, overtime,
  setup, overhead, total).
- **Lab Comparison table:** lab, estimated cost, utilization, operational risk,
  cost delta, economic recommendation.
- **Cost-vs-Risk chart** (`cost_vs_risk_scatter`): x = estimated cost, y =
  utilization/operational risk, points = labs/allocation scenarios.
- **Economic Alerts:** overtime cost impact, materially-cheaper alternative,
  missing/default cost data, no available capacity.
- **Recommendation panel:** combined operational + economic decision per order,
  reusing the prominent card style.

Order selector (selectbox) drives breakdown / lab-comparison / recommendation for
the focused order; KPIs aggregate across all orders.

## 10. Edge cases (PRD §16)

Missing hourly cost (→ default + banner), `quantity == 0` (cost-per-garment
guarded, no ZeroDivision), `required_hours == 0`, missing alternative lab (delta
shown as "—", no REALLOCATE), no available capacity (overtime/REJECT path,
utilization ∞ handled), unknown-product orders excluded from aggregation.
Missing data shows warnings, never breaks the page (top-level try/except already
in `app.py`).

## 11. Testing

`tests/test_economic_engine.py`:
- Formula units: labour, excess hours, overtime cost, overhead, total, realloc delta.
- **Golden test:** feed the Excel's own `required_hours` + per-row params into the
  pure formula functions; assert reproduction of `standard_labour_cost_eur`,
  `overhead_cost_eur`, `total_estimated_cost_eur` to the cent.
- Recommendation: ACCEPT / REALLOCATE (materially cheaper) / ACCEPT WITH OVERTIME
  / POSTPONE / REJECT branches.
- Edge: quantity 0, missing alternative lab, missing cost data → defaults+flag.
- No Streamlit import; in-memory DataFrames only.

Whole suite (`pytest tests/ -v`) stays green; baseline 43 unaffected.

## 12. File coherence / pre-v2 housekeeping

- Move workbook → `data/sample/clothing_production_planning_database_with_economic_layer.xlsx`.
- Rename `PRD — Cost Feasibility Dashboard.md` → `docs/PRD_ECONOMIC_LAYER_v2.md`.
- Update README (nav list, datasets table, project structure, economic layer note).
- Update `docs/MASTER_PRD_v2_EXECUTION.md` (note the economic layer addition),
  `docs/TASKS.md` (new PHASE 10 — Economic Layer), `docs/PRESENTATION_AUDIT.md`
  (mention the new page).
- Commit a tagged **pre-v2** snapshot before implementing.

## 13. Task breakdown (TASKS.md PHASE 10, atomic, TDD, per-task commit)

1. **TASK-042** — Economic config defaults + constants (config/defaults.yaml, constants.py).
2. **TASK-043** — Extend demo data with derived economic columns (build_sample_data.py).
3. **TASK-044** — Economic input loader (normalizer): source params from `economic_layer` / config.
4. **TASK-045** — Economic engine: pure formulas + `compute_economic_results` (+ golden test).
5. **TASK-046** — Economic recommendation logic (5 cost-driven types).
6. **TASK-047** — `cost_vs_risk_scatter` chart component.
7. **TASK-048** — Cost Feasibility page (KPIs, breakdown, lab comparison, chart, alerts, combined rec).
8. **TASK-049** — Register page in nav + data gating.
9. **TASK-050** — Docs/README sweep + final verification (full suite green, app smoke test).

Each task: implement → tests green → commit `feat(TASK-0NN): …`.

## 14. Out of scope (unchanged from PRD §4)

Advanced cost accounting, ERP integration, live accounting, price optimization,
financial forecasting, AI cost prediction, full P&L. Margin/profitability display
(this version is cost-focused).
