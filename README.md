# Clothing Production Planning Dashboard

## What it is

A lightweight operational planning platform that transforms the company's
current Excel-based production planning workflow into a centralized,
interactive, and scalable decision-support dashboard. It supports Product
Managers and planning teams in evaluating real production capacity, monitoring
workload saturation, identifying bottlenecks, and avoiding operational
overload. The MVP is rule-based and deterministic; future AI extensions
(predictive delays, optimization, forecasting) are scoped on a dedicated page
and not implemented here.

## Setup & run locally

Requires **Python ≥ 3.10**.

```bash
# 1. install dependencies
pip install -r requirements.txt

# 2. (optional) run the test suite
pytest tests/ -v

# 3. launch the dashboard (opens at http://localhost:8501)
streamlit run app.py
```

(Optional, one-shot) regenerate the small bundled demo dataset:

```bash
python scripts/build_sample_data.py
```

## Datasets bundled with the project

Two `.xlsx` workbooks ship under `data/sample/`. Pick the one that matches
what you want to demo:

| File | Size | Scope | When to use |
|---|---|---|---|
| `data/sample/sample_planning.xlsx` | 5 orders · 2 products · 2 labs | Tiny synthetic demo | Sanity-check the UI without any setup. Loaded automatically by the **"Use demo data"** toggle. |
| `data/sample/clothing_production_planning_database_cleaned.xlsx` | 60 orders · 16 products · 10 labs · 373 phase-capacity rows | Realistic test database | Stress-test the dashboard with production-like volumes (bottlenecks, REJECT/SPLIT recommendations, late deadlines). |

## How to load data (3 ways)

**Option A — Quick demo (zero steps).**
On the running app, go to **Upload Data** and toggle
**"Use demo data instead of uploading"**. The dashboard loads
`sample_planning.xlsx` automatically.

**Option B — Realistic dataset (recommended for demos & presentations).**
1. Start the app: `streamlit run app.py`.
2. Open the **Upload Data** page.
3. Leave the demo toggle **off**.
4. Click **"Browse files"** and select
   `data/sample/clothing_production_planning_database_cleaned.xlsx`
   from this repo.
5. Navigate to **Capacity Dashboard** / **Phase Saturation** /
   **Timeline** to see the full pipeline running on realistic data.

**Option C — Your own Excel workbook.**
The parser accepts any `.xlsx` with the four canonical sheets
(`orders`, `product_matrix`, `labs` *or* `labs_factories`, `phase_capacity`).
Italian column names (`cliente`, `quantità`, `scadenza`, …) are auto-mapped
to the canonical English schema. Missing sheets fall back to the bundled
demo. Lab ids referenced by `phase_capacity` or `orders` but absent from
the labs sheet are auto-created with the defaults in `config/defaults.yaml`
— no warnings emitted.

## Project structure

```text
/project
    app.py
    requirements.txt
    README.md

    /docs
        MASTER_PRD_v2_EXECUTION.md
        TASKS.md
        PRESENTATION_AUDIT.md
        CLOUD_CODE_MASTER_PROMPT.md

    /data
        /sample
        /uploaded

    /config
        defaults.yaml

    /src
        /parsers
            excel_parser.py
            normalizer.py

        /engines
            product_matrix_engine.py
            capacity_engine.py
            bottleneck_engine.py
            lab_allocation_engine.py
            stress_engine.py
            recommendation_engine.py
            timeline_engine.py
            scenario_engine.py

        /components
            kpi_cards.py
            charts.py
            alerts.py
            timeline.py

        /ui
            /pages
                overview.py
                upload.py
                capacity_dashboard.py
                phase_saturation.py
                timeline.py
                scenario_testing.py
                future_ai.py

        /utils
            config.py
            constants.py
            validation.py
            formatting.py

    /assets
        /mockups

    /scripts
        build_sample_data.py

    /tests
        test_capacity_engine.py
        test_recommendation_engine.py
        test_normalizer.py
```

## Configuration

All operational defaults (working hours, efficiency, utilization thresholds,
parallel-order limits, etc.) live in [`config/defaults.yaml`](./config/defaults.yaml)
and are loaded once via `src/utils/config.py`. Tune them without code changes;
status thresholds shared with the UI are mirrored in `src/utils/constants.py`.

## Deployment (Railway)

`railway.json` configures a NIXPACKS build and launches Streamlit on the
container's `$PORT`. Push the repo to Railway, point a service at it, and it
deploys with no further setup. Headless mode + usage-stats opt-out are
already wired into the start command.

## Out of scope

The following are intentionally **not** part of the MVP:

- user authentication
- cloud deployment
- database persistence
- ERP integration
- real-time synchronization
- advanced ML pipelines
- optimization algorithms
- automatic scheduling optimization
- production-grade access control
- multi-tenant SaaS architecture
- real legal compliance engine

## Future work

The **Future AI Layer** page inside the running dashboard documents the
planned expansion path: predictive delay risk, anomaly detection,
forecasting, optimization engine, and a digital twin simulation environment.
These features require historical delivery data not currently available in
the Excel workflow being digitalized; they are deliberately deferred to a
later phase.
