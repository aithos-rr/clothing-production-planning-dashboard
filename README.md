# Clothing Production Planning Dashboard

Lightweight operational planning platform for fashion manufacturing. Replaces fragmented Excel workflows with a centralized Streamlit dashboard for capacity calculation, bottleneck analysis, operational stress monitoring, and rule-based recommendations.

> **Status:** planning phase — implementation tracked in [`TASKS.md`](./TASKS.md).

## Documents

- [`MASTER_PRD_v2_EXECUTION.md`](./MASTER_PRD_v2_EXECUTION.md) — single source of truth (vision, scope, data schema, module contracts).
- [`TASKS.md`](./TASKS.md) — 40-task iterative implementation plan across 9 phases.
- [`CLOUD_CODE_MASTER_PROMPT.md`](./CLOUD_CODE_MASTER_PROMPT.md) — execution rules for AI coding agents.

## Tech Stack

- **Frontend:** Streamlit
- **Backend:** Python (Pandas, NumPy)
- **Visualization:** Plotly
- **Excel I/O:** Openpyxl
- **Config:** PyYAML

## Run Locally (once implemented)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Use the **Demo mode** toggle on the Upload page to explore the dashboard without real data.

## Project Structure (target)

```
/
├── app.py                       # Streamlit entry point
├── requirements.txt
├── config/
│   └── defaults.yaml            # Thresholds & operational defaults
├── data/
│   ├── sample/                  # Committed sample dataset
│   └── uploaded/                # User uploads (gitignored)
├── src/
│   ├── parsers/                 # Excel parser + normalizer
│   ├── engines/                 # Capacity, bottleneck, stress, recommendation, timeline, scenario
│   ├── components/              # Reusable Streamlit widgets
│   ├── ui/pages/                # Streamlit page modules
│   └── utils/                   # Config, constants, validation, formatting
└── tests/
```

## Out of Scope (MVP)

No authentication, no database, no cloud deployment, no ML pipelines, no ERP integration. These belong to the Future AI Expansion Layer described in the PRD.

## Contributing / Agent Workflow

AI coding agents should follow the loop protocol at the bottom of `TASKS.md`: pick the first `TODO` task whose dependencies are `DONE`, implement, verify acceptance criteria, mark `DONE`, commit, stop.
