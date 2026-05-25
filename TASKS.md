# TASKS.md

## Sustainable Capacity Planning & Operational Decision Support Platform
### Iterative Execution Task List — MVP

> **Source of truth:** `MASTER_PRD_v2_EXECUTION.md`
> **Execution model:** Tasks are atomic, dependency-ordered, and loop-compatible. Each task should be completable in one focused iteration. After completing a task, update its `Status` to `DONE` and commit before moving on.
>
> **Status values:** `TODO` · `IN_PROGRESS` · `BLOCKED` · `DONE` · `CODE_READY` (implementation complete, runtime verification pending dependency install)
>
> **Architectural rule reminder (from PRD §15):** all code lives under `/src` split into `parsers/`, `engines/`, `components/`, `utils/`. Streamlit entry is `app.py` at project root. No databases, no auth, no cloud — local Streamlit only.

---

# PHASE 1 — Foundation

## TASK-001 — Create Project Folder Structure

### Description
Initialize the directory tree exactly as defined in PRD §15. Create empty `__init__.py` files inside every Python package directory so imports resolve cleanly.

### Dependencies
None

### Expected Output
- Directories: `data/sample/`, `data/uploaded/`, `config/`, `src/parsers/`, `src/engines/`, `src/components/`, `src/utils/`, `assets/mockups/`, `tests/`.
- Empty `__init__.py` in `src/`, `src/parsers/`, `src/engines/`, `src/components/`, `src/utils/`, `tests/`.
- `.gitkeep` placeholders in `data/uploaded/` and `assets/mockups/`.

### Acceptance Criteria
- `find . -type d` shows all directories listed above.
- `python -c "import src, src.parsers, src.engines, src.components, src.utils"` runs without error.
- No source code yet — structure only.

### Status
DONE

---

## TASK-002 — Add requirements.txt

### Description
Pin the runtime dependencies needed for the entire MVP stack so a fresh environment can be reproduced with one command.

### Dependencies
TASK-001

### Expected Output
`requirements.txt` at project root containing:
```
streamlit>=1.30
pandas>=2.0
numpy>=1.24
plotly>=5.18
openpyxl>=3.1
pyyaml>=6.0
pytest>=7.4
```

### Acceptance Criteria
- `pip install -r requirements.txt` succeeds in a clean venv.
- `python -c "import streamlit, pandas, numpy, plotly, openpyxl, yaml, pytest"` runs without error.

### Status
DONE

---

## TASK-003 — Create Constants Module

### Description
Create a single source of truth for thresholds, status colors, recommendation labels, and column-name constants used across engines and UI. Centralizes magic numbers so no engine hardcodes thresholds (PRD §8).

### Dependencies
TASK-001

### Expected Output
`src/utils/constants.py` defining:
- Threshold constants: `SAFE_UTILIZATION_THRESHOLD = 0.85`, `CRITICAL_UTILIZATION_THRESHOLD = 1.00`, `PHASE_STRESS_THRESHOLD = 0.90`, `MAX_PARALLEL_ORDERS_PER_LAB = 2`.
- Status enum/strings: `STATUS_SAFE`, `STATUS_AT_RISK`, `STATUS_CRITICAL`, `STATUS_NEUTRAL`.
- Status color map: `STATUS_COLORS = {"safe": "#22C55E", "at_risk": "#F59E0B", "critical": "#EF4444", "neutral": "#6B7280"}`.
- Recommendation labels: `REC_ACCEPT`, `REC_AT_RISK`, `REC_REALLOCATE`, `REC_SPLIT`, `REC_POSTPONE`, `REC_REJECT`.
- Severity levels: `SEVERITY_LOW`, `SEVERITY_MEDIUM`, `SEVERITY_HIGH`.

### Acceptance Criteria
- All constants are importable: `from src.utils.constants import SAFE_UTILIZATION_THRESHOLD`.
- No threshold literal (`0.85`, `1.00`, `0.90`) appears anywhere else in the codebase in later tasks.

### Status
DONE

---

## TASK-004 — Create Default Configuration File

### Description
Externalize the default operational values from PRD §8 into a YAML file so they can be tuned without code changes.

### Dependencies
TASK-001

### Expected Output
`config/defaults.yaml`:
```yaml
default_lab_id: "Default Lab"
working_hours_per_day: 8
working_days_per_week: 5
default_efficiency: 0.75
machine_uptime: 0.90
safe_utilization_threshold: 0.85
critical_utilization_threshold: 1.00
phase_stress_threshold: 0.90
max_parallel_orders_per_lab: 2
max_weekly_hours: 48
overtime_allowed: false
```

### Acceptance Criteria
- File parses successfully with `yaml.safe_load`.
- Every key from PRD §8 is present with matching value/type.

### Status
DONE

---

## TASK-005 — Create Configuration Loader Utility

### Description
Provide a small helper that loads `config/defaults.yaml` once and exposes values via a typed dict. Used by engines that need fallback defaults when input data is missing.

### Dependencies
TASK-004

### Expected Output
`src/utils/config.py` exposing:
- `load_config(path: str = "config/defaults.yaml") -> dict`
- `get_default(key: str)` returning the value from cached config.
- LRU/module-level cache so YAML is read once per process.

### Acceptance Criteria
- `from src.utils.config import get_default; get_default("working_hours_per_day") == 8`.
- Calling `get_default` twice does not re-open the file.
- Missing key raises a clear `KeyError` mentioning the key name and the YAML path.

### Status
DONE

---

## TASK-006 — Create Streamlit App Skeleton

### Description
Build the entry point `app.py` with sidebar navigation to the seven pages defined in PRD §13.1. Pages render only a title placeholder for now — real content is added in Phase 8.

### Dependencies
TASK-001

### Expected Output
`app.py` at project root:
- `st.set_page_config` with title `"Marvi — Operational Planning"` and wide layout.
- Sidebar radio with options: `Overview`, `Upload Data`, `Capacity Dashboard`, `Phase Saturation`, `Timeline`, `Scenario Testing`, `Future AI Layer`.
- Each selection renders `st.title(page_name)` and `st.info("Coming soon")`.

