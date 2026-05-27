# MASTER_PRD_v2_EXECUTION.md

## Sustainable Capacity Planning & Operational Decision Support Platform  
### Fashion Manufacturing Operations Dashboard  
### Execution-Oriented PRD for Claude Code / Cloud Code  
### MVP Version — University Project + Future Commercial Expansion

---

# 0. How to Use This PRD

This document is the **single source of truth** for the development of the MVP.

It is written as an execution-oriented PRD for AI-assisted development with Claude Code / Cloud Code.

The coding agent must:

- read this file before writing code
- follow the MVP scope strictly
- avoid overengineering
- preserve the operational logic of the existing Excel workflow
- build a working local Streamlit prototype
- prioritize clarity, usability, and deterministic calculations over advanced AI features

This project is **not** a generic dashboard.  
It is a **fashion manufacturing operational planning tool** that transforms fragmented Excel workflows into a centralized, interactive, and sustainability-aware decision-support dashboard.

---

# 1. Product Vision

## 1.1 Vision

The goal of this project is to transform the company’s current Excel-based production planning workflow into a centralized, interactive, and scalable operational decision-support platform.

The system supports Product Managers and planning teams in:

- evaluating real production capacity
- monitoring workload saturation
- identifying bottlenecks
- planning production chains
- avoiding operational overload
- improving sustainability and compliance
- simulating operational disruptions
- generating clear recommendations

The platform replaces fragmented Excel logic with a modern dashboard architecture capable of integrating:

- operational calculations
- production phase logic
- sustainability constraints
- compliance-aware risk rules
- recommendation systems
- future AI/ML expansion layers

---

## 1.2 Product Positioning

This product is **not**:

- a full ERP system
- a database-heavy enterprise platform
- a real-time production control system
- a pure Machine Learning project
- an AI forecasting product in the MVP phase

This product **is**:

> a lightweight operational planning platform specialized for fashion manufacturing workflows.

The MVP focuses on:

- deterministic planning logic
- Excel upload and parsing
- phase-based capacity calculation
- bottleneck and saturation analysis
- operational stress evaluation
- sustainability-aware recommendations
- a clean and usable dashboard

The system intentionally leaves open a future commercial layer for:

- predictive delay models
- anomaly detection
- forecasting
- scheduling optimization
- AI recommendation engines
- ERP/database integration

---

# 2. Final MVP Scope Freeze

## 2.1 Included in the MVP

The MVP must include:

1. **Excel Upload**
   - Upload production planning Excel files.
   - Accept `.xlsx` files.
   - Parse available sheets into normalized DataFrames.

2. **Data Validation**
   - Detect missing columns.
   - Detect invalid values.
   - Show clear user-facing warnings.

3. **Product Matrix Engine**
   - Extract product types.
   - Extract production phases.
   - Extract phase timing information.

4. **Capacity Engine**
   - Calculate required capacity.
   - Calculate available capacity.
   - Calculate utilization rate.
   - Calculate capacity gap.

5. **Phase Saturation Engine**
   - Calculate saturation per production phase.
   - Identify overloaded phases.

6. **Bottleneck Engine**
   - Identify the most critical phase.
   - Identify the most constrained resource.

7. **Operational Stress & Compliance Engine**
   - Replace the originally planned ML delay risk with a rule-based operational stress system.
   - Evaluate overtime, overload, machine downtime, worker absence, and oversized orders.

8. **Recommendation Engine**
   - Generate recommendations:
     - Accept
     - At Risk
     - Reallocate
     - Split Order
     - Postpone
     - Reject

9. **Timeline / Scheduling View**
   - Visualize orders over time.
   - Show overlaps and planning windows.
   - Provide a lightweight Gantt-style view.

10. **Scenario Testing**
    - Simulate:
      - demand increase
      - efficiency drop
      - worker absence
      - machine downtime

11. **Dashboard UI**
    - Minimal Streamlit interface.
    - Clean navigation.
    - Clear operational cards.
    - Status colors:
      - green = safe
      - orange = at risk
      - red = critical

12. **Future AI Layer Placeholder**
    - Show a non-functional placeholder section explaining future AI/ML opportunities.

---

## 2.2 Explicitly Excluded from the MVP

Do **not** implement:

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

These features belong to the **Future Expansion Layer**.

---

# 3. Current Workflow Analysis

## 3.1 Current Excel-Based Workflow

The company currently manages production planning through multiple interconnected Excel files.

These Excel systems already contain operational intelligence such as:

