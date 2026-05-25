"""Streamlit KPI card component — TASK-024.

Purely presentational: card label + value, color border driven by status.
"""
from __future__ import annotations

from typing import Sequence

import streamlit as st

from src.utils.formatting import status_color


def kpi_card(
    label: str,
    value: str,
    status: str = "neutral",
    delta: str | None = None,
) -> None:
    """Render a bordered KPI card."""
    color = status_color(status)
    delta_html = f"<div style='font-size:12px;color:#6B7280;margin-top:4px'>{delta}</div>" if delta else ""
    html = f"""
    <div style="
        border: 1px solid {color};
        border-left: 4px solid {color};
        border-radius: 8px;
        padding: 16px 20px;
        background: #FFFFFF;
        margin-bottom: 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    ">
        <div style="font-size:12px;color:#6B7280;letter-spacing:0.04em;text-transform:uppercase">{label}</div>
        <div style="font-size:28px;font-weight:600;color:#111827;margin-top:6px">{value}</div>
        {delta_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def kpi_row(cards: Sequence[dict]) -> None:
    """Render a horizontal row of KPI cards."""
    if not cards:
        return
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        with col:
            kpi_card(
                label=card.get("label", ""),
                value=card.get("value", "—"),
                status=card.get("status", "neutral"),
                delta=card.get("delta"),
            )


__all__ = ["kpi_card", "kpi_row"]