### Acceptance Criteria
- `streamlit run app.py` launches without errors.
- Clicking each sidebar option changes the page title.
- No tracebacks in terminal.

### Status
DONE

---

## TASK-007 — Create Sample Excel Mock Data

### Description
Produce a realistic but small `.xlsx` file under `data/sample/` containing the four input sheets the normalizer will expect (orders, product matrix, labs, phase capacity). Used by Demo Mode (PRD §6.2) and tests.

### Dependencies
TASK-002

### Expected Output
`data/sample/sample_planning.xlsx` with sheets:
- **orders**: 5 rows covering 2 product types, at least one tight-deadline order. Columns: order_id, client, product_type, quantity, start_date, deadline, assigned_lab, assigned_chain, progress_percentage, priority.
- **product_matrix**: 2 product types × 4 phases each. Columns: product_type, phase_name, min_time_minutes, max_time_minutes, avg_time_minutes, setup_time_minutes, phase_order. Phase names drawn from PRD §3.3.A (e.g. `imbastitura`, `rifilo`, `confezione capo`, `controllo misure`).
- **labs**: 2 labs. Columns match PRD §7.3.
- **phase_capacity**: 8 rows (2 labs × 4 phases). Columns match PRD §7.4.

Generated by a one-shot script `scripts/build_sample_data.py` that writes the file via openpyxl — script is committed so the file can be regenerated.

### Acceptance Criteria
- File opens in `openpyxl.load_workbook` without error.
- `pd.read_excel(path, sheet_name=None)` returns 4 DataFrames with the expected column names.
- At least one order's `quantity × avg_time` exceeds its lab's daily capacity (so bottleneck logic has something to flag in later tasks).

### Status
CODE_READY

---

# PHASE 2 — Data Layer

## TASK-008 — Build Validation Utility

### Description
Generic helpers used by the normalizer and engines to check DataFrames for required columns, missing values, and invalid numeric ranges. Returns structured warnings rather than raising, so the UI can show user-friendly messages (PRD §16).

### Dependencies
TASK-001

### Expected Output
`src/utils/validation.py` with:
- `@dataclass ValidationWarning(field: str, message: str, severity: str)`
- `check_required_columns(df: pd.DataFrame, required: list[str], context: str) -> list[ValidationWarning]`
- `check_no_nulls(df: pd.DataFrame, columns: list[str], context: str) -> list[ValidationWarning]`
- `check_positive(df: pd.DataFrame, columns: list[str], context: str) -> list[ValidationWarning]`
- `check_date_valid(df: pd.DataFrame, columns: list[str], context: str) -> list[ValidationWarning]`

### Acceptance Criteria
- Each function returns `[]` on a clean DataFrame.
- `check_required_columns(df, ["x"], "orders")` on a df missing `x` returns one warning whose `message` mentions both `"x"` and `"orders"`.
- `severity` for missing-required-column is `"high"`; for nulls in optional column is `"medium"`.

### Status
CODE_READY

---

## TASK-009 — Build Formatting Utility

### Description
Display helpers used by the UI layer: percentage strings, minute-to-hour conversion, status-to-color lookup, and short number formatting. Keeps Streamlit code free of inline formatting logic.

### Dependencies
TASK-003

### Expected Output
`src/utils/formatting.py` with:
- `fmt_pct(value: float, decimals: int = 1) -> str` → `"85.0%"`
- `fmt_minutes(minutes: float) -> str` → `"2h 30m"` or `"45m"`
- `fmt_int(value: float) -> str` with thousands separator.
- `status_color(status: str) -> str` returning a hex from `constants.STATUS_COLORS`.
- `utilization_status(utilization: float) -> str` returning `"safe" | "at_risk" | "critical"` using thresholds from `constants`.

### Acceptance Criteria
- `fmt_pct(0.853) == "85.3%"`.
- `fmt_minutes(150) == "2h 30m"`, `fmt_minutes(45) == "45m"`.
- `utilization_status(0.5) == "safe"`, `utilization_status(0.9) == "at_risk"`, `utilization_status(1.2) == "critical"`.

### Status
DONE

---

## TASK-010 — Build Excel Parser

### Description
Read an uploaded `.xlsx` file and return a dict of raw DataFrames keyed by sheet name. No business logic, no normalization — pure I/O (PRD §9.1).

### Dependencies
TASK-002

### Expected Output
`src/parsers/excel_parser.py` exposing:
- `parse_excel(file: BinaryIO | str | Path) -> dict[str, pd.DataFrame]`
- `list_sheets(file) -> list[str]`
- Custom exception `ExcelParseError` raised on unreadable / empty workbook / unsupported file type.

### Acceptance Criteria
- `parse_excel("data/sample/sample_planning.xlsx")` returns 4 DataFrames keyed `"orders"`, `"product_matrix"`, `"labs"`, `"phase_capacity"`.
- Passing a non-xlsx path raises `ExcelParseError` with a message containing the file extension.
- Module contains no calls to engine modules.

### Status
CODE_READY

---

## TASK-011 — Normalizer: orders_df

### Description
Convert the raw `orders` sheet into the canonical `orders_df` schema from PRD §7.1, applying fallbacks for optional columns and emitting `ValidationWarning`s for required-but-missing fields.

### Dependencies
TASK-008, TASK-010

### Expected Output
In `src/parsers/normalizer.py`:
- `normalize_orders(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, list[ValidationWarning]]`
- Column mapping handles case-insensitive matches and Italian aliases for at least: `cliente→client`, `quantità→quantity`, `scadenza→deadline`.
- Applies fallbacks: `client="Unknown Client"`, `start_date=today()`, `assigned_lab="Default Lab"`, `assigned_chain="Default Chain"`, `progress_percentage=0.0`, `priority="normal"`.
- Generates `order_id` as `ORD-{row_index:04d}` if missing.
- Casts: `quantity`→int, `start_date`/`deadline`→`datetime.date`, `progress_percentage`→float in `[0.0, 1.0]` (canonical scale used everywhere downstream).