- phase-based production logic
- product routing
- timing per product and phase
- saturation percentages
- worker allocation
- timeline planning
- production chain scheduling

The new dashboard should not ignore this logic.  
It should **preserve and modernize** it.

The purpose of the MVP is therefore:

> to convert an existing manual Excel planning process into a centralized, interactive, and user-friendly operational dashboard.

---

## 3.2 Current Problems

The current Excel workflow is functional but limited by:

- fragmented logic across multiple sheets
- manual updates
- low readability
- difficult sharing
- poor scalability
- fragile formulas
- limited scenario testing
- difficult cross-order visibility
- lack of a centralized recommendation layer
- lack of explicit sustainability/compliance logic

---

## 3.3 Existing Excel Components Identified

### A. Product Matrix

Contains:

- product categories
- production phases
- phase-specific processing times
- product routing logic

Example production phases include:

- imbastitura
- apertura TX doppia
- adesivazione
- rifilo
- preparazione
- confezione capo
- controllo misure
- asole e bottoni
- punti a mano

This acts as:

> the production routing matrix.

---

### B. Capacity & Saturation Planning

Contains:

- total workers per phase
- assigned workers per phase
- saturation percentage
- phase crossing time
- workable minutes
- unit processing time
- total order requirement
- productive capacity need

This acts as:

> the operational capacity engine.

---

### C. Timeline / Chain Planning

Contains:

- order scheduling
- planning timeline
- overlapping orders
- production progression
- chain-level planning

This acts as:

> the scheduling layer.

---

# 4. Target Users

## 4.1 Primary User — Product Manager

The Product Manager is the main operational user.

Needs:

- fast understanding of current capacity
- immediate identification of overloaded phases
- ability to test new orders
- clear recommendation on what to do
- ability to communicate decisions internally
- low-friction interface

---

## 4.2 Secondary Users

### Production Planning Team

Needs:

- workload distribution
- timeline visibility
- order overlap visibility
- operational bottleneck awareness

### Management

Needs:

- production visibility
- risk visibility
- strategic decision support
- proof of sustainable planning logic

---

# 5. Final System Architecture

## 5.1 High-Level Architecture

```text
Excel / CSV Inputs
        ↓
Data Parsing Layer
        ↓
Data Normalization Layer
        ↓
Product Matrix Engine
        ↓
Phase-Based Capacity Engine
        ↓
Lab / Chain Allocation Engine
        ↓
Saturation & Bottleneck Engine
        ↓
Operational Stress & Compliance Engine
        ↓
Recommendation Engine
        ↓
Timeline / Scheduling Layer
        ↓
Streamlit Dashboard UI
```

---

## 5.2 Technical Stack

### Frontend

- Streamlit

### Backend

- Python

### Data Processing

- Pandas
- NumPy

### Visualization

- Plotly

### Excel Handling

- Openpyxl

### Optional Future Layer

- Scikit-learn

---

# 6. Data Flow

## 6.1 Runtime Data Flow

```text
User uploads Excel file
        ↓
System reads workbook sheets
        ↓
Parser extracts raw tables
        ↓
Normalizer converts them into standard DataFrames
        ↓
Engines calculate capacity, saturation, bottlenecks, stress, and recommendations
        ↓
Dashboard renders metrics, charts, alerts, and timeline
        ↓
User adjusts scenarios
        ↓
Calculations update dynamically
```

---

## 6.2 Data Strategy

Because company data may be incomplete, the MVP must support two modes:

### Mode A — Real Excel Mode

Uses uploaded Excel files when available.

### Mode B — Mock / Demo Mode

Uses sample data when:

- real data is unavailable
- uploaded Excel has missing information
- development/testing is required

The system must not fail completely when data is incomplete.  
It must degrade gracefully using configurable default values.

---

# 7. Data Schema

The system should normalize all inputs into the following core DataFrames.

---

## 7.1 `orders_df`

Represents production orders.

| Column | Type | Required | Source | Fallback |
|---|---:|---:|---|---|
| order_id | string | yes | Excel / generated | auto-generate |
| client | string | no | Excel / user input | `"Unknown Client"` |
| product_type | string | yes | Excel / user input | raise warning |
| quantity | int | yes | Excel / user input | raise warning |
| start_date | date | no | Excel / user input | today |
| deadline | date | yes | Excel / user input | raise warning |
| assigned_lab | string | no | Excel / user input | `"Default Lab"` |
| assigned_chain | string | no | Excel / user input | `"Default Chain"` |
| progress_percentage | float | no | Excel | `0.0` |
| priority | string | no | user input | `"normal"` |

