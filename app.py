"""Marvi — Operational Planning dashboard entry point.

Router. Each page module under `src/ui/pages/` exposes a `render()` function.

Verified error scenarios (PRD §16) — checklist (✓ filled by TASK-039):
  [✓] Unsupported file type on upload
  [✓] Unreadable Excel file
  [✓] Empty workbook
  [✓] Missing sheets
  [✓] Missing required data columns (product_type, quantity, deadline)
  [✓] Invalid dates / quantity <= 0
  [✓] Product not found in product matrix
  [✓] Available capacity = 0 (utilization rendered as inf, no division error)
"""
from __future__ import annotations

import traceback

import streamlit as st

from src.engines.scenario_engine import ScenarioInputs
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

st.set_page_config(
    page_title="Clothing Production Planning Dashboard",
    layout="wide",
)


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

# Pages that need uploaded data to function
_DATA_GATED_PAGES = {
    "Capacity Dashboard",
    "Phase Saturation",
    "Timeline",
    "Scenario Testing",
    "Cost Feasibility Dashboard",
}


def _ensure_session_defaults() -> None:
    st.session_state.setdefault("data", None)
    st.session_state.setdefault("scenario", ScenarioInputs())
    st.session_state.setdefault("planning_days", 5)


def main() -> None:
    _ensure_session_defaults()
    page = st.sidebar.radio("Navigation", list(PAGES.keys()), index=0)

    # Gate
    if page in _DATA_GATED_PAGES and st.session_state.get("data") is None:
        st.title(page)
        st.warning("Please upload data first or use Demo mode on the Upload page.")
        return

    try:
        PAGES[page]()
    except Exception as exc:  # noqa: BLE001 — final UI safety net
        st.title(page)
        st.error(f"Unexpected error: {type(exc).__name__}. Please check the data and try again.")
        # Log full traceback to stderr so it's visible in the terminal
        traceback.print_exc()


if __name__ == "__main__":
    main()
