"""Alerts + recommendation panel components — TASK-026."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.utils.constants import (
    REC_ACCEPT,
    REC_AT_RISK,
    REC_POSTPONE,
    REC_REALLOCATE,
    REC_REJECT,
    REC_SPLIT,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    STATUS_COLORS,
)

_REC_COLORS = {
    REC_ACCEPT: STATUS_COLORS["safe"],
    REC_AT_RISK: STATUS_COLORS["at_risk"],
    REC_REALLOCATE: STATUS_COLORS["at_risk"],
    REC_SPLIT: STATUS_COLORS["at_risk"],
    REC_POSTPONE: STATUS_COLORS["at_risk"],
    REC_REJECT: STATUS_COLORS["critical"],
}


def _render_event(ev) -> None:
    """Render a single event as a colored Streamlit message."""
    message = f"**{ev['event_type']}** · {ev['order_id']} — {ev['message']}"
    if ev["severity"] == SEVERITY_HIGH:
        st.error(message)
    elif ev["severity"] == SEVERITY_MEDIUM:
        st.warning(message)
    else:
        st.info(message)


def render_alerts(stress_events_df: pd.DataFrame, max_items: int = 10) -> None:
    """Render stress events: first `max_items` inline, the rest in an expander.

    Inline gives an at-a-glance summary; the expander lets the user drill into
    every event without leaving the page.
    """
    if stress_events_df is None or stress_events_df.empty:
        st.success("No operational stress detected")
        return

    severity_order = {SEVERITY_HIGH: 0, SEVERITY_MEDIUM: 1, SEVERITY_LOW: 2}
    sorted_events = stress_events_df.assign(
        _ord=stress_events_df["severity"].map(severity_order).fillna(99)
    ).sort_values("_ord")

    head = sorted_events.head(max_items)
    tail = sorted_events.iloc[max_items:]

    for _, ev in head.iterrows():
        _render_event(ev)

    if not tail.empty:
        with st.expander(f"Show all {len(sorted_events)} events ({len(tail)} more)"):
            for _, ev in tail.iterrows():
                _render_event(ev)


def render_recommendation_panel(
    recommendations_df: pd.DataFrame,
    order_id: str | None = None,
) -> None:
    """Render the recommendation card(s) as the most visually prominent block."""
    if recommendations_df is None or recommendations_df.empty:
        st.info("No recommendations yet — load data to generate.")
        return

    df = recommendations_df
    if order_id is not None:
        df = df[df["order_id"] == order_id]
        if df.empty:
            st.warning(f"No recommendation for order '{order_id}'.")
            return

    for _, rec in df.iterrows():
        color = _REC_COLORS.get(rec["recommendation"], STATUS_COLORS["neutral"])
        reasons = rec.get("reasons") or []
        actions = rec.get("suggested_actions") or []
        reasons_html = "".join(f"<li>{r}</li>" for r in reasons)
        actions_html = "".join(f"<li>{a}</li>" for a in actions)
        html = f"""
        <div style="
            border: 1px solid {color};
            border-left: 6px solid {color};
            border-radius: 10px;
            padding: 20px 22px;
            background: #FFFFFF;
            margin-bottom: 14px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        ">
            <div style="display:flex;justify-content:space-between;align-items:baseline">
                <div style="font-size:20px;font-weight:600;color:#111827">{rec['order_id']}</div>
                <div style="font-size:13px;font-weight:600;color:{color};letter-spacing:0.06em">
                    {rec['recommendation']} · {str(rec.get('severity','')).upper()}
                </div>
            </div>
            <div style="margin-top:12px;font-size:13px;color:#374151">
                <div style="font-weight:600;margin-bottom:4px">Reasons</div>
                <ul style="margin:0 0 12px 18px;padding:0">{reasons_html}</ul>
                <div style="font-weight:600;margin-bottom:4px">Suggested actions</div>
                <ul style="margin:0 0 0 18px;padding:0">{actions_html}</ul>
            </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)


__all__ = ["render_alerts", "render_recommendation_panel"]