---

## 7.2 `product_matrix_df`

Represents product routing and phase timing.

| Column | Type | Required | Source | Fallback |
|---|---:|---:|---|---|
| product_type | string | yes | Product matrix Excel | raise warning |
| phase_name | string | yes | Product matrix Excel | raise warning |
| min_time_minutes | float | no | Product matrix Excel | use average |
| max_time_minutes | float | no | Product matrix Excel | use average |
| avg_time_minutes | float | yes | Product matrix Excel | compute from min/max |
| setup_time_minutes | float | no | Product matrix Excel / config | `0.0` |
| phase_order | int | no | Product matrix Excel / inferred | infer order |

---

## 7.3 `labs_df`

Represents laboratory or chain capacity.

| Column | Type | Required | Source | Fallback |
|---|---:|---:|---|---|
| lab_id | string | yes | Lab registry / config | `"Default Lab"` |
| lab_name | string | no | Lab registry / config | same as lab_id |
| working_hours_per_day | float | yes | Lab registry / config | `8.0` |
| working_days_per_week | int | no | Lab registry / config | `5` |
| default_efficiency | float | no | Lab registry / config | `0.75` |
| machine_uptime | float | no | Lab registry / config | `0.90` |
| max_weekly_hours | float | no | config | `48.0` |
| overtime_allowed | bool | no | config | `False` |

---

## 7.4 `phase_capacity_df`

Represents capacity by lab and phase.

| Column | Type | Required | Source | Fallback |
|---|---:|---:|---|---|
| lab_id | string | yes | Lab registry / config | `"Default Lab"` |
| phase_name | string | yes | Lab registry / product matrix | raise warning |
| workers_total | int | yes | Lab registry / config | `1` |
| workers_assigned | int | no | Lab registry / config | workers_total |
| machines_total | int | no | Lab registry / config | `0` |
| available_minutes_per_day | float | yes | calculated | computed |
| efficiency | float | no | Lab registry / config | `0.75` |
| uptime | float | no | Lab registry / config | `0.90` |

---

## 7.5 `capacity_results_df`

Represents calculated capacity results per order and phase.

| Column | Type |
|---|---:|
| order_id | string |
| product_type | string |
| phase_name | string |
| quantity | int |
| required_minutes | float |
| available_minutes | float |
| utilization_rate | float |
| capacity_gap_minutes | float |
| is_overloaded | bool |
| is_bottleneck | bool |

---

## 7.6 `timeline_df`

Represents scheduling information.

| Column | Type |
|---|---:|
| order_id | string |
| product_type | string |
| assigned_lab | string |
| start_date | date |
| end_date | date |
| deadline | date |
| duration_days | int |
| overlap_flag | bool |
| status | string |

---

## 7.7 `stress_events_df`

Represents rule-based operational stress warnings.

| Column | Type |
|---|---:|
| event_id | string |
| order_id | string |
| event_type | string |
| severity | string |
| message | string |
| triggered_by | string |
| recommended_action | string |

---

## 7.8 `recommendations_df`

Represents final decision output.

| Column | Type |
|---|---:|
| order_id | string |
| recommendation | string |
| severity | string |
| reasons | list/string |
| suggested_actions | list/string |

---

# 8. Default Configuration Values

Use default values when data is missing.

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

All thresholds must be centralized in a config file or constants module.

Do not hardcode thresholds throughout the codebase.

---

# 9. Module Contracts

Each module must have a clear responsibility.

---

## 9.1 Parser Module

Suggested file:

```text
src/parsers/excel_parser.py
```

### Responsibility

- read uploaded Excel files
- list available sheets
- extract raw tables
- return raw DataFrames

### Input

- uploaded `.xlsx` file

### Output

- dictionary of raw DataFrames

```python
{
    "sheet_name": dataframe
}
```

### Must Not

- perform business calculations
- generate recommendations

---

## 9.2 Normalization Module

Suggested file:

```text
src/parsers/normalizer.py
```

### Responsibility

- convert raw Excel tables into standardized DataFrames
- map column names
- clean missing values
- validate required columns

### Input

- raw DataFrame dictionary

### Output

- normalized DataFrames:
  - orders_df
  - product_matrix_df
  - labs_df
  - phase_capacity_df

### Must Not

- calculate recommendations
- render UI

---

## 9.3 Product Matrix Engine

