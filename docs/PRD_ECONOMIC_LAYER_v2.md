#   
  
  
## PRD — Cost Feasibility Dashboard  
## Economic Layer for the Clothing Manufacturing System Dashboard  
  
⸻  
  
## 1. Purpose of the Page  
The **Cost Feasibility Dashboard** is a new page of the Clothing Manufacturing System Dashboard designed to evaluate the economic impact of production decisions.  
The existing dashboard already evaluates:  
* productive feasibility;  
* capacity saturation;  
* bottlenecks;  
* operational stress;  
* scenario risk;  
* recommendation logic.  
This new page adds an economic layer by answering a further managerial question:  
“The order may be technically feasible, but is it economically sustainable?”  
The goal is to transform the dashboard from a capacity risk management tool into a broader **production decision-support system**, able to compare operational feasibility with cost impact and estimated margin.  
  
⸻  
  
## 2. Page Positioning inside the Dashboard  
The new page should be added to the dashboard navigation as:  
**Cost Feasibility Dashboard**  
Recommended placement in the navigation:  
1. Overview  
2. Upload Data  
3. Capacity Dashboard  
4. Phase Saturation  
5. Timeline  
6. Scenario Testing  
7. **Cost Feasibility Dashboard**  
8. Future AI Layer  
This page should use the same visual language as the rest of the dashboard:  
* minimal;  
* clean;  
* managerial;  
* KPI-driven;  
* neutral colors with green/orange/red only for status logic.  
  
⸻  
  
## 3. Business Problem Solved  
Production decisions are not only technical. An order can be:  
* feasible in terms of capacity;  
* risky in terms of workload;  
* expensive because it requires overtime;  
* less convenient if allocated to a more costly laboratory;  
* economically unsustainable if the margin becomes too low.  
The new page helps Product Managers and managers evaluate:  
* estimated production cost;  
* cost of overtime;  
* impact of reallocation;  
* margin reduction;  
* cost difference between laboratories;  
* economic sustainability of the order.  
This allows Pattern to make decisions that balance:  
* capacity;  
* risk;  
* cost;  
* profitability;  
* operational sustainability.  
  
⸻  
  
## 4. MVP Scope of the Page  
## Included in MVP  
The Cost Feasibility Dashboard must calculate and display:  
* required production hours;  
* standard labour cost;  
* overtime hours;  
* overtime cost;  
* setup cost;  
* overhead cost;  
* total estimated production cost;  
* estimated margin;  
* margin percentage;  
* average cost per garment;  
* cost impact of reallocation;  
* economic recommendation.  
  
⸻  
  
## Excluded from MVP  
Do not implement in this version:  
* advanced cost accounting;  
* real ERP integration;  
* live accounting data;  
* automatic price optimization;  
* financial forecasting;  
* AI-based cost prediction;  
* supplier cost negotiation automation;  
* full profit & loss simulation.  
These can remain part of a future business expansion layer.  
  
⸻  
  
## 5. Required Inputs  
The page must reuse existing dashboard calculations where possible.  
The current system already calculates:  
* required minutes;  
* available minutes;  
* utilization rate;  
* capacity gap;  
* overtime requirement;  
* recommended allocation;  
* bottleneck phase.  
The economic page adds a limited number of additional inputs.  
  
⸻  
  
## 5.1 Minimum Required Inputs  
For a first working version, the page requires:  
**From existing capacity engine**  
* order_id;  
* product_type;  
* quantity;  
* required_minutes;  
* required_hours;  
* available_hours;  
* excess_hours;  
* assigned_lab;  
* recommended_lab, if available.  
**New economic inputs**  
* hourly_labour_cost;  
* overtime_multiplier;  
* setup_cost;  
* overhead_percentage;  
* order_value.  
  
⸻  
  
## 6. Data Schema Extension  
The following fields should be added or mocked in the existing data model.  
  
⸻  
  
## 6.1 Extension to   
```
labs_df

```

| Column | Type | Required | Source | Fallback |
| -------------------- | ------ | -------- | ----------------- | ------------------------------------------ |
| lab_id | string | yes | existing lab data | Default Lab |
| standard_hourly_cost | float | yes | Excel / config | 18.0 |
| overtime_multiplier | float | no | Excel / config | 1.25 |
| overtime_hourly_cost | float | no | calculated | standard_hourly_cost × overtime_multiplier |
| fixed_setup_cost | float | no | Excel / config | 0.0 |
| overhead_percentage | float | no | Excel / config | 0.10 |
| currency | string | no | Excel / config | EUR |
  
  
⸻  
  