### Acceptance Criteria
- Feeding the sample file's `orders` sheet returns a DataFrame with all 10 columns from PRD §7.1 and zero high-severity warnings.
- Feeding a DataFrame missing `product_type` returns a warning of severity `"high"` mentioning `product_type`.
- `progress_percentage` is always a float in `[0.0, 1.0]` (decision: fraction scale; document with a one-line comment in the module).

### Status
CODE_READY

---

## TASK-012 — Normalizer: product_matrix_df

### Description
Convert raw `product_matrix` into the canonical schema from PRD §7.2. Compute `avg_time_minutes` from min/max if missing; infer `phase_order` by row position within each product if missing.

### Dependencies
TASK-008, TASK-010

### Expected Output
In `src/parsers/normalizer.py`:
- `normalize_product_matrix(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, list[ValidationWarning]]`
- If `avg_time_minutes` missing but both `min_time_minutes` and `max_time_minutes` present → `avg = (min+max)/2`.
- If only one of min/max present → use it as avg.
- If all three missing → severity-high warning for that row.
- `phase_order` inferred via `groupby("product_type").cumcount()+1` when missing.
- `setup_time_minutes` default `0.0`.

### Acceptance Criteria
- Sample data produces 7-column DataFrame with no warnings.
- Synthetic row with only `min=10, max=20` yields `avg_time_minutes == 15.0`.
- `phase_order` is strictly increasing within each `product_type` group.

### Status
CODE_READY

---

## TASK-013 — Normalizer: labs_df

### Description
Convert raw `labs` sheet into the schema from PRD §7.3, applying defaults from `config/defaults.yaml` for any missing optional field.

### Dependencies
TASK-005, TASK-008, TASK-010

### Expected Output
In `src/parsers/normalizer.py`:
- `normalize_labs(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, list[ValidationWarning]]`
- Missing `working_hours_per_day` → fill from `get_default("working_hours_per_day")`.
- Missing `default_efficiency` → fill from config default.
- Missing `machine_uptime` → fill from config default.
- Missing `max_weekly_hours` → fill from config default.
- Missing `overtime_allowed` → fill from config default.
- Required: `lab_id` (warning if missing).

### Acceptance Criteria
- Sample data passes through with no warnings.
- DataFrame with only `lab_id` populated produces a result where every other column is filled with the documented config default.

### Status
CODE_READY

---

## TASK-014 — Normalizer: phase_capacity_df

### Description
Convert raw `phase_capacity` sheet into the schema from PRD §7.4. Pre-computes `available_minutes_per_day` so the capacity engine doesn't have to recompute on every call.

### Dependencies
TASK-005, TASK-008, TASK-010, TASK-013

### Expected Output
In `src/parsers/normalizer.py`:
- `normalize_phase_capacity(raw_df: pd.DataFrame, labs_df: pd.DataFrame) -> tuple[pd.DataFrame, list[ValidationWarning]]`
- `workers_assigned` defaults to `workers_total` if missing.
- `efficiency` and `uptime` pulled from the matching lab row when missing.
- `available_minutes_per_day = workers_assigned × (lab.working_hours_per_day × 60) × efficiency × uptime`.
- Warns when a phase row references an unknown `lab_id`.

### Acceptance Criteria
- For sample lab `"L1"` with `workers_assigned=4, working_hours_per_day=8, efficiency=0.75, uptime=0.9`: `available_minutes_per_day == 4 * 480 * 0.75 * 0.9 == 1296.0`.
- A row with `lab_id="GHOST"` produces one warning naming the missing lab.

### Status
CODE_READY

---

## TASK-015 — Normalization Orchestrator + Mock Fallback

### Description
Single entry point that the UI calls after upload. Runs all four normalizers, collects warnings, and — if any sheet is missing or empty — substitutes the sample DataFrames so the dashboard still renders (Mode B from PRD §6.2).

### Dependencies
TASK-007, TASK-011, TASK-012, TASK-013, TASK-014

### Expected Output
In `src/parsers/normalizer.py`:
- `normalize_all(raw: dict[str, pd.DataFrame], use_mock_fallback: bool = True) -> dict`
- Returns: `{"orders": df, "product_matrix": df, "labs": df, "phase_capacity": df, "warnings": list[ValidationWarning], "used_mock": dict[str, bool]}`.
- For each of the four canonical sheets: if missing/empty in `raw` AND `use_mock_fallback`, load that sheet from `data/sample/sample_planning.xlsx` and set `used_mock[sheet]=True`.

### Acceptance Criteria
- `normalize_all(parse_excel("data/sample/sample_planning.xlsx"))` returns four populated DataFrames and `used_mock == {sheet: False for sheet in 4 sheets}`.
- `normalize_all({}, use_mock_fallback=True)` returns four populated DataFrames and `used_mock` all True.
- `normalize_all({}, use_mock_fallback=False)` returns four empty DataFrames and high-severity warnings.

### Status
CODE_READY

---

# PHASE 3 — Core Calculation Engines

## TASK-016 — Product Matrix Engine

### Description
Given a product_type, return the ordered list of phases with their average timing. Used by the capacity engine to expand each order into per-phase work (PRD §9.3, §10.6).

### Dependencies
TASK-012

### Expected Output
`src/engines/product_matrix_engine.py` with:
- `get_phases_for_product(product_matrix_df: pd.DataFrame, product_type: str) -> pd.DataFrame`
  Returns subset sorted by `phase_order` with columns `phase_name`, `avg_time_minutes`, `setup_time_minutes`, `phase_order`.
- `list_product_types(product_matrix_df) -> list[str]`
- Custom exception `UnknownProductError` raised when product is not in the matrix.

### Acceptance Criteria
- For sample data product `"Giacca"`: returns 4 rows ordered by `phase_order`.
- `get_phases_for_product(df, "DoesNotExist")` raises `UnknownProductError` whose message contains the product name.

### Status
CODE_READY

---

## TASK-017 — Capacity Engine