Suggested file:

```text
src/engines/product_matrix_engine.py
```

### Responsibility

- identify product phases
- compute average time per phase
- generate production routing

### Input

- product_matrix_df
- product_type

### Output

- list/DataFrame of phases for selected product

---

## 9.4 Capacity Engine

Suggested file:

```text
src/engines/capacity_engine.py
```

### Responsibility

- calculate required minutes
- calculate available minutes
- calculate utilization rate
- calculate capacity gap

### Input

- orders_df
- product_matrix_df
- labs_df
- phase_capacity_df

### Output

- capacity_results_df

### Formulas

```text
required_minutes = quantity × avg_time_minutes + setup_time_minutes

available_minutes = workers_assigned × working_hours_per_day × 60 × efficiency × uptime × available_days

utilization_rate = required_minutes / available_minutes

capacity_gap_minutes = available_minutes - required_minutes
```

---

## 9.5 Bottleneck Engine

Suggested file:

```text
src/engines/bottleneck_engine.py
```

### Responsibility

- identify the phase with highest utilization
- flag bottleneck phases
- rank phases by operational criticality

### Input

- capacity_results_df

### Output

- capacity_results_df with:
  - is_bottleneck
  - bottleneck_rank

---

## 9.6 Operational Stress Engine

Suggested file:

```text
src/engines/stress_engine.py
```

### Responsibility

Evaluate rule-based operational stress.

### Input

- capacity_results_df
- orders_df
- timeline_df
- config values
- scenario inputs

### Output

- stress_events_df

### Stress Rules

Trigger warnings for:

- utilization > 85%
- utilization > 100%
- phase utilization > 90%
- overtime required
- machine downtime scenario active
- worker absence scenario active
- more than 2 parallel orders on same lab
- deadline infeasible

---

## 9.7 Recommendation Engine

Suggested file:

```text
src/engines/recommendation_engine.py
```

### Responsibility

Generate final recommendation.

### Input

- capacity_results_df
- stress_events_df
- timeline_df

### Output

- recommendations_df

### Decision Logic

```text
IF utilization < 85%
AND no critical stress events
AND no bottleneck overload
THEN ACCEPT

IF utilization between 85% and 100%
OR medium stress events exist
THEN AT RISK / SPLIT / REALLOCATE

IF utilization > 100%
OR overtime required
OR compliance risk exists
THEN POSTPONE / REJECT
```

---

## 9.8 Timeline Engine

Suggested file:

```text
src/engines/timeline_engine.py
```

### Responsibility

- calculate estimated duration
- generate start/end dates
- detect overlaps
- prepare data for timeline visualization

### Input

- orders_df
- capacity_results_df

### Output

- timeline_df

---

## 9.9 Scenario Engine

Suggested file:

```text
src/engines/scenario_engine.py
```

### Responsibility

Apply scenario modifiers.

### Scenario Inputs

- demand_multiplier
- efficiency_drop
- absent_workers
- machine_downtime
- urgent_order_flag

### Output

- modified DataFrames used for recalculation

---

# 10. Core Logic

## 10.1 Capacity Formula

```text
Capacity = Workers × Available Hours × Efficiency × Uptime
```

---

## 10.2 Required Capacity

```text
Required Capacity = Quantity × Unit Time + Setup Time
```

---

## 10.3 Utilization Rate

```text
Utilization Rate = Required Capacity / Available Capacity
```

---

## 10.4 Capacity Gap

```text
Capacity Gap = Available Capacity - Required Capacity
```

---

## 10.5 Bottleneck Logic

The bottleneck is defined as:

> the production phase with the highest utilization rate and lowest residual capacity.

---

## 10.6 Phase-Based Planning

Each order must be decomposed into:

- product type
- required production phases
- phase-specific timing
- phase-specific capacity
- phase-level saturation
- phase-level bottleneck risk

The system must not treat orders only as a single total number.  
The order must be evaluated at production-phase level.

---

# 11. Operational Stress & Compliance Engine

## 11.1 Purpose

The Operational Stress & Compliance Engine replaces the originally planned ML delay risk system.

The goal is not to statistically predict delays in the MVP.

The goal is to detect operational conditions that can create:

- worker overload
- overtime pressure
- unsafe workload redistribution
- bottleneck concentration
- unrealistic production compression
- sustainability risks

---

## 11.2 Risk Categories

### A. Last-Minute Orders

Risk:

- compressed schedules
- overtime
- loss of planning buffer

Dashboard alert example:

