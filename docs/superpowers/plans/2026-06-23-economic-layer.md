# Cost Feasibility Dashboard (Economic Layer v2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a cost-focused economic layer (new engine + page) that estimates production/overtime/overhead cost and the cost impact of reallocation, with a 5-type cost-driven economic recommendation, fully consistent with the live capacity pipeline.

**Architecture:** Pure formula functions in a new `economic_engine.py` consume `required_hours` derived from the dashboard's own `capacity_results_df`. Economic input parameters (per-lab hourly cost & overtime multiplier, per-product overhead %, per-order setup cost) are sourced from an `economic_layer` sheet when present, else from `config/defaults.yaml`. A new Streamlit page renders KPIs, cost breakdown, lab comparison, a cost-vs-risk chart, alerts, and a combined operational+economic recommendation.

**Tech Stack:** Python 3.12, pandas, Plotly, Streamlit, pytest, openpyxl.

**Reference spec:** `docs/superpowers/specs/2026-06-23-economic-layer-design.md`

**Ground-truth workbook:** `data/sample/clothing_production_planning_database_with_economic_layer.xlsx` (sheet `economic_layer`, 60 rows). Verified formulas reproduce its values to the cent; reallocation threshold of **500€** reproduces its ACCEPT/CONSIDER-REALLOCATION split exactly.

---

## Task 0: Pre-v2 housekeeping (file coherence + snapshot)

**Files:**
- Move: `clothing_production_planning_database_with_economic_layer.xlsx` → `data/sample/`
- Rename: `PRD — Cost Feasibility Dashboard.md` → `docs/PRD_ECONOMIC_LAYER_v2.md`

- [ ] **Step 1: Move workbook & rename PRD via git**

```bash
git mv "clothing_production_planning_database_with_economic_layer.xlsx" data/sample/clothing_production_planning_database_with_economic_layer.xlsx
git mv "PRD — Cost Feasibility Dashboard.md" docs/PRD_ECONOMIC_LAYER_v2.md
```

- [ ] **Step 2: Verify the workbook still parses from the new location**

Run:
```bash
.venv/bin/python -c "from src.parsers.excel_parser import parse_excel; from src.parsers.normalizer import normalize_all; r=normalize_all(parse_excel('data/sample/clothing_production_planning_database_with_economic_layer.xlsx')); print(r['orders'].shape, r['used_mock'])"
```
Expected: `(60, 10) {'orders': False, 'product_matrix': False, 'labs': False, 'phase_capacity': False}`

- [ ] **Step 3: Update README datasets table + docs pointers (do in Task 9; here only move).** Commit the moves.

```bash
git commit -m "chore(pre-v2): relocate economic workbook to data/sample, rename PRD to docs/PRD_ECONOMIC_LAYER_v2.md"
```

> NOTE: The full README/docs/TASKS pre-v2 update + tagged snapshot happens in **Task 9-pre** below, just before implementation of code tasks, per the user's sequence (pre-v2 commit → implement). Task 0 is only the safe file relocation.

---

## Task 9-pre: Docs sweep + pre-v2 snapshot commit

> Run this BEFORE the code tasks (1–9), per the user's sequence. Numbered 9-pre because the final docs verification closes in Task 9.

**Files:**
- Modify: `README.md` (nav list, datasets table, project structure, economic note)
- Modify: `docs/TASKS.md` (add PHASE 10 task stubs, status TODO)
- Modify: `docs/MASTER_PRD_v2_EXECUTION.md` (note economic layer addition)
- Modify: `docs/PRESENTATION_AUDIT.md` (mention new page)

- [ ] **Step 1: Add PHASE 10 section to `docs/TASKS.md`** listing TASK-042…TASK-050 with `Status: TODO`, dependencies, and one-line expected output each (mirror the task titles in this plan). Append after TASK-041.

- [ ] **Step 2: README** — add `Cost Feasibility Dashboard` to the nav list (between Scenario Testing and Future AI Layer), add the economic workbook to the datasets table, add a short "Economic layer" subsection under "How capacity is computed".

- [ ] **Step 3: MASTER_PRD_v2_EXECUTION.md** — add a one-paragraph note at the top of the scope section: economic layer added as a cost-focused page; margin/profitability intentionally excluded.

- [ ] **Step 4: PRESENTATION_AUDIT.md** — add the new page to the page tour and the "cosa fa" summary.

- [ ] **Step 5: Commit the pre-v2 snapshot**

```bash
git add -A
git commit -m "docs(pre-v2): document economic layer across README/TASKS/PRD/audit before implementation"
git tag pre-v2
```

Expected: `git tag` lists `pre-v2`.

---

## Task 1 (TASK-042): Economic config defaults + constants

**Files:**
- Modify: `config/defaults.yaml` (append economic block)
- Modify: `src/utils/constants.py` (append economic recommendation labels)
- Test: `tests/test_economic_engine.py` (create; first assertion is constants/config presence)

- [ ] **Step 1: Append to `config/defaults.yaml`**