## 6.2 Extension to   
```
orders_df

```

| Column | Type | Required | Source | Fallback |
| ------------------- | ------ | -------- | ------------------- | -------------------- |
| order_id | string | yes | existing order data | generated |
| order_value | float | yes | Excel / user input | warning / demo value |
| agreed_price | float | no | Excel / user input | same as order_value |
| target_margin | float | no | Excel / config | 0.30 |
| max_acceptable_cost | float | no | Excel / config | order_value × 0.70 |
| cost_sensitivity | string | no | user input | medium |
| customer_priority | string | no | user input | normal |
  
  
⸻  
  
## 6.3 Optional Extension to   
```
product_matrix_df

```
These fields are optional and should not block MVP implementation.  

| Column | Type | Required | Source | Fallback |
| ----------------------------- | ----- | -------- | -------------- | --------------- |
| phase_hourly_cost | float | no | Excel / config | lab hourly cost |
| specialized_operator_required | bool | no | Excel / config | false |
| rework_risk_percentage | float | no | future data | 0.0 |
  
  
⸻  
  
## 7. Default Values  
If real economic data is missing, the system should use configurable default values.  
```
standard_hourly_cost: 18.0
overtime_multiplier: 1.25
fixed_setup_cost: 0.0
overhead_percentage: 0.10
target_margin: 0.30
currency: "EUR"

```
The page must clearly indicate when demo/default values are being used.  
Example warning:  
“Some cost values are estimated using default assumptions.”  
  
⸻  
  
## 8. Core Formulas  
## 8.1 Required Hours  
```
required_hours = required_minutes / 60

```
  
⸻  
  
## 8.2 Standard Labour Cost  
```
standard_labour_cost = required_hours × standard_hourly_cost

```
  
⸻  
  
## 8.3 Excess Hours  
```
excess_hours = max(0, required_hours - available_hours)

```
  
⸻  
  
## 8.4 Overtime Hourly Cost  
```
overtime_hourly_cost = standard_hourly_cost × overtime_multiplier

```
  
⸻  
  
## 8.5 Overtime Cost  
```
overtime_cost = excess_hours × overtime_hourly_cost

```
  
⸻  
  
## 8.6 Setup Cost  
```
setup_cost = fixed_setup_cost

```
  
⸻  
  
## 8.7 Overhead Cost  
```
overhead_cost = (standard_labour_cost + overtime_cost + setup_cost) × overhead_percentage

```
  
⸻  
  
## 8.8 Total Estimated Production Cost  
```
total_estimated_cost = standard_labour_cost + overtime_cost + setup_cost + overhead_cost

```
  
⸻  
  
## 8.9 Estimated Margin  
```
estimated_margin = order_value - total_estimated_cost

```
  
⸻  
  
## 8.10 Margin Percentage  
```
margin_percentage = estimated_margin / order_value

```
  
⸻  
  
## 8.11 Average Cost per Garment  
```
average_cost_per_garment = total_estimated_cost / quantity

```
  
⸻  
  
## 8.12 Cost Impact of Reallocation  
```
cost_impact_of_reallocation = total_cost_alternative_lab - total_cost_current_lab

```
  
⸻  
  
## 9. Economic Recommendation Logic  
The page should generate an economic recommendation that complements the operational recommendation.  
  
⸻  
  
## 9.1 Recommendation Types  
**ACCEPT — Profitable and Feasible**  
Conditions:  
* margin_percentage >= target_margin;  
* no overtime required;  
* operational recommendation is Accept or low risk.  
  
⸻  
  
**ACCEPT WITH OVERTIME — Margin Still Acceptable**  
Conditions:  
* overtime is required;  
* margin_percentage remains above target_margin;  
* operational stress is not critical.  
  
⸻  
  
**REALLOCATE — Lower Risk, Higher Cost**  
Conditions:  
* alternative lab reduces operational stress;  
* alternative lab has higher estimated cost;  
* margin remains acceptable.  
Example message:  
“Reallocation reduces operational risk but increases estimated cost by €2,000.”  
  
⸻  
  
**RENEGOTIATE PRICE — Cost Exceeds Target Margin**  
Conditions:  
* total_estimated_cost is too high;  
* margin_percentage is below target_margin;  
* order could still be produced if price is adjusted.  
  
⸻  
  
**POSTPONE — Avoids Overtime Cost**  
Conditions:  
* current timeline requires overtime;  
* postponing would reduce overtime cost;  
* margin improves under postponed scenario.  
  
⸻  
  