```text
Last-minute order creates high operational stress.
Order not feasible without overtime.
```

---

### B. Machine Downtime

Risk:

- reduced productive capacity
- unsafe reallocation
- unrealistic productivity assumptions

Dashboard alert example:

```text
Machine downtime reduces available capacity by X%.
Do not allocate production to unavailable machines.
```

---

### C. Worker Absence

Risk:

- reduced labor capacity
- overload of remaining workers

Dashboard alert example:

```text
Worker absence reduces phase capacity.
Recommendation: postpone or reallocate.
```

---

### D. Oversized Orders

Risk:

- excessive saturation
- overtime
- quality loss
- social sustainability violation

Dashboard alert example:

```text
Order exceeds sustainable capacity.
Recommendation: split or postpone.
```

---

# 12. Recommendation Logic

## 12.1 Recommendation Types

### ACCEPT

Conditions:

- utilization < 85%
- no bottleneck above threshold
- no critical stress events
- no overtime required

---

### AT RISK

Conditions:

- utilization between 85% and 100%
- bottleneck warning
- medium stress events

---

### REALLOCATE

Conditions:

- specific lab/phase overloaded
- alternative capacity exists
- order can be moved partially or fully

---

### SPLIT ORDER

Conditions:

- single lab overloaded
- total order too large
- production can be divided across labs/chains

---

### POSTPONE

Conditions:

- timeline infeasible
- deadline too close
- capacity available only after deadline

---

### REJECT

Conditions:

- utilization > 100%
- overtime required
- compliance/sustainability violation
- no viable reallocation or postponement

---

# 13. Streamlit Application Architecture

## 13.1 Recommended App Structure

Use a multi-page or tabbed Streamlit app.

Recommended pages:

1. **Overview**
2. **Upload Data**
3. **Capacity Dashboard**
4. **Phase Saturation**
5. **Timeline**
6. **Scenario Testing**
7. **Future AI Layer**

---

## 13.2 Page Requirements

### Page 1 — Overview

Displays:

- project title
- short explanation
- current dataset status
- high-level KPIs

---

### Page 2 — Upload Data

Allows:

- upload Excel file
- inspect sheets
- validate columns
- choose demo/mock mode

Must show:

- upload success
- missing columns
- warnings
- parsed sheet preview

---

### Page 3 — Capacity Dashboard

Displays:

- total utilization
- capacity gap
- estimated production days
- number of overloaded phases
- overall recommendation

---

### Page 4 — Phase Saturation

Displays:

- utilization by phase
- bottleneck phase
- capacity gap by phase
- workers at risk flag

Recommended charts:

- horizontal bar chart
- status cards

---

### Page 5 — Timeline

Displays:

- lightweight Gantt-style timeline
- order start/end
- deadlines
- overlaps

---

### Page 6 — Scenario Testing

Allows user to modify:

- demand increase
- efficiency drop
- worker absence
- machine downtime

Must update:

- utilization
- stress events
- recommendation

---

### Page 7 — Future AI Layer

Non-functional placeholder explaining possible future extensions:

- predictive delays
- anomaly detection
- forecasting
- optimization
- AI recommendations
- digital twin simulation

This section is strategically important and must be visually polished.

---

# 14. UI/UX Requirements

The dashboard must be:

- minimal
- modern
- operational
- fast to read
- neutral and elegant
- usable by non-technical Product Managers

Avoid:

- clutter
- excessive chart density
- ERP-style visual design
- too many colors
- technical jargon in the UI

Status colors:

```text
Green  = safe
Orange = at risk
Red    = critical
Gray   = neutral / inactive
```

The recommendation panel should be the most visually important decision area.

---

# 15. Folder Structure

Use this structure unless there is a strong reason to simplify further.

```text
/project
    app.py
    requirements.txt
    README.md
    MASTER_PRD.md
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
            stress_engine.py
            recommendation_engine.py
            timeline_engine.py
            scenario_engine.py

        /components
            kpi_cards.py
            charts.py
            alerts.py
            timeline.py

        /utils
            validation.py
            formatting.py
            constants.py

    /assets
        /mockups

    /tests
        test_capacity_engine.py
        test_recommendation_engine.py
```

---

# 16. Error Handling & Edge Cases

The app must handle:

## File Upload Errors

- unsupported file type
- unreadable Excel file
- empty workbook
- missing sheets

## Data Errors

- missing product type
- missing quantity
- missing deadline
- invalid date
- quantity <= 0
- product not found in product matrix
- phase not mapped to capacity
- missing lab assignment