```yaml
# --- Economic layer (v2) defaults ---
standard_hourly_cost: 18.0
overtime_multiplier: 1.25
fixed_setup_cost: 0.0
overhead_percentage: 0.10
currency: "EUR"
reallocation_material_threshold_eur: 500.0
```

- [ ] **Step 2: Append to `src/utils/constants.py`**

```python
# --- Economic recommendation labels (v2, cost-driven) ---
ECON_ACCEPT: str = "ACCEPT"
ECON_ACCEPT_OVERTIME: str = "ACCEPT WITH OVERTIME"
ECON_REALLOCATE: str = "REALLOCATE"
ECON_POSTPONE: str = "POSTPONE"
ECON_REJECT: str = "REJECT"

ALL_ECON_RECOMMENDATIONS: tuple[str, ...] = (
    ECON_ACCEPT,
    ECON_ACCEPT_OVERTIME,
    ECON_REALLOCATE,
    ECON_POSTPONE,
    ECON_REJECT,
)

# Economic status for cost cards
ECON_STATUS_OK: str = "safe"
ECON_STATUS_WATCH: str = "at_risk"
ECON_STATUS_BAD: str = "critical"
```

- [ ] **Step 3: Write the failing test** (`tests/test_economic_engine.py`)

```python
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
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/test_economic_engine.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add config/defaults.yaml src/utils/constants.py tests/test_economic_engine.py
git commit -m "feat(TASK-042): economic config defaults + recommendation constants"
```

---

## Task 2 (TASK-043): Extend demo data with an economic_layer sheet

**Files:**
- Modify: `scripts/build_sample_data.py` (add `_economic_layer_rows` + write sheet)
- Regenerate: `data/sample/sample_planning.xlsx`

**Rationale:** Give the small demo the same sourcing path as the real workbook — an `economic_layer` sheet with derived, differentiated values (per-lab hourly cost, per-lab overtime multiplier, per-product overhead %, per-order setup cost). Values are demo-realistic, not config defaults, so the demo exercises lab comparison and reallocation.

- [ ] **Step 1: Add `_economic_layer_rows()` to `scripts/build_sample_data.py`**

```python
def _economic_layer_rows() -> list[list]:
    # Per-lab hourly cost & overtime multiplier; per-product overhead %; per-order setup.
    # Derived demo values (L1 cheaper than L2 for Giacca-heavy load; differentiated).
    header = [
        "order_id", "assigned_lab", "product_type",
        "standard_hourly_cost_eur", "overtime_multiplier",
        "overhead_pct", "setup_cost_eur",
    ]
    rows: list[list] = [
        ["ORD-0001", "L1", "Giacca",    18.0, 1.25, 0.10, 120.0],
        ["ORD-0002", "L1", "Pantalone", 18.0, 1.25, 0.12,  80.0],
        ["ORD-0003", "L2", "Giacca",    21.5, 1.30, 0.10, 150.0],
        ["ORD-0004", "L2", "Pantalone", 21.5, 1.30, 0.12,  60.0],
        ["ORD-0005", "L1", "Giacca",    18.0, 1.25, 0.10, 100.0],
    ]
    return [header] + rows
```

- [ ] **Step 2: Register the sheet in `build_workbook`** — add to the loop tuple:

```python
    for name, rows in (
        ("product_matrix", _product_matrix_rows()),
        ("labs",            _labs_rows()),
        ("phase_capacity",  _phase_capacity_rows()),
        ("economic_layer",  _economic_layer_rows()),
    ):
```

- [ ] **Step 3: Regenerate the sample workbook**

Run: `.venv/bin/python scripts/build_sample_data.py`
Expected: `Wrote data/sample/sample_planning.xlsx`

- [ ] **Step 4: Verify the new sheet reads back**

Run:
```bash
.venv/bin/python -c "import pandas as pd; print(pd.read_excel('data/sample/sample_planning.xlsx', sheet_name='economic_layer').to_string())"
```
Expected: 5 rows with the economic columns.

- [ ] **Step 5: Verify the existing pipeline is unaffected (the canonical 4 sheets still parse)**

Run: `.venv/bin/python -m pytest tests/ -q`
Expected: 45 passed (43 baseline + 2 from Task 1).

- [ ] **Step 6: Commit**

```bash
git add scripts/build_sample_data.py data/sample/sample_planning.xlsx
git commit -m "feat(TASK-043): add economic_layer sheet to demo dataset (derived realistic values)"
```

---

## Task 3 (TASK-044): Economic input loader

**Files:**
- Create: `src/parsers/economic_inputs.py`
- Test: `tests/test_economic_inputs.py`

**Contract:** `load_economic_inputs(raw: dict[str, pd.DataFrame]) -> EconomicInputs` where
`EconomicInputs` is a dataclass holding lookup maps + a `uses_default` flag.
Sources from the `economic_layer` sheet when present (combining assigned+alternative
lab cost columns to cover all labs), else config defaults.

