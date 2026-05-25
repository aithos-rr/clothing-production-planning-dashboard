"""Marvi — Operational Planning dashboard entry point.

Placeholder skeleton: each page renders a title and a "Coming soon" notice.
TASK-028 will refactor this into a real router with session-state-backed data.

Verified error scenarios (PRD §16) — checklist (✓ filled by TASK-039):
  [ ] Unsupported file type on upload
  [ ] Unreadable Excel file
  [ ] Empty workbook
  [ ] Missing sheets
  [ ] Missing required data columns (product_type, quantity, deadline)
  [ ] Invalid dates / quantity <= 0
  [ ] Product not found in product matrix
  [ ] Available capacity = 0 (division by zero)
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Marvi — Operational Planning",
    layout="wide",
)

PAGES: list[str] = [
    "Overview",
    "Upload Data",
    "Capacity Dashboard",
    "Phase Saturation",
    "Timeline",
    "Scenario Testing",
    "Future AI Layer",
]


def main() -> None:
    page = st.sidebar.radio("Navigation", PAGES, index=0)
    st.title(page)
    st.info("Coming soon")


if __name__ == "__main__":
    main()