### Description
Core arithmetic engine. For every (order, phase) pair, compute required minutes, available minutes, utilization rate, and capacity gap using the formulas in PRD §9.4 and §10.

### Dependencies
TASK-014, TASK-016

### Expected Output
`src/engines/capacity_engine.py` with:
- `compute_capacity_results(orders_df, product_matrix_df, labs_df, phase_capacity_df, planning_days: int = 5) -> pd.DataFrame`
- Output schema = PRD §7.5 `capacity_results_df`:
  `order_id, product_type, phase_name, quantity, required_minutes, available_minutes, utilization_rate, capacity_gap_minutes, is_overloaded, is_bottleneck`.
- Formulas:
  - `required_minutes = quantity * avg_time_minutes + setup_time_minutes`
  - `available_minutes = phase_capacity.available_minutes_per_day * planning_days`
  - `utilization_rate = required_minutes / available_minutes` (returns `inf` if available is 0; never raises ZeroDivisionError)
  - `capacity_gap_minutes = available_minutes - required_minutes`
  - `is_overloaded = utilization_rate > SAFE_UTILIZATION_THRESHOLD`
  - `is_bottleneck = False` (set by bottleneck engine in TASK-018)
- Rows where order's `assigned_lab` does not exist in `phase_capacity_df` are still emitted, with `available_minutes=0` and a clear value (`inf`) for utilization so the UI can flag them.

### Acceptance Criteria
- Sample data produces one row per (order, phase) — for 5 orders averaging 4 phases each, ≥ 15 rows.
- `available_minutes == 0` produces `utilization_rate == math.inf` (no division error).
- The pre-built sample order designed to exceed capacity has `utilization_rate > 1.0` for at least one phase.

### Status
CODE_READY

---

## TASK-018 — Bottleneck Engine

### Description
Mark the single most-overloaded phase per order as `is_bottleneck=True` and add a `bottleneck_rank` column ranking phases by utilization within each order. Implements PRD §9.5 and §10.5.

### Dependencies
TASK-017

### Expected Output
`src/engines/bottleneck_engine.py` with:
- `identify_bottlenecks(capacity_results_df: pd.DataFrame) -> pd.DataFrame`
- Sets `is_bottleneck=True` for the row with the highest `utilization_rate` within each `order_id`.
- Adds `bottleneck_rank: int` (1 = most critical) per order.
- Adds `bottleneck_phase_global: str` — name of the phase with the highest mean utilization across all orders, attached as a top-level summary returned alongside the DataFrame.
- Returns `(df_with_flags, summary: dict)` where summary contains `most_critical_phase: str` and `most_critical_phase_utilization: float`.

### Acceptance Criteria
- For each `order_id`, exactly one row has `is_bottleneck=True`.
- `bottleneck_rank == 1` matches the row with `is_bottleneck=True`.
- On sample data, `summary["most_critical_phase"]` is one of the actual phase names from `product_matrix`.

### Status
CODE_READY

---

## TASK-018B — Lab / Chain Allocation Engine

### Description
Decide which lab (and chain) processes each order when `assigned_lab` / `assigned_chain` are missing or empty in the input, and provide an alternative-lab lookup the recommendation engine can use for `REALLOCATE` suggestions. Implements the "Lab / Chain Allocation Engine" box from PRD §5.1 (which §9 leaves unspecified — this task fills that gap).

### Dependencies
TASK-014, TASK-016

### Expected Output
`src/engines/lab_allocation_engine.py` with:
- `allocate_orders(orders_df: pd.DataFrame, phase_capacity_df: pd.DataFrame, product_matrix_df: pd.DataFrame) -> tuple[pd.DataFrame, list[ValidationWarning]]`
  - For each order with missing/empty `assigned_lab`: pick the lab whose phases required by that product have the highest aggregate `available_minutes_per_day` (least-loaded lab first).
  - For each order with missing/empty `assigned_chain`: fill with `"Default Chain"`.
  - Returns a new DataFrame; must not mutate input.
- `find_alternative_lab(order_row: pd.Series, current_lab: str, phase_capacity_df, product_matrix_df) -> str | None`
  - Returns the `lab_id` with the most residual capacity for the order's required phases, excluding `current_lab`. Returns `None` if no alternative exists.
- Deterministic tie-break by `lab_id` lexicographic order (no randomness).

### Acceptance Criteria
- An order with `assigned_lab=None` and 2 viable labs is allocated to the lab with the higher aggregate available minutes across the product's phases.
- An order with `assigned_lab` already set is returned unchanged.
- `find_alternative_lab(...)` with only one lab in the system returns `None`.
- `allocate_orders` does not mutate `orders_df` (`orig.equals(orig_copy)` after call).

### Status
CODE_READY

---

# PHASE 4 — Operational Stress & Scenario Layer

## TASK-019 — Scenario Engine

### Description
Apply user-controlled scenario modifiers from PRD §9.9 to copies of the input DataFrames before the calculation engines run. Pure transformation — no side effects on originals.

### Dependencies
TASK-013, TASK-014

### Expected Output
`src/engines/scenario_engine.py` with:
- `@dataclass ScenarioInputs(demand_multiplier: float = 1.0, efficiency_drop: float = 0.0, absent_workers: int = 0, machine_downtime: float = 0.0, urgent_order_flag: bool = False)`
- `apply_scenario(orders_df, phase_capacity_df, scenario: ScenarioInputs) -> tuple[pd.DataFrame, pd.DataFrame]`
- Effects:
  - `orders.quantity *= demand_multiplier` (rounded to int, min 1).
  - `phase_capacity.efficiency = max(0.0, efficiency - efficiency_drop)`.
  - `phase_capacity.workers_assigned = max(0, workers_assigned - absent_workers)`.
  - `phase_capacity.uptime = max(0.0, uptime - machine_downtime)`.
  - Recomputes `available_minutes_per_day` after the changes.
  - If `urgent_order_flag`, sets `priority="urgent"` on rows where it was `"normal"`.
- Original DataFrames must not be mutated (`assert orig.equals(orig_copy)` after call).