- [ ] **Step 1: Write the failing test** (`tests/test_economic_inputs.py`)

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_economic_inputs.py -v`
Expected: FAIL (`ModuleNotFoundError: src.parsers.economic_inputs`).

- [ ] **Step 3: Implement `src/parsers/economic_inputs.py`**

```python
"""Economic input sourcing (PRD v2 §5/§6).

Sources per-lab hourly cost & overtime multiplier, per-product overhead %,
and per-order setup cost from an `economic_layer` sheet when present; otherwise
falls back to config defaults (flagged via `uses_default`). No numeric literals:
every fallback comes from config/defaults.yaml.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from src.utils.config import get_default

_ECON_SHEET_NAMES = ("economic_layer", "economic", "economics")


@dataclass
class EconomicInputs:
    _hourly: dict[str, float] = field(default_factory=dict)
    _overtime: dict[str, float] = field(default_factory=dict)
    _overhead: dict[str, float] = field(default_factory=dict)
    _setup: dict[str, float] = field(default_factory=dict)
    uses_default: bool = True

    # Config fallbacks (read once)
    _def_hourly: float = field(default_factory=lambda: float(get_default("standard_hourly_cost")))
    _def_overtime: float = field(default_factory=lambda: float(get_default("overtime_multiplier")))
    _def_overhead: float = field(default_factory=lambda: float(get_default("overhead_percentage")))
    _def_setup: float = field(default_factory=lambda: float(get_default("fixed_setup_cost")))

    def hourly_cost(self, lab_id) -> float:
        return float(self._hourly.get(str(lab_id), self._def_hourly))

    def overtime_multiplier(self, lab_id) -> float:
        return float(self._overtime.get(str(lab_id), self._def_overtime))

    def overhead_pct(self, product_type) -> float:
        return float(self._overhead.get(str(product_type), self._def_overhead))

    def setup_cost(self, order_id) -> float:
        return float(self._setup.get(str(order_id), self._def_setup))


def _find_econ_sheet(raw: dict[str, pd.DataFrame]) -> pd.DataFrame | None:
    if not raw:
        return None
    for k, v in raw.items():
        if str(k).strip().lower() in _ECON_SHEET_NAMES and v is not None and not v.empty:
            return v
    return None


def load_economic_inputs(raw: dict[str, pd.DataFrame]) -> EconomicInputs:
    sheet = _find_econ_sheet(raw)
    if sheet is None:
        return EconomicInputs(uses_default=True)

    df = sheet.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    hourly: dict[str, float] = {}
    overtime: dict[str, float] = {}
    overhead: dict[str, float] = {}
    setup: dict[str, float] = {}

    def _num(v):
        try:
            f = float(v)
            return f if pd.notna(f) else None
        except (TypeError, ValueError):
            return None

    for _, row in df.iterrows():
        lab = row.get("assigned_lab")
        if lab is not None and pd.notna(lab):
            hc = _num(row.get("standard_hourly_cost_eur"))
            if hc is not None:
                hourly[str(lab)] = hc
            ot = _num(row.get("overtime_multiplier"))
            if ot is not None:
                overtime[str(lab)] = ot
        # Alternative lab cost columns extend lab coverage
        alt = row.get("alternative_lab")
        if alt is not None and pd.notna(alt):
            ahc = _num(row.get("alternative_hourly_cost_eur"))
            if ahc is not None:
                hourly.setdefault(str(alt), ahc)
        prod = row.get("product_type")
        if prod is not None and pd.notna(prod):
            oh = _num(row.get("overhead_pct"))
            if oh is not None:
                overhead[str(prod)] = oh
        oid = row.get("order_id")
        if oid is not None and pd.notna(oid):
            sc = _num(row.get("setup_cost_eur"))
            if sc is not None:
                setup[str(oid)] = sc

    return EconomicInputs(
        _hourly=hourly,
        _overtime=overtime,
        _overhead=overhead,
        _setup=setup,
        uses_default=False,
    )


__all__ = ["EconomicInputs", "load_economic_inputs"]
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/test_economic_inputs.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/parsers/economic_inputs.py tests/test_economic_inputs.py
git commit -m "feat(TASK-044): economic input loader (economic_layer sheet -> maps, config fallback)"
```

---

## Task 4 (TASK-045): Economic engine — pure formulas + results, with golden test

**Files:**
- Create: `src/engines/economic_engine.py`
- Test: append to `tests/test_economic_engine.py`

- [ ] **Step 1: Write the failing formula + golden tests** (append to `tests/test_economic_engine.py`)

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_economic_engine.py -k "labour or overhead or total or excess or overtime or golden" -v`
Expected: FAIL (`ModuleNotFoundError: src.engines.economic_engine`).

- [ ] **Step 3: Implement formulas in `src/engines/economic_engine.py`**

```python
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
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/test_economic_engine.py -v`
Expected: all green including `test_golden_reproduces_workbook_to_the_cent`.

- [ ] **Step 5: Commit**

```bash
git add src/engines/economic_engine.py tests/test_economic_engine.py
git commit -m "feat(TASK-045): economic engine pure formulas + golden test vs workbook"
```

---

## Task 5 (TASK-046): `compute_economic_results` + 5-type cost-driven recommendation

**Files:**
- Modify: `src/engines/economic_engine.py` (add per-order cost helper + `compute_economic_results` + recommendation)
- Test: append to `tests/test_economic_engine.py`

**Per-order cost helper** computes the total estimated cost of an order if run on a
given lab, using `required_hours` from capacity results, that lab's hourly cost &
overtime multiplier, the product's overhead %, and the order's setup cost.

**Recommendation (first match wins):**
1. `REJECT` — operational rec is REJECT (or utilization ∞ / no capacity) **and** no alternative lab.
2. `POSTPONE` — overtime required (`overtime_hours > 0`) **and** a deadline-infeasible operational signal exists.
3. `ACCEPT WITH OVERTIME` — overtime required, lab allows overtime, no materially cheaper alternative.
4. `REALLOCATE` — `cost_delta_if_reallocated <= -threshold` (alternative materially cheaper).
5. `ACCEPT` — otherwise.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_economic_engine.py`)

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_economic_engine.py -k "compute or reallocate or accept or reason" -v`
Expected: FAIL (`compute_economic_results` not defined / import error).

- [ ] **Step 3: Implement in `src/engines/economic_engine.py`** (add below the formula functions; add imports `math`, `find_alternative_lab` already imported)

```python
def _order_cost_on_lab(
    required_hours: float,
    available_hours: float,
    lab_id: str,
    product_type: str,
    order_id: str,
    econ: EconomicInputs,
    overtime_allowed: bool,
) -> tuple[float, float, float, float, float, float]:
    """Return (labour, excess_h, ot_cost, setup, overhead, total) for an order on a lab."""
    hourly = econ.hourly_cost(lab_id)
    labour = standard_labour_cost(required_hours, hourly)
    exc = excess_hours(required_hours, available_hours)
    ot = overtime_cost(exc, hourly, econ.overtime_multiplier(lab_id)) if (exc > 0 and overtime_allowed) else 0.0
    setup = econ.setup_cost(order_id)
    oh = overhead_cost(labour, ot, setup, econ.overhead_pct(product_type))
    total = total_estimated_cost(labour, ot, setup, oh)
    return labour, exc, ot, setup, oh, total


def _overtime_allowed_for_lab(labs_df: pd.DataFrame | None, lab_id: str) -> bool:
    if labs_df is None or labs_df.empty or "lab_id" not in labs_df.columns:
        return False
    match = labs_df[labs_df["lab_id"].astype(str) == str(lab_id)]
    if match.empty or "overtime_allowed" not in match.columns:
        return False
    return bool(match.iloc[0]["overtime_allowed"])


def _available_hours_for_order(group: pd.DataFrame) -> float:
    """Sum available_minutes across the order's phases / 60. inf-safe."""
    vals = [v for v in group["available_minutes"].tolist() if math.isfinite(v)]
    return sum(vals) / 60.0 if vals else 0.0


