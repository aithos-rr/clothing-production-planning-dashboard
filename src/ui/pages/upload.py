"""Page 2 — Upload Data (TASK-030)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.parsers.excel_parser import ExcelParseError, parse_excel
from src.parsers.normalizer import normalize_all
from src.utils.constants import SEVERITY_HIGH, SEVERITY_LOW, SEVERITY_MEDIUM

SAMPLE_PATH = Path("data/sample/sample_planning.xlsx")


def _render_warnings(warnings: list) -> None:
    if not warnings:
        st.success("No validation warnings.")
        return
    by_sev = {SEVERITY_HIGH: [], SEVERITY_MEDIUM: [], SEVERITY_LOW: []}
    for w in warnings:
        by_sev.setdefault(w.severity, []).append(w)
    for w in by_sev[SEVERITY_HIGH]:
        st.error(f"[{w.field}] {w.message}")
    for w in by_sev[SEVERITY_MEDIUM]:
        st.warning(f"[{w.field}] {w.message}")
    for w in by_sev[SEVERITY_LOW]:
        st.info(f"[{w.field}] {w.message}")


def _ingest(raw_sheets: dict[str, pd.DataFrame], used_mock_marker: str | None = None) -> None:
    result = normalize_all(raw_sheets, use_mock_fallback=True)
    st.session_state["data"] = result
    if used_mock_marker:
        st.success(f"Loaded demo dataset: {used_mock_marker}")
    else:
        st.success(f"Detected sheets: {', '.join(raw_sheets.keys())}")

    _render_warnings(result["warnings"])

    for sheet_name in ("orders", "product_matrix", "labs", "phase_capacity"):
        with st.expander(f"Preview — {sheet_name} (first 10 rows)"):
            df = result.get(sheet_name)
            if df is None or df.empty:
                st.write("_(empty)_")
            else:
                st.dataframe(df.head(10), use_container_width=True)


def render() -> None:
    st.title("Upload Data")
    st.write("Upload an `.xlsx` workbook with the 4 input sheets, or enable demo mode.")

    use_demo = st.toggle("Use demo data instead of uploading", value=False)
    uploaded = st.file_uploader("Planning workbook", type=["xlsx"], disabled=use_demo)

    if use_demo:
        if not SAMPLE_PATH.exists():
            st.error(
                f"Sample dataset not found at `{SAMPLE_PATH}`. "
                "Run `python scripts/build_sample_data.py` once to generate it."
            )
            return
        try:
            raw = parse_excel(SAMPLE_PATH)
        except ExcelParseError as exc:
            st.error(f"Could not read sample workbook: {exc}")
            return
        _ingest(raw, used_mock_marker=str(SAMPLE_PATH))
        return

    if uploaded is None:
        st.info("Choose a file above, or toggle demo mode.")
        return

    try:
        raw = parse_excel(uploaded)
    except ExcelParseError as exc:
        st.error(str(exc))
        return

    _ingest(raw)