### Acceptance Criteria
- `apply_scenario(orders, capacity, ScenarioInputs())` returns DataFrames equal to inputs (identity scenario).
- `ScenarioInputs(demand_multiplier=2.0)` doubles all quantities (after rounding).
- `ScenarioInputs(absent_workers=1)` reduces `workers_assigned` by 1 and proportionally reduces `available_minutes_per_day`.
- Original DataFrames remain unchanged after call.

### Status
CODE_READY

---

## TASK-020 — Stress Engine: Utilization Rules

### Description
Generate `stress_events_df` rows for utilization-based triggers from PRD §9.6: utilization > 85%, utilization > 100%, phase utilization > 90%.

### Dependencies
TASK-017, TASK-018

### Expected Output
In `src/engines/stress_engine.py`:
- `evaluate_utilization_stress(capacity_results_df: pd.DataFrame) -> pd.DataFrame`
- Returns DataFrame matching PRD §7.7 schema: `event_id, order_id, event_type, severity, message, triggered_by, recommended_action`.
- Event types emitted: `"utilization_high"` (>85%), `"utilization_critical"` (>100%), `"phase_overload"` (phase utilization >90%).
- Severity: `"medium"` for high, `"high"` for critical and phase_overload.
- `event_id` = `f"STR-{uuid4().hex[:8]}"`.
- `recommended_action` strings drawn from: `"Consider split"`, `"Consider postpone"`, `"Reallocate to another lab"`.

### Acceptance Criteria
- An order with all phases at 50% produces zero events.
- An order with one phase at 1.2 produces at least one `utilization_critical` event mentioning that phase.
- Every event row has all 7 schema columns populated (no NaN).

### Status
CODE_READY

---

## TASK-021 — Stress Engine: Scenario & Deadline Rules

### Description
Add the remaining stress triggers from PRD §9.6: overtime required, machine downtime active, worker absence active, >2 parallel orders per lab, deadline infeasible.

### Dependencies
TASK-019, TASK-020

### Expected Output
In `src/engines/stress_engine.py`:
- `evaluate_scenario_stress(orders_df, capacity_results_df, scenario: ScenarioInputs, today: date) -> pd.DataFrame`
- Triggers:
  - `"machine_downtime"` severity high — when `scenario.machine_downtime > 0`.
  - `"worker_absence"` severity high — when `scenario.absent_workers > 0`.
  - `"overtime_required"` severity high — when any phase's required_minutes > available_minutes AND `lab.overtime_allowed == False`.
  - `"parallel_overload"` severity medium — when same `assigned_lab` appears > `MAX_PARALLEL_ORDERS_PER_LAB` times within overlapping start_date→deadline windows.
  - `"deadline_infeasible"` severity high — when `(deadline - today).days * lab.available_minutes_per_day < order_total_required_minutes`.
- `evaluate_all_stress(...)` convenience wrapper concatenates utilization + scenario events.

### Acceptance Criteria
- `evaluate_scenario_stress(..., ScenarioInputs())` on a clean dataset where capacity is sufficient produces 0 events.
- A scenario with `machine_downtime=0.2` produces at least one `"machine_downtime"` event.
- Order with `deadline = today` and any positive required time produces a `"deadline_infeasible"` event.

### Status
CODE_READY

---

# PHASE 5 — Recommendation Layer

## TASK-022 — Recommendation Engine

### Description
Map calculation outputs to one of the six recommendation labels from PRD §12 with human-readable reasons and suggested actions. This is the most user-visible output — clarity matters.

### Dependencies
TASK-018, TASK-018B, TASK-021

### Expected Output
`src/engines/recommendation_engine.py` with:
- `generate_recommendations(capacity_results_df, stress_events_df, timeline_df: pd.DataFrame | None = None) -> pd.DataFrame`
- Output schema = PRD §7.8: `order_id, recommendation, severity, reasons, suggested_actions`.
- Decision order (first matching wins, applied per `order_id`):
  1. `utilization > 1.0` OR any stress event of type `"utilization_critical"`, `"overtime_required"`, `"deadline_infeasible"` → `REJECT` (or `POSTPONE` if deadline-related, or `SPLIT` if oversized).
  2. `utilization between 0.85 and 1.0` OR any medium-severity stress event → `AT_RISK` / `REALLOCATE` (REALLOCATE if `find_alternative_lab` from TASK-018B returns a non-None lab; otherwise AT_RISK). When REALLOCATE is chosen, the alternative lab name must appear in `suggested_actions`.
  3. Otherwise → `ACCEPT`.
- `reasons` is a list of human strings, e.g. `["Phase 'rifilo' at 112% utilization", "Deadline only 2 days away"]`.
- `suggested_actions` is a list of strings, e.g. `["Split order across L1 and L2", "Postpone by 3 days"]`.
- Severity column mirrors the highest severity that drove the decision: `low`, `medium`, `high`.

### Acceptance Criteria
- Order with all phases at 50% utilization and no stress events → `recommendation == "ACCEPT"`, `severity == "low"`, non-empty reason list.
- Order with one phase at 120% utilization → recommendation in `{"REJECT", "POSTPONE", "SPLIT"}`, never `"ACCEPT"`.
- An `"overtime_required"` event blocks `"ACCEPT"` outcome.
- `reasons` list is never empty; `suggested_actions` is never empty.

### Status
CODE_READY

---

# PHASE 6 — Timeline Layer

## TASK-023 — Timeline Engine

### Description
Compute order-level start, end, and overlap data for the Gantt visualization (PRD §9.8).

### Dependencies
TASK-017

### Expected Output
`src/engines/timeline_engine.py` with:
- `build_timeline(orders_df, capacity_results_df) -> pd.DataFrame`
- Output schema = PRD §7.6: `order_id, product_type, assigned_lab, start_date, end_date, deadline, duration_days, overlap_flag, status`.
- For each order: `total_required_minutes = sum(capacity_results_df[order_id].required_minutes)`.
- `duration_days = ceil(total_required_minutes / order_lab.available_minutes_per_day)`.
- `end_date = start_date + duration_days` (skip weekends if `working_days_per_week == 5`).
- `overlap_flag = True` if another order in the same `assigned_lab` has an overlapping `[start_date, end_date]` window.
- `status`: `"on_track"` if `end_date <= deadline`, `"at_risk"` if within 2 days of deadline, `"late"` if `end_date > deadline`.

