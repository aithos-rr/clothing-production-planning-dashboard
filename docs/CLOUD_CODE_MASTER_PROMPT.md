# CLOUD_CODE_MASTER_PROMPT.md

## Master Prompt for Claude Code / Cloud Code

You are working on an operational planning dashboard MVP for fashion manufacturing.

Read and strictly follow:

```text
docs/MASTER_PRD_v2_EXECUTION.md
docs/PRD_ECONOMIC_LAYER_v2.md
```

and:

```text
docs/TASKS.md
```

The PRDs are the single source of truth.

---

# Project Overview

This project is NOT:
- a generic analytics dashboard
- an ERP
- an AI experiment
- an enterprise platform

This project IS:
> a lightweight operational decision-support platform for sustainable capacity planning.

The dashboard replaces fragmented Excel workflows with:
- centralized planning
- phase-based capacity calculations
- bottleneck analysis
- operational stress monitoring
- recommendation logic
- scenario simulation

---

# Core Technical Stack

Frontend:
- Streamlit

Backend:
- Python

Data:
- Pandas DataFrames

Visualization:
- Plotly

Excel Parsing:
- Openpyxl

---

# Architecture Principles

## 1. Keep It Modular

Separate:
- parsers
- engines
- UI components
- utilities

Avoid monolithic files.

---

## 2. Keep It Simple

DO NOT:
- overengineer
- introduce unnecessary abstractions
- build enterprise architecture
- add authentication
- add databases
- add APIs
- add cloud deployment

This is an MVP.

---

## 3. Respect the Existing Workflow

The system must preserve the logic already present in the Excel workflows.

The dashboard is:
> a digitalization and orchestration layer,
not a complete reinvention.

---

## 4. Prioritize Operational Clarity

The UI must feel:
- minimal
- modern
- fast
- readable
- operational

Avoid:
- ERP aesthetics
- excessive charts
- visual clutter

References:
- Linear
- Notion
- Stripe Dashboard

---

# UI Priorities

Most important sections:
1. Capacity Overview
2. Phase Saturation
3. Timeline View
4. Operational Stress Alerts
5. Recommendation Panel
6. Scenario Testing

---

# Operational Stress Engine

This replaces the original ML delay prediction system.

The system must evaluate:
- overload
- overtime
- machine downtime
- worker absence
- bottleneck concentration
- sustainability risks

Use:
- deterministic logic
- thresholds
- rule-based alerts

NOT:
- predictive AI models

---

# Coding Rules

## Use Type Hints
Where appropriate.

---

## Keep Functions Small

Functions should:
- do one thing
- be readable
- be reusable

---

## Separate Business Logic

Keep:
- calculation engines
- recommendation logic
- stress logic

outside Streamlit UI code.

---

## Avoid Hardcoding

Use:
- config files
- constants
- mappings

when possible.

---

# Git Workflow

- Small commits
- One feature per commit
- Respect TASKS.md order

---

# Task Execution Workflow

For every task:

1. Read task requirements
2. Check dependencies
3. Implement minimal working version
4. Validate acceptance criteria
5. Update TASKS.md status
6. Proceed to next task

---

# Important MVP Constraints

DO NOT IMPLEMENT:
- real ML pipelines
- optimization engines
- forecasting systems
- ERP integrations
- authentication systems
- cloud infrastructure

These belong to:
> Future AI Expansion Layer.

---

# Future AI Layer

The dashboard must include a placeholder/mock section for future AI features:

- predictive delays
- anomaly detection
- forecasting
- optimization
- AI recommendations

This section is:
- visual only
- non-functional in MVP
- strategically important

---

# Final Goal

Build:
> a clean, modular, operational planning dashboard
that feels like a real internal SaaS tool for fashion manufacturing operations.

The product should be:
- realistic
- elegant
- understandable
- extensible
- sustainability-aware

Prioritize:
- usability
- operational clarity
- maintainability
- execution speed
over technical complexity.