def compute_economic_results(
    capacity_results_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    phase_capacity_df: pd.DataFrame,
    product_matrix_df: pd.DataFrame,
    econ: EconomicInputs,
    labs_df: pd.DataFrame | None = None,
    operational_recs_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    if capacity_results_df is None or capacity_results_df.empty:
        return pd.DataFrame(columns=ECONOMIC_RESULTS_COLS)

    threshold = float(get_default("reallocation_material_threshold_eur"))
    orders_by_id = orders_df.set_index("order_id") if orders_df is not None and not orders_df.empty else None
    rec_by_order = (
        operational_recs_df.set_index("order_id")
        if operational_recs_df is not None and not operational_recs_df.empty
        else None
    )
    work = capacity_results_df[capacity_results_df["phase_name"] != "<unknown product>"]

    rows: list[dict] = []
    for order_id, group in work.groupby("order_id"):
        lab = str(group["assigned_lab"].iloc[0])
        product_type = str(group["product_type"].iloc[0])
        quantity = int(group["quantity"].iloc[0]) if "quantity" in group else 0
        required_hours = float(group["required_minutes"].sum()) / 60.0
        available_hours = _available_hours_for_order(group)
        ot_allowed = _overtime_allowed_for_lab(labs_df, lab)

        labour, exc, ot, setup, oh, total = _order_cost_on_lab(
            required_hours, available_hours, lab, product_type, str(order_id), econ, ot_allowed
        )
        cpg = (total / quantity) if quantity > 0 else float("nan")

        # Alternative lab cost
        order_row = orders_by_id.loc[order_id] if orders_by_id is not None and order_id in orders_by_id.index else None
        alt_lab = (
            find_alternative_lab(order_row, lab, phase_capacity_df, product_matrix_df)
            if order_row is not None else None
        )
        if alt_lab:
            _, _, _, _, _, alt_total = _order_cost_on_lab(
                required_hours, available_hours, alt_lab, product_type, str(order_id), econ,
                _overtime_allowed_for_lab(labs_df, alt_lab),
            )
            cost_delta = alt_total - total
        else:
            alt_total = float("nan")
            cost_delta = float("nan")

        # Operational signals
        op_rec = str(rec_by_order.loc[order_id]["recommendation"]) if rec_by_order is not None and order_id in rec_by_order.index else None
        infeasible = (
            (op_rec == REC_REJECT)
            or (~group["utilization_rate"].apply(math.isfinite)).any()
        )
        has_deadline_issue = op_rec in {"POSTPONE"} or (group["utilization_rate"].replace([math.inf], 9e9) > 1.0).any()

        # ---- Decision tree (5 cost-driven types) ----
        if infeasible and not alt_lab:
            rec = ECON_REJECT
            reason = "Operationally infeasible and no alternative lab with capacity."
        elif exc > 0 and has_deadline_issue:
            rec = ECON_POSTPONE
            reason = f"Overtime of {exc:.1f}h required to hit the deadline; postponing avoids the premium."
        elif exc > 0 and ot_allowed and not (alt_lab and cost_delta <= -threshold):
            rec = ECON_ACCEPT_OVERTIME
            reason = f"Overtime of {exc:.1f}h required (+€{ot:,.0f}); lab permits overtime."
        elif alt_lab and math.isfinite(cost_delta) and cost_delta <= -threshold:
            rec = ECON_REALLOCATE
            reason = f"Lab '{alt_lab}' is materially cheaper (€{cost_delta:,.0f} vs current)."
        else:
            rec = ECON_ACCEPT
            reason = f"Estimated cost €{total:,.0f}; no materially cheaper lab and no overtime."

        rows.append({
            "order_id": order_id,
            "assigned_lab": lab,
            "product_type": product_type,
            "quantity": quantity,
            "required_hours": required_hours,
            "available_hours": available_hours,
            "standard_labour_cost": labour,
            "overtime_hours": exc if ot_allowed else 0.0,
            "overtime_cost": ot,
            "setup_cost": setup,
            "overhead_cost": oh,
            "total_estimated_cost": total,
            "cost_per_garment_internal": cpg,
            "alternative_lab": alt_lab,
            "alternative_total_cost": alt_total,
            "cost_delta_if_reallocated": cost_delta,
            "economic_recommendation": rec,
            "economic_reason": reason,
            "uses_default_costs": bool(econ.uses_default),
        })

    return pd.DataFrame(rows, columns=ECONOMIC_RESULTS_COLS)
```

- [ ] **Step 4: Run the full economic test file**

Run: `.venv/bin/python -m pytest tests/test_economic_engine.py -v`
Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add src/engines/economic_engine.py tests/test_economic_engine.py
git commit -m "feat(TASK-046): compute_economic_results + 5-type cost-driven recommendation"
```

---

## Task 6 (TASK-047): Cost-vs-Risk chart component

**Files:**
- Modify: `src/components/charts.py` (add `cost_vs_risk_scatter`)
- Test: append to `tests/test_charts_economic.py` (create)

- [ ] **Step 1: Write the failing test** (`tests/test_charts_economic.py`)

```python
import pandas as pd
import plotly.graph_objects as go

from src.components.charts import cost_vs_risk_scatter


def test_cost_vs_risk_returns_figure_with_points():
    df = pd.DataFrame({
        "label": ["L1", "L2"],
        "estimated_cost": [2000.0, 2400.0],
        "utilization": [0.96, 0.78],
    })
    fig = cost_vs_risk_scatter(df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_cost_vs_risk_empty_is_safe():
    fig = cost_vs_risk_scatter(pd.DataFrame(columns=["label", "estimated_cost", "utilization"]))
    assert isinstance(fig, go.Figure)
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_charts_economic.py -v`
Expected: FAIL (`cannot import name 'cost_vs_risk_scatter'`).

- [ ] **Step 3: Add to `src/components/charts.py`** (before `__all__`; extend `__all__`)

```python
def cost_vs_risk_scatter(df: pd.DataFrame) -> go.Figure:
    """Scatter of estimated cost (x) vs utilization/operational risk (y).

    Each point is a lab or allocation scenario. Color by utilization status.
    """
    if df is None or df.empty:
        return _empty_figure("No cost/risk data yet")
    work = df.copy()
    colors = [STATUS_COLORS[utilization_status(v)] for v in work["utilization"].values]
    fig = go.Figure(
        go.Scatter(
            x=work["estimated_cost"].values,
            y=work["utilization"].values,
            mode="markers+text",
            text=work["label"].astype(str).values,
            textposition="top center",
            marker=dict(size=14, color=colors),
            hovertemplate="%{text}<br>cost €%{x:,.0f}<br>util %{y:.0%}<extra></extra>",
        )
    )
    fig.add_hline(y=CRITICAL_UTILIZATION_THRESHOLD, line=dict(color="#9CA3AF", width=1, dash="dash"))
    fig = _base_layout(fig, title="Cost vs operational risk")
    fig.update_yaxes(tickformat=".0%")
    fig.update_xaxes(title="Estimated cost (€)")
    return fig
```

Update the last line:
```python
__all__ = ["phase_utilization_bar", "lab_phase_capacity_gap_bar", "cost_vs_risk_scatter"]
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/test_charts_economic.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/components/charts.py tests/test_charts_economic.py
git commit -m "feat(TASK-047): cost-vs-risk scatter chart component"
```

---

## Task 7 (TASK-048): Cost Feasibility page

**Files:**
- Create: `src/ui/pages/cost_feasibility.py`

**Mirror** `capacity_dashboard.py`'s pipeline; add economic results, KPIs, breakdown,
lab comparison, cost-vs-risk, alerts, combined recommendation. Page reads
`st.session_state["data"]["economic_inputs"]` (wired in Task 8).

- [ ] **Step 1: Create `src/ui/pages/cost_feasibility.py`**

```python
"""Page 7 — Cost Feasibility Dashboard (Economic Layer v2, cost-focused)."""
from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from src.components.alerts import render_recommendation_panel
from src.components.charts import cost_vs_risk_scatter
from src.components.kpi_cards import kpi_row
from src.engines.bottleneck_engine import identify_bottlenecks
from src.engines.capacity_engine import aggregate_lab_phase, compute_capacity_results
from src.engines.economic_engine import compute_economic_results
from src.engines.recommendation_engine import generate_recommendations
from src.engines.scenario_engine import apply_scenario
from src.engines.stress_engine import evaluate_all_stress
from src.parsers.economic_inputs import EconomicInputs
from src.utils.config import get_default
from src.utils.formatting import fmt_int


def _eur(v: float) -> str:
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return "—"
    return f"€{v:,.0f}"


def render() -> None:
    st.title("Cost Feasibility Dashboard")
    st.caption(
        "Economic layer — estimates production cost, overtime cost and the cost "
        "impact of reallocation. Cost-focused: margin/profitability are out of scope."
    )

    data = st.session_state["data"]
    scenario = st.session_state["scenario"]
    planning_days = st.session_state["planning_days"]

    orders_df = data["orders"]
    pm_df = data["product_matrix"]
    labs_df = data["labs"]
    pc_df = data["phase_capacity"]
    econ: EconomicInputs = data.get("economic_inputs") or EconomicInputs(uses_default=True)

    orders_scn, pc_scn = apply_scenario(orders_df, pc_df, scenario)
    cap = compute_capacity_results(orders_scn, pm_df, labs_df, pc_scn, planning_days=planning_days)
    lab_phase = aggregate_lab_phase(cap)
    cap, _ = identify_bottlenecks(cap, lab_phase)
    stress = evaluate_all_stress(orders_scn, cap, labs_df, pc_scn, scenario, lab_phase_df=lab_phase)
    op_recs = generate_recommendations(cap, stress, orders_scn, pc_scn, pm_df)

    econ_df = compute_economic_results(cap, orders_scn, pc_scn, pm_df, econ, labs_df=labs_df, operational_recs_df=op_recs)

    if econ_df.empty:
        st.info("No economic results — load data on the Upload page.")
        return

    if econ.uses_default:
        st.warning("Some cost values are estimated using default assumptions.")

    # --- Aggregate KPIs (cost-focused) ---
    total_cost = float(econ_df["total_estimated_cost"].sum())
    total_overtime = float(econ_df["overtime_cost"].sum())
    total_labour = float(econ_df["standard_labour_cost"].sum())
    realloc_saving = float(
        econ_df.loc[econ_df["cost_delta_if_reallocated"] < 0, "cost_delta_if_reallocated"].sum()
    )
    kpi_row([
        {"label": "Total estimated production cost", "value": _eur(total_cost), "status": "neutral"},
        {"label": "Overtime cost", "value": _eur(total_overtime), "status": "critical" if total_overtime > 0 else "safe"},
        {"label": "Standard labour cost", "value": _eur(total_labour), "status": "neutral"},
        {"label": "Cost impact of reallocation", "value": _eur(realloc_saving), "status": "at_risk" if realloc_saving < 0 else "safe"},
    ])

    # --- Order selector ---
    order_ids = econ_df["order_id"].tolist()
    sel = st.selectbox("Focus order", order_ids)
    row = econ_df[econ_df["order_id"] == sel].iloc[0]

    # --- Cost breakdown table ---
    st.subheader("Order cost breakdown")
    total = row["total_estimated_cost"] or 0.0
    components = [
        ("Standard labour", row["standard_labour_cost"]),
        ("Overtime", row["overtime_cost"]),
        ("Setup", row["setup_cost"]),
        ("Overhead", row["overhead_cost"]),
        ("Total estimated cost", total),
    ]
    breakdown = pd.DataFrame(
        [
            {"Cost component": name, "Amount (€)": f"{amt:,.2f}",
             "% of total": (f"{(amt / total * 100):.1f}%" if total and name != "Total estimated cost" else ("100.0%" if name == "Total estimated cost" else "—"))}
            for name, amt in components
        ]
    )
    st.dataframe(breakdown, hide_index=True, width="stretch")

    # --- Lab comparison ---
    st.subheader("Lab comparison")
    cur_lab = row["assigned_lab"]
    alt_lab = row["alternative_lab"]
    lab_rows = [{"Lab": cur_lab, "Estimated cost (€)": f"{row['total_estimated_cost']:,.0f}",
                 "Role": "current", "Cost delta (€)": "—"}]
    if alt_lab and isinstance(alt_lab, str):
        lab_rows.append({"Lab": alt_lab, "Estimated cost (€)": f"{row['alternative_total_cost']:,.0f}",
                         "Role": "alternative", "Cost delta (€)": f"{row['cost_delta_if_reallocated']:,.0f}"})
    st.dataframe(pd.DataFrame(lab_rows), hide_index=True, width="stretch")

    # --- Cost vs risk chart (current vs alternative) ---
    st.subheader("Cost vs operational risk")
    util_lookup = (
        lab_phase.groupby("assigned_lab")["utilization_rate"]
        .max().replace([math.inf], 1.5).to_dict()
        if not lab_phase.empty else {}
    )
    pts = [{"label": str(cur_lab), "estimated_cost": float(row["total_estimated_cost"]), "utilization": float(util_lookup.get(cur_lab, 0.0))}]
    if alt_lab and isinstance(alt_lab, str):
        pts.append({"label": str(alt_lab), "estimated_cost": float(row["alternative_total_cost"]), "utilization": float(util_lookup.get(alt_lab, 0.0))})
    st.plotly_chart(cost_vs_risk_scatter(pd.DataFrame(pts)), width="stretch")

    # --- Economic alerts ---
    st.subheader("Economic alerts")
    alerts_shown = False
    if row["overtime_cost"] and row["overtime_cost"] > 0:
        st.warning(f"Overtime increases production cost by {_eur(row['overtime_cost'])}.")
        alerts_shown = True
    if isinstance(alt_lab, str) and math.isfinite(row["cost_delta_if_reallocated"]) and row["cost_delta_if_reallocated"] < 0:
        st.info(f"Alternative lab '{alt_lab}' reduces estimated cost by {_eur(-row['cost_delta_if_reallocated'])}.")
        alerts_shown = True
    if row["uses_default_costs"]:
        st.warning("Cost values for this order use default assumptions.")
        alerts_shown = True
    if not alerts_shown:
        st.success("No economic alerts for this order.")

    # --- Combined recommendation ---
    st.subheader("Recommendation (operational + economic)")
    op_row = op_recs[op_recs["order_id"] == sel]
    op_label = str(op_row.iloc[0]["recommendation"]) if not op_row.empty else "—"
    st.markdown(f"**Operational:** {op_label}  ·  **Economic:** {row['economic_recommendation']}")
    combined = pd.DataFrame([{
        "order_id": sel,
        "recommendation": row["economic_recommendation"],
        "severity": "low" if row["economic_recommendation"] == "ACCEPT" else "medium",
        "reasons": [row["economic_reason"], f"Operational layer: {op_label}"],
        "suggested_actions": [
            f"Reallocate to '{alt_lab}'" if row["economic_recommendation"] == "REALLOCATE" and isinstance(alt_lab, str)
            else "Proceed as scheduled" if row["economic_recommendation"] == "ACCEPT"
            else row["economic_recommendation"].title()
        ],
    }])
    render_recommendation_panel(combined)
```

- [ ] **Step 2: Smoke-import the page**

Run: `.venv/bin/python -c "import src.ui.pages.cost_feasibility as p; print(hasattr(p, 'render'))"`
Expected: `True`

- [ ] **Step 3: Commit**

```bash
git add src/ui/pages/cost_feasibility.py
git commit -m "feat(TASK-048): Cost Feasibility page (KPIs, breakdown, lab comparison, cost-vs-risk, alerts, combined rec)"
```

---

## Task 8 (TASK-049): Wire economic inputs into session + register page in nav

**Files:**
- Modify: `src/ui/pages/upload.py` (store `economic_inputs` into session data)
- Modify: `app.py` (import + register page + data-gate)

- [ ] **Step 1: In `src/ui/pages/upload.py`,** after the raw workbook is parsed and `normalize_all` result is stored, also load economic inputs from the SAME raw dict and attach them. Locate the spot where the normalized `result` dict is saved to `st.session_state["data"]` and add, before saving:

```python
from src.parsers.economic_inputs import load_economic_inputs
...
# raw_sheets is the dict returned by parse_excel(...) for this upload/demo
result["economic_inputs"] = load_economic_inputs(raw_sheets)
```

> If `upload.py` does not currently keep the raw dict around, capture it: where it calls `parse_excel(...)`, assign to `raw_sheets` and pass the same variable to `normalize_all`. For demo mode it parses `data/sample/sample_planning.xlsx` — that now has an `economic_layer` sheet (Task 2).

- [ ] **Step 2: Register the page in `app.py`** — add the import and PAGES entry (after `scenario_testing`, before `future_ai`):

```python
from src.ui.pages import (
    capacity_dashboard,
    cost_feasibility,
    future_ai,
    overview,
    phase_saturation,
    scenario_testing,
    timeline as timeline_page,
    upload,
)
```

```python
PAGES: dict[str, callable] = {
    "Overview": overview.render,
    "Upload Data": upload.render,
    "Capacity Dashboard": capacity_dashboard.render,
    "Phase Saturation": phase_saturation.render,
    "Timeline": timeline_page.render,
    "Scenario Testing": scenario_testing.render,
    "Cost Feasibility Dashboard": cost_feasibility.render,
    "Future AI Layer": future_ai.render,
}
```

```python
_DATA_GATED_PAGES = {
    "Capacity Dashboard",
    "Phase Saturation",
    "Timeline",
    "Scenario Testing",
    "Cost Feasibility Dashboard",
}
```

- [ ] **Step 3: End-to-end check (both datasets) — write a throwaway script and run it**

Run:
```bash
.venv/bin/python - <<'PY'
import warnings; warnings.filterwarnings("ignore")
from src.parsers.excel_parser import parse_excel
from src.parsers.normalizer import normalize_all
from src.parsers.economic_inputs import load_economic_inputs
from src.engines.scenario_engine import ScenarioInputs, apply_scenario
from src.engines.capacity_engine import compute_capacity_results, aggregate_lab_phase
from src.engines.bottleneck_engine import identify_bottlenecks
from src.engines.stress_engine import evaluate_all_stress
from src.engines.recommendation_engine import generate_recommendations
from src.engines.economic_engine import compute_economic_results

for path in ("data/sample/sample_planning.xlsx", "data/sample/clothing_production_planning_database_with_economic_layer.xlsx"):
    raw = parse_excel(path)
    d = normalize_all(raw)
    ei = load_economic_inputs(raw)
    o, pc = apply_scenario(d["orders"], d["phase_capacity"], ScenarioInputs())
    cap = compute_capacity_results(o, d["product_matrix"], d["labs"], pc, planning_days=5)
    lp = aggregate_lab_phase(cap); cap, _ = identify_bottlenecks(cap, lp)
    stress = evaluate_all_stress(o, cap, d["labs"], pc, ScenarioInputs(), lab_phase_df=lp)
    recs = generate_recommendations(cap, stress, o, pc, d["product_matrix"])
    econ = compute_economic_results(cap, o, pc, d["product_matrix"], ei, labs_df=d["labs"], operational_recs_df=recs)
    print(path.split("/")[-1], "| econ rows:", len(econ), "| uses_default:", ei.uses_default,
          "| recs:", econ["economic_recommendation"].value_counts().to_dict())
PY
```
Expected: both datasets produce economic rows with no exception; the big workbook shows a mix of `ACCEPT` and `REALLOCATE`.

- [ ] **Step 4: Commit**

```bash
git add app.py src/ui/pages/upload.py
git commit -m "feat(TASK-049): register Cost Feasibility page + wire economic inputs into session"
```

---

## Task 9 (TASK-050): Final verification + docs close-out

**Files:**
- Modify: `README.md`, `docs/TASKS.md` (flip PHASE 10 statuses to DONE)

- [ ] **Step 1: Run the full suite**

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: all green (45 baseline+Task1 → grows to ~60 with the new economic tests).

- [ ] **Step 2: App smoke test (headless, boots without error)**

Run:
```bash
.venv/bin/python -m streamlit run app.py --server.headless true --server.port 8599 &
sleep 8
curl -s -o /dev/null -w "%{http_code}" http://localhost:8599/ ; echo
kill %1
```
Expected: `200`.

- [ ] **Step 3: Manual visual check (user-driven)** — `streamlit run app.py`, open **Cost Feasibility Dashboard** with both demo and the economic workbook; confirm KPIs, breakdown, lab comparison, chart, alerts, and combined recommendation render.

- [ ] **Step 4: Flip TASK-042…TASK-050 to DONE in `docs/TASKS.md`; finalize README economic subsection.**

- [ ] **Step 5: Commit + tag v2**

```bash
git add -A
git commit -m "feat(TASK-050): economic layer complete — docs finalized, full suite green"
git tag v2
```

- [ ] **Step 6: Push (triggers Railway auto-deploy)** — only on user's go.

```bash
git push origin main --tags
```

- [ ] **Step 7: Verify Railway deploy** — use the `use-railway` skill to check deployment status/logs and confirm the service is live.

---

## Self-review notes

- **Spec coverage:** §3 architecture → Tasks 1–8; §5 input sourcing → Task 3; §6 schema → Task 5 (`ECONOMIC_RESULTS_COLS`); §7 formulas → Task 4; §8 5-type recommendation → Task 5; §9 page/components → Tasks 6–7; §10 edge cases → guarded in Task 5 (quantity 0 → NaN cpg; no alt lab → NaN delta; inf-safe available hours); §11 testing → Tasks 1,3,4,5,6; §12 housekeeping → Task 0 + 9-pre + 9.
- **Margin exclusion:** no margin/revenue columns produced; `cost_per_garment_internal` computed but never shown as KPI.
- **0 hardcode:** every numeric default read via `get_default`; the only literals in code are the demo-data values in `build_sample_data.py` (data, not logic).
- **Type consistency:** `EconomicInputs` methods (`hourly_cost`, `overtime_multiplier`, `overhead_pct`, `setup_cost`, `uses_default`) used identically in Tasks 3, 5, 7; `compute_economic_results` signature consistent across Tasks 5, 7, 8.