**REJECT — Economically Unsustainable**  
Conditions:  
* estimated margin is negative;  
* total cost exceeds max acceptable cost;  
* no viable operational or economic alternative exists.  
  
⸻  
  
## 10. Page KPI  
The top row of the page should include four main KPI cards.  
  
⸻  
  
## KPI 1 — Total Estimated Production Cost  
Shows:  
```
€ total_estimated_cost

```
Purpose:  
* gives immediate visibility on total production cost.  
  
⸻  
  
## KPI 2 — Average Cost per Garment  
Shows:  
```
€ average_cost_per_garment

```
Purpose:  
* helps compare cost efficiency across orders.  
  
⸻  
  
## KPI 3 — Estimated Margin  
Shows:  
```
€ estimated_margin / margin_percentage

```
Purpose:  
* indicates whether the order remains economically attractive.  
  
⸻  
  
## KPI 4 — Cost Impact of Reallocation  
Shows:  
```
€ difference between current lab and alternative lab

```
Purpose:  
* helps evaluate whether reallocation is economically justified.  
  
⸻  
  
## 11. Page Layout  
## 11.1 Recommended Layout  
The Cost Feasibility Dashboard should follow this structure:  
```
Header
│
├── KPI Cards
│   ├── Total Estimated Production Cost
│   ├── Average Cost per Garment
│   ├── Estimated Margin
│   └── Cost Impact of Reallocation
│
├── Order Cost Breakdown
│   ├── standard labour cost
│   ├── overtime cost
│   ├── setup cost
│   ├── overhead
│   └── total estimated cost
│
├── Lab Comparison
│   ├── current lab
│   ├── alternative labs
│   ├── cost difference
│   ├── risk difference
│   └── margin difference
│
├── Cost vs Operational Risk Chart
│
├── Economic Alerts
│
└── Economic Recommendation Panel

```
  
⸻  
  
## 12. Visual Components  
## 12.1 KPI Cards  
Use compact cards with:  
* value;  
* short label;  
* status color;  
* optional delta.  
  
⸻  
  
## 12.2 Cost Breakdown Table  
Columns:  
* cost component;  
* amount;  
* percentage of total cost.  
Rows:  
* standard labour;  
* overtime;  
* setup;  
* overhead;  
* total.  
  
⸻  
  
## 12.3 Lab Comparison Table  
Columns:  
* lab;  
* estimated cost;  
* utilization;  
* operational risk;  
* margin;  
* recommendation.  
  
⸻  
  
## 12.4 Cost vs Risk Chart  
Recommended visualization:  
* x-axis: estimated production cost;  
* y-axis: operational risk or utilization;  
* points: labs or allocation scenarios.  
Purpose:  
* shows trade-off between lower cost and lower risk.  
  
⸻  
  
## 12.5 Economic Alerts  
Examples:  
* “Estimated margin below target.”  
* “Overtime increases production cost by €X.”  
* “Alternative lab reduces risk but increases cost.”  
* “Order economically unsustainable under current assumptions.”  
  
⸻  
  
## 12.6 Recommendation Panel  
The recommendation panel should clearly answer:  
“What is the economically best decision?”  
Example:  
```
Recommendation:
REALLOCATE — lower operational risk, higher cost

Reason:
- Lab B reduces utilization from 96% to 78%
- Estimated cost increases by €2,000
- Margin remains above target threshold

```
  
⸻  
  
## 13. Module Contract  
A new economic engine should be added.  
Suggested file:  
```
src/engines/economic_engine.py

```
  
⸻  
  
## 13.1 Responsibility  
The economic engine calculates:  
* required hours;  
* standard labour cost;  
* excess hours;  
* overtime cost;  
* setup cost;  
* overhead cost;  
* total estimated cost;  
* estimated margin;  
* margin percentage;  
* cost per garment;  
* cost impact of reallocation;  
* economic recommendation.  
  
⸻  
  
## 13.2 Inputs  
The module receives:  
* orders_df;  
* capacity_results_df;  
* labs_df;  
* recommendations_df;  
* scenario inputs;  
* config values.  
  
⸻  
  
## 13.3 Outputs  
The module returns:  
```
economic_results_df

```

| Column                   | Type   |
| ------------------------ | ------ |
| order_id                 | string |
| assigned_lab             | string |
| required_hours           | float  |
| available_hours          | float  |
| standard_labour_cost     | float  |
| overtime_hours           | float  |
| overtime_cost            | float  |
| setup_cost               | float  |
| overhead_cost            | float  |
| total_estimated_cost     | float  |
| order_value              | float  |
| estimated_margin         | float  |
| margin_percentage        | float  |
| average_cost_per_garment | float  |
| economic_recommendation  | string |
| economic_reason          | string |
  
  
⸻  
  