### Acceptance Criteria
- Every order in `orders_df` produces exactly one row.
- Two orders in the same lab with overlapping windows both have `overlap_flag == True`.
- An order with `end_date == deadline - 5 days` has `status == "on_track"`.

### Status
CODE_READY

---

# PHASE 7 — UI Components

## TASK-024 — KPI Cards Component

### Description
Reusable Streamlit component for the colored metric cards used on Overview and Capacity Dashboard pages.

### Dependencies
TASK-006, TASK-009

### Expected Output
`src/components/kpi_cards.py` with:
- `kpi_card(label: str, value: str, status: str = "neutral", delta: str | None = None) -> None`
  Renders a bordered card using `st.markdown` with inline CSS, colored by `status_color(status)`.
- `kpi_row(cards: list[dict]) -> None` — renders multiple cards in `st.columns`.

### Acceptance Criteria
- Calling `kpi_card("Utilization", "87%", "at_risk")` in a Streamlit page renders without error.
- Card border color matches `STATUS_COLORS["at_risk"]`.
- No business logic in this file — purely presentational.

### Status
CODE_READY

---

## TASK-025 — Charts Component

### Description
Plotly chart helpers used by Capacity Dashboard and Phase Saturation pages. Keeps Plotly figure construction out of page files.

### Dependencies
TASK-003

### Expected Output
`src/components/charts.py` with:
- `phase_utilization_bar(capacity_results_df: pd.DataFrame) -> go.Figure`
  Horizontal bar of utilization per phase, colored by status (`safe`/`at_risk`/`critical`), with a vertical reference line at 100%.
- `order_capacity_gap_bar(capacity_results_df: pd.DataFrame) -> go.Figure`
  Bar of capacity gap (minutes) per order, negative gaps in red.
- All figures: white background, no gridlines, minimum 400px height, no Plotly logo.

### Acceptance Criteria
- Each function returns a `plotly.graph_objects.Figure` object.
- Calling each with sample data produces a figure with `len(fig.data) > 0`.
- Figure color decisions use `STATUS_COLORS` from constants, no hex literals inline.

### Status
CODE_READY

---

## TASK-026 — Alerts Component

### Description
Render a list of stress events or warnings as colored cards. Used on Capacity Dashboard and Scenario Testing pages.

### Dependencies
TASK-006, TASK-009

### Expected Output
`src/components/alerts.py` with:
- `render_alerts(stress_events_df: pd.DataFrame, max_items: int = 10) -> None`
  Iterates over events, renders each as `st.error` / `st.warning` / `st.info` based on severity.
- `render_recommendation_panel(recommendations_df: pd.DataFrame, order_id: str | None = None) -> None`
  Highlights one or all recommendations with reason/action lists. This panel must be visually prominent (PRD §14).

### Acceptance Criteria
- `render_alerts` on empty DataFrame renders `st.success("No operational stress detected")`.
- `render_recommendation_panel(df, order_id="ORD-0001")` renders only that order.
- A `REJECT` recommendation renders in red, `ACCEPT` in green, `AT_RISK`/`REALLOCATE`/`SPLIT`/`POSTPONE` in orange.

### Status
CODE_READY

---

## TASK-027 — Timeline UI Component

### Description
Plotly-based Gantt-style timeline component for the Timeline page.

### Dependencies
TASK-023, TASK-025

### Expected Output
`src/components/timeline.py` with:
- `render_timeline_chart(timeline_df: pd.DataFrame) -> go.Figure`
  `px.timeline` with `x_start=start_date`, `x_end=end_date`, `y=order_id`, color by `status`.
- Vertical dashed line at "today".
- Hover shows: order_id, product_type, deadline, duration_days, status.

### Acceptance Criteria
- Returns a Plotly figure with one bar per row of `timeline_df`.
- Colors follow `STATUS_COLORS` mapping (`on_track`→safe, `at_risk`→at_risk, `late`→critical).
- No errors when `timeline_df` is empty (renders empty figure with an annotation `"No orders to display"`).

### Status
CODE_READY

---

# PHASE 8 — UI Pages

## TASK-028 — Refactor app.py for Page Routing + Session State

### Description
Replace the placeholder skeleton with a real router that loads page modules and persists normalized DataFrames across page switches via `st.session_state`.

### Dependencies
TASK-006, TASK-015

### Expected Output
Updated `app.py`:
- Each page lives in `src/ui/pages/<name>.py` (create `src/ui/__init__.py` and `src/ui/pages/__init__.py`).
- `app.py` maintains `st.session_state["data"]` = dict from `normalize_all` and `st.session_state["scenario"]` = `ScenarioInputs()`.
- Each page module exposes `def render(): ...` called by the router.
- If `st.session_state["data"]` is missing, every page except `Overview` and `Upload Data` shows `st.warning("Please upload data first or use demo mode on the Upload page.")` and returns.

### Acceptance Criteria
- `streamlit run app.py` still launches cleanly.
- Navigating away and back to a page does not re-trigger Excel parsing (session state persists).
- A fresh session lands on Overview without errors.

### Status
CODE_READY

---

## TASK-029 — Page: Overview

### Description
First page the user sees. Shows project title, short explanation, dataset status (loaded? mock?), and 3-4 high-level KPIs (PRD §13.2 Page 1).

### Dependencies
TASK-024, TASK-028

### Expected Output
`src/ui/pages/overview.py` with `render()` that displays:
- `st.title("Marvi — Operational Planning")`.
- Two-paragraph project description sourced from PRD §1.1.
- A dataset-status card: `"Live data: sample_planning.xlsx"` or `"Demo mode — no data uploaded"` or `"No data — upload a file"`.
- KPI row (uses `kpi_row` from TASK-024): total orders, total products, overall utilization, number of critical alerts. KPIs show `"—"` when data not yet loaded.