## Calculation Errors

- available capacity = 0
- utilization division by zero
- negative capacity gap
- utilization > 100%
- missing efficiency
- missing uptime

## UI Behavior

Errors should be shown as:

- clear warnings
- not raw stack traces
- actionable messages

Example:

```text
Product type not found in product matrix. Please check spelling or add this product to the matrix.
```

---

# 17. Acceptance Criteria

The MVP is complete when the following are true.

## Upload & Parsing

- User can upload an Excel file.
- App reads at least one workbook successfully.
- App shows available sheets.
- App can fall back to demo data if parsing fails.

## Data Normalization

- App creates standard DataFrames.
- Missing required columns are detected.
- User sees readable warnings.

## Capacity Engine

- Required minutes are calculated correctly.
- Available minutes are calculated correctly.
- Utilization rate is calculated correctly.
- Capacity gap is calculated correctly.

## Bottleneck Engine

- Phase with highest utilization is identified.
- Overloaded phases are flagged.
- Bottleneck appears clearly in UI.

## Operational Stress Engine

- Utilization > 85% triggers warning.
- Utilization > 100% triggers critical alert.
- Worker absence scenario reduces capacity.
- Machine downtime scenario reduces capacity.
- Overtime requirement blocks Accept recommendation.

## Recommendation Engine

- Accept is only possible when no critical stress exists.
- Utilization > 100% cannot produce Accept.
- Critical stress produces Postpone, Split, Reallocate, or Reject.
- Recommendation includes reasons.

## Dashboard UI

- App is usable by non-technical users.
- Recommendation panel is clear.
- Status colors are consistent.
- Scenario testing updates outputs dynamically.

## Future AI Layer

- Future AI page exists.
- It clearly states that AI features are not implemented in MVP.
- It presents future expansion opportunities professionally.

---

# 18. Development Phases

## Phase 1 — Project Foundation

- initialize repo structure
- create Streamlit app skeleton
- create config/default values
- create sample data

## Phase 2 — Data Layer

- build Excel parser
- build data normalizer
- build validation utilities

## Phase 3 — Core Calculation Layer

- product matrix engine
- capacity engine
- bottleneck engine

## Phase 4 — Operational Stress Layer

- stress rules
- compliance-aware warnings
- scenario modifiers

## Phase 5 — Recommendation Layer

- decision rules
- explanation generation
- output standardization

## Phase 6 — UI Layer

- overview page
- upload page
- capacity dashboard
- phase saturation view
- timeline view
- scenario testing
- future AI page

## Phase 7 — Testing & Polish

- test with sample data
- test edge cases
- improve UX
- create README
- finalize presentation-ready MVP

---

# 19. Future AI Expansion Layer

This layer is **not implemented in the MVP**.

It must be described and visually represented as future potential.

Future features may include:

## Predictive Delay Risk

A classification model trained on historical orders to estimate probability of delay.

Required future data:

- historical orders
- actual delivery dates
- delay causes
- product complexity
- lab performance
- seasonal workload

---

## Anomaly Detection

Detect unusual patterns such as:

- abnormal processing times
- repeated bottlenecks
- sudden capacity drops
- recurring delay sources

---

## Forecasting

Predict:

- future workload
- lab saturation
- seasonal production peaks
- capacity shortages

---

## Optimization Engine

Suggest:

- optimal lab allocation
- best order splitting strategy
- least stressful production schedule
- capacity rebalancing

---

## Digital Twin Simulation

Create a simulation environment for:

- testing disruptions
- planning production scenarios
- analyzing resilience

---

# 20. Strategic Value

The platform transforms:

```text
fragmented Excel workflows
```

into:

```text
a centralized operational planning system
```

The project demonstrates:

- workflow digitalization
- operational transparency
- sustainability-aware planning
- compliance-aware production logic
- scalable decision support

It also creates a foundation for:

- future AI integration
- future enterprise expansion
- future paid collaboration with the company

---

# 21. Final Implementation Principle

Build the simplest version that demonstrates the full operational logic.

Prioritize:

1. correct calculations
2. readable UI
3. clear recommendations
4. graceful handling of missing data
5. future extensibility

Do not prioritize:

- complex infrastructure
- advanced AI
- perfect parsing of every Excel variation
- enterprise deployment
- unnecessary abstractions

The MVP should feel like:

> a real internal SaaS prototype for sustainable fashion manufacturing operations.