## 14. Streamlit Page Contract  
Suggested file:  
```
pages/Cost_Feasibility_Dashboard.py

```
or, if using a single app file:  
```
src/components/cost_feasibility_page.py

```
  
⸻  
  
## 14.1 Page Requirements  
The page must:  
* read existing capacity results;  
* compute economic results;  
* show KPI cards;  
* show cost breakdown;  
* compare labs if data is available;  
* show alerts;  
* show recommendation;  
* clearly mark estimated/default values.  
  
⸻  
  
## 15. Interaction with Existing Dashboard  
The Cost Feasibility Dashboard must not replace the operational recommendation engine.  
It must complement it.  
The final decision logic should combine:  
```
operational recommendation + economic recommendation

```
Example:  
```
Operational recommendation: REALLOCATE
Economic recommendation: REALLOCATE — higher cost but margin remains acceptable

```
or:  
```
Operational recommendation: ACCEPT
Economic recommendation: RENEGOTIATE PRICE

```
This is important because an order can be:  
* operationally feasible but economically weak;  
* economically attractive but operationally risky;  
* operationally risky but worth reallocating;  
* not feasible from both perspectives.  
  
⸻  
  
## 16. Edge Cases  
The page must handle:  
* missing order value;  
* missing hourly cost;  
* missing overtime multiplier;  
* quantity equal to zero;  
* required hours equal to zero;  
* negative margin;  
* missing alternative lab;  
* missing available hours;  
* order feasible operationally but not economically;  
* order profitable but operationally critical.  
When data is missing, show clear warnings instead of breaking the page.  
Example:  
```
Order value missing. Margin cannot be calculated.

```
  
⸻  
  
## 17. Acceptance Criteria  
The Cost Feasibility Dashboard is complete when:  
* the page appears in dashboard navigation;  
* required hours are correctly derived from required minutes;  
* standard labour cost is calculated correctly;  
* overtime hours are calculated when required_hours > available_hours;  
* overtime cost uses the overtime multiplier;  
* total estimated cost includes labour, overtime, setup and overhead;  
* estimated margin is calculated when order_value is available;  
* average cost per garment is shown;  
* economic recommendation is generated;  
* cost alerts are displayed clearly;  
* default values are marked as estimated;  
* the page works with demo/mock data;  
* the page does not break when economic data is incomplete.  
  
⸻  
  
## 18. Development Tasks for This Page  
## Task 1 — Extend Data Schema  
Add economic fields to mock/demo data:  
* standard_hourly_cost;  
* overtime_multiplier;  
* fixed_setup_cost;  
* overhead_percentage;  
* order_value;  
* target_margin.  
  
⸻  
  
## Task 2 — Create Economic Engine  
Create:  
```
src/engines/economic_engine.py

```
Implement all formulas and return economic_results_df.  
  
⸻  
  
## Task 3 — Add Cost Feasibility Page  
Create a new Streamlit page in navigation.  
  
⸻  
  
## Task 4 — Build KPI Cards  
Show:  
* total estimated production cost;  
* average cost per garment;  
* estimated margin;  
* cost impact of reallocation.  
  
⸻  
  
## Task 5 — Build Cost Breakdown Table  
Show:  
* standard labour cost;  
* overtime cost;  
* setup cost;  
* overhead cost;  
* total cost.  
  
⸻  
  
## Task 6 — Add Economic Alerts  
Display warnings for:  
* low margin;  
* negative margin;  
* overtime cost impact;  
* missing cost data.  
  
⸻  
  
## Task 7 — Add Lab Comparison  
If multiple labs are available, compare estimated cost and risk by lab.  
  
⸻  
  
## Task 8 — Add Economic Recommendation  
Generate recommendation based on margin, cost and overtime impact.  
  
⸻  
  
## Task 9 — Test with Demo Data  
Verify all formulas using simple test cases.  
  
⸻  
  
## 19. Strategic Value  
The Cost Feasibility Dashboard increases the managerial value of the system because it connects operational planning with economic decision-making.  
It allows the user to understand not only:  
“Can we produce this order?”  
but also:  
“What does this decision cost, and is it worth it?”  
This makes the dashboard more useful for managers, more credible as a business tool and more attractive as a future commercial product.  
The economic layer also creates a clear path for future developments such as:  
* profitability forecasting;  
* cost optimization;  
* price negotiation support;  
* AI-based margin prediction;  
* allocation optimization.  
  