### Acceptance Criteria
- Page renders before any upload (KPIs show `"—"`, no traceback).
- After upload, KPI values reflect computed data.
- Status card color: green (live data), orange (mock), gray (none).

### Status
CODE_READY

---

## TASK-030 — Page: Upload Data

### Description
Allows the user to upload an Excel file, choose demo mode, preview parsed sheets, and view validation warnings (PRD §13.2 Page 2).

### Dependencies
TASK-010, TASK-015, TASK-028

### Expected Output
`src/ui/pages/upload.py` with `render()`:
- `st.file_uploader("Upload planning workbook", type=["xlsx"])`.
- `st.toggle("Use demo data instead")` — when on, ignores upload and loads `data/sample/sample_planning.xlsx`.
- On successful parse:
  - Show "Detected sheets" list.
  - Show first 10 rows of each normalized DataFrame in `st.expander`.
  - Show all `ValidationWarning`s grouped by severity (high → `st.error`, medium → `st.warning`, low → `st.info`).
  - Save normalized result into `st.session_state["data"]`.
- On parse error: show `st.error(str(ExcelParseError))` and do not clear existing session data.

### Acceptance Criteria
- Uploading the sample file populates session state and shows 4 sheet previews with zero high-severity warnings.
- Demo toggle works without an actual upload.
- A malformed file (e.g. a renamed `.txt`) produces a user-friendly error, no stack trace in the UI.

### Status
CODE_READY

---

## TASK-031 — Page: Capacity Dashboard

### Description
Headline operational view: overall utilization, capacity gap, estimated production days, count of overloaded phases, and the global recommendation card (PRD §13.2 Page 3).

### Dependencies
TASK-017, TASK-022, TASK-024, TASK-025, TASK-026, TASK-028

### Expected Output
`src/ui/pages/capacity_dashboard.py` with `render()`:
- Runs `compute_capacity_results` → `identify_bottlenecks` → `evaluate_all_stress` → `generate_recommendations` against current session data + scenario.
- KPI row (4 cards): overall avg utilization, total capacity gap (hours), planning days assumed, overloaded phases count.
- Chart: `phase_utilization_bar`.
- Alerts panel: top 5 stress events via `render_alerts`.
- Recommendation panel: `render_recommendation_panel` showing all orders.

### Acceptance Criteria
- Loading sample data → page renders all four KPIs, the bar chart, alerts, and at least one recommendation card.
- Switching scenarios (after TASK-033) updates the values without page reload.
- All status colors match thresholds from `constants`.

### Status
CODE_READY

---

## TASK-032 — Page: Phase Saturation

### Description
Detailed per-phase view: utilization, bottleneck flag, capacity gap, workers-at-risk indicator (PRD §13.2 Page 4).

### Dependencies
TASK-018, TASK-024, TASK-025, TASK-028

### Expected Output
`src/ui/pages/phase_saturation.py` with `render()`:
- `phase_utilization_bar` horizontal chart.
- A table (DataFrame): `phase_name`, `avg_utilization`, `bottleneck` (✓ for bottleneck phase), `capacity_gap_h`, `status`.
- Status cards above the table: "Most critical phase: X (utilization Y%)" — large prominent card.
- "Workers at risk" indicator: shows count of phases where `is_overloaded == True`.

### Acceptance Criteria
- Sample data produces a table where exactly one row is marked bottleneck.
- The "most critical phase" card matches `summary["most_critical_phase"]` from bottleneck engine.

### Status
CODE_READY

---

## TASK-033 — Page: Timeline

### Description
Renders the Gantt-style timeline of all orders (PRD §13.2 Page 5).

### Dependencies
TASK-023, TASK-027, TASK-028

### Expected Output
`src/ui/pages/timeline.py` with `render()`:
- Builds timeline via `build_timeline`.
- Renders `render_timeline_chart`.
- Below chart: small legend (`on_track` green, `at_risk` orange, `late` red).
- Filter widget: multiselect for `assigned_lab` and `status`.

### Acceptance Criteria
- Sample data renders a chart with N bars where N = number of orders.
- Filtering by lab visibly reduces displayed bars.
- Page does not error when timeline is empty.

### Status
CODE_READY

---

## TASK-034 — Page: Scenario Testing

### Description
Interactive controls for the four scenario modifiers, with live recomputation of capacity, stress, and recommendations (PRD §13.2 Page 6).

### Dependencies
TASK-019, TASK-031, TASK-028

### Expected Output
`src/ui/pages/scenario_testing.py` with `render()`:
- Four sliders (in a sidebar `st.form` to batch changes):
  - `demand_multiplier` 0.5 → 2.0 (step 0.1, default 1.0).
  - `efficiency_drop` 0.0 → 0.5 (step 0.05, default 0.0).
  - `absent_workers` 0 → 5 (default 0).
  - `machine_downtime` 0.0 → 0.5 (step 0.05, default 0.0).
- Apply button writes the resulting `ScenarioInputs` into `st.session_state["scenario"]`.
- Displays a before/after comparison table: overall utilization, overloaded phase count, critical events count, accepted-order count.

### Acceptance Criteria
- Moving any slider and pressing Apply updates the comparison table on the same page.
- The Capacity Dashboard page reflects the new scenario after navigating to it (no manual refresh).
- "Reset" button restores `ScenarioInputs()` defaults.

### Status
CODE_READY

---

## TASK-035 — Page: Future AI Layer

### Description
Polished non-functional showcase of planned future expansions: predictive delays, anomaly detection, forecasting, optimization, digital twin (PRD §13.2 Page 7, §19).

### Dependencies
TASK-024, TASK-028

