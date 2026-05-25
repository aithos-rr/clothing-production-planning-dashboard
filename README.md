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

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

(Optional, one-shot) regenerate the bundled sample dataset:

```bash
python scripts/build_sample_data.py
```

## Try it without data

Open the **Upload Data** page and toggle **"Use demo data instead of
uploading"**. The dashboard loads the bundled sample workbook
(`data/sample/sample_planning.xlsx`) — five orders × two product types ×
four phases × two labs — so every downstream page renders without any
real data being uploaded.

## Project structure

```text
/project
    app.py
    requirements.txt
    README.md
    MASTER_PRD_v2_EXECUTION.md
    TASKS.md

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