### Expected Output
`src/ui/pages/future_ai.py` with `render()`:
- Title + intro paragraph: "These features are intentionally not implemented in the MVP. They represent the strategic expansion path."
- 5 cards (using `kpi_card` style but larger), one per future feature, each with: name, one-paragraph description, "Planned" pill.
- One visual diagram (PNG placeholder in `assets/mockups/future_ai.png` — create a 1200×600 transparent PNG with text "Future AI Layer Roadmap" as placeholder; can be improved later).
- Disclaimer at the bottom: "MVP is rule-based and deterministic. AI extensions require additional historical data not currently available."

### Acceptance Criteria
- Page renders without errors and without requiring uploaded data.
- All 5 future-feature cards are visible and styled consistently.
- Disclaimer is present and prominent.

### Status
CODE_READY

---

# PHASE 9 — Testing & Polish

## TASK-036 — Unit Tests: Capacity Engine

### Description
Cover the four formulas in PRD §10 with happy-path and edge-case tests.

### Dependencies
TASK-017

### Expected Output
`tests/test_capacity_engine.py` with at least these tests:
- `test_required_minutes_basic` — quantity × time + setup.
- `test_available_minutes_uses_efficiency_and_uptime`.
- `test_utilization_rate_correct`.
- `test_capacity_gap_can_be_negative`.
- `test_zero_available_minutes_returns_inf_no_exception`.
- `test_overloaded_flag_uses_threshold_from_constants`.
- Uses small in-memory DataFrames (no Excel file dependency).

### Acceptance Criteria
- `pytest tests/test_capacity_engine.py -v` passes with ≥ 6 tests green.
- Tests do not read from disk.
- Tests do not import Streamlit.

### Status
CODE_READY

---

## TASK-037 — Unit Tests: Recommendation Engine

### Description
Lock down the decision logic from PRD §12 with table-driven tests.

### Dependencies
TASK-022

### Expected Output
`tests/test_recommendation_engine.py` with at least:
- `test_accept_when_low_utilization_and_no_stress`.
- `test_reject_when_utilization_above_one`.
- `test_at_risk_when_utilization_between_85_and_100`.
- `test_overtime_event_blocks_accept`.
- `test_deadline_infeasible_produces_postpone`.
- `test_reasons_list_never_empty`.
- `test_suggested_actions_list_never_empty`.

### Acceptance Criteria
- `pytest tests/test_recommendation_engine.py -v` passes with ≥ 7 tests green.
- Each test uses fixtures with hand-crafted `capacity_results_df` and `stress_events_df`.

### Status
CODE_READY

---

## TASK-038 — Unit Tests: Normalizer Fallbacks

### Description
Verify that fallback values from `config/defaults.yaml` are applied correctly when input columns are missing (PRD §6.2 Mode B).

### Dependencies
TASK-015

### Expected Output
`tests/test_normalizer.py` with at least:
- `test_orders_fills_missing_client_with_unknown`.
- `test_orders_generates_order_id_when_missing`.
- `test_product_matrix_computes_avg_from_min_max`.
- `test_labs_fills_efficiency_from_config_default`.
- `test_phase_capacity_warns_on_unknown_lab_id`.
- `test_normalize_all_uses_mock_for_missing_sheets`.

### Acceptance Criteria
- `pytest tests/test_normalizer.py -v` passes with ≥ 6 tests green.

### Status
CODE_READY

---

## TASK-039 — Error Handling Pass

### Description
Walk through every error case in PRD §16 and verify the UI shows a friendly message (not a stack trace) for each one. Fix anything that leaks an exception.

### Dependencies
TASK-029, TASK-030, TASK-031, TASK-032, TASK-033, TASK-034, TASK-035

### Expected Output
- Updated try/except blocks in page render functions that catch:
  - `ExcelParseError` → `st.error(message)`.
  - `UnknownProductError` → `st.warning(f"Product '{product}' not in product matrix.")`.
  - `KeyError` for missing config keys → `st.error("Configuration missing: <key>")`.
  - Any uncaught `Exception` in a page → `st.error("Unexpected error: <type>. Please check the data and try again.")` (and log full traceback to stderr).
- A checklist comment at the top of `app.py` listing the 8 error scenarios from PRD §16 with a ✓ next to each verified case.

### Acceptance Criteria
- Manually exercising each scenario from PRD §16 in `streamlit run app.py` produces a user-friendly message, never a red traceback box.
- The "Calculation Errors" category (available capacity = 0, division by zero, etc.) is covered by capacity engine's `inf`-instead-of-exception behavior (verified in TASK-036).

### Status
DONE

---

## TASK-040 — README

### Description
Single-page README so a fresh reviewer can install, run, and understand the MVP in under 5 minutes. A placeholder README already exists at project root — this task **replaces** it with the §-aligned 7-section version below.

### Dependencies
TASK-002, TASK-006, TASK-007, TASK-030

### Expected Output
`README.md` at project root with these sections (no more):
1. **What it is** — 3 sentences from PRD §1.1.
2. **Run locally** — `pip install -r requirements.txt && streamlit run app.py`.
3. **Try it without data** — toggle Demo mode on the Upload page.
4. **Project structure** — copy of the tree from PRD §15.
5. **Configuration** — pointer to `config/defaults.yaml`.
6. **Out of scope** — bullet list from PRD §2.2.
7. **Future work** — pointer to the Future AI Layer page.

### Acceptance Criteria
- A reader who has never seen the project can install and launch within 5 minutes following only the README.
- File is under 200 lines.
- No links to nonexistent files or pages.

### Status
DONE

---

# Loop-Compatible Iteration Protocol

For AI agents executing this file in iterative mode (Claude Code, Cloud Code, Ralf Loop):

1. **Pick** the first task with `Status: TODO` whose dependencies are all `DONE`.
2. **Set** that task's status to `IN_PROGRESS`.
3. **Implement** the task using only the files listed in its Expected Output.
4. **Verify** the Acceptance Criteria — run the explicit commands when present.
5. **Set** status to `DONE` and commit with message `feat(TASK-NNN): <task title>`.
6. **Stop** — do not chain tasks. The loop runner picks the next one.

If a task cannot be completed because of an upstream gap, set status to `BLOCKED` and add a one-line note under the Description explaining what is missing.
