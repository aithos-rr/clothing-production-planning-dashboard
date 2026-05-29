"""Plotly chart helpers — TASK-025.

All color decisions go through STATUS_COLORS to keep the palette consistent.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from src.utils.constants import (
    CRITICAL_UTILIZATION_THRESHOLD,
    STATUS_COLORS,
)
from src.utils.formatting import utilization_status

_BG = "#FFFFFF"
_GRID = "#E5E7EB"
_MIN_HEIGHT = 400


def _empty_figure(message: str = "No data to display") -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        height=_MIN_HEIGHT,
        margin=dict(l=30, r=20, t=40, b=40),
        annotations=[dict(text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)],
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def _base_layout(fig: go.Figure, title: str | None = None) -> go.Figure:
    fig.update_layout(
        title=title or "",
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        height=_MIN_HEIGHT,
        margin=dict(l=60, r=20, t=50, b=40),
        font=dict(family="Inter, system-ui, sans-serif", color="#111827"),
        showlegend=False,
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)
    return fig


def phase_utilization_bar(lab_phase_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of AGGREGATE utilization per lab-phase, colored by status.

    Aggregate (sum required / available per lab-phase) is the real capacity picture —
    it reflects all orders sharing a phase, not a single worst-case order.
    """
    if lab_phase_df.empty:
        return _empty_figure("No capacity data yet")

    finite_util = lab_phase_df["utilization_rate"].replace(
        [float("inf"), float("-inf")], float("nan")
    )
    work = (
        lab_phase_df.assign(_u=finite_util)
        .dropna(subset=["_u"])
        .copy()
    )
    if work.empty:
        return _empty_figure("All phases have undefined capacity")
    work["_label"] = work["phase_name"].astype(str) + " · " + work["assigned_lab"].astype(str)
    work = work.sort_values("_u", ascending=True)

    colors = [STATUS_COLORS[utilization_status(v)] for v in work["_u"].values]
    fig = go.Figure(
        go.Bar(
            x=work["_u"].values,
            y=work["_label"].values,
            orientation="h",
            marker=dict(color=colors),
            hovertemplate="%{y}: %{x:.0%}<extra></extra>",
        )
    )
    fig.add_vline(
        x=CRITICAL_UTILIZATION_THRESHOLD,
        line=dict(color="#9CA3AF", width=1, dash="dash"),
    )
    fig = _base_layout(fig, title="Aggregate utilization by lab-phase")
    fig.update_xaxes(tickformat=".0%", range=[0, max(1.2, float(work["_u"].max()) * 1.1)])
    return fig


def lab_phase_capacity_gap_bar(lab_phase_df: pd.DataFrame) -> go.Figure:
    """Bar chart of AGGREGATE capacity gap per lab-phase. Negative (deficit) in red.

    Gap = available - sum required, capacity counted once per lab-phase. Replaces the
    old per-order gap chart that inflated capacity by crediting it to each order.
    """
    if lab_phase_df.empty:
        return _empty_figure("No capacity data yet")

    work = lab_phase_df.copy()
    work["_label"] = work["phase_name"].astype(str) + " · " + work["assigned_lab"].astype(str)
    work = work.sort_values("capacity_gap_minutes")
    colors = [
        STATUS_COLORS["critical"] if v < 0 else STATUS_COLORS["safe"]
        for v in work["capacity_gap_minutes"].values
    ]
    fig = go.Figure(
        go.Bar(
            x=work["_label"].values,
            y=work["capacity_gap_minutes"].values,
            marker=dict(color=colors),
            hovertemplate="%{x}: %{y:.0f} min<extra></extra>",
        )
    )
    fig.add_hline(y=0, line=dict(color="#9CA3AF", width=1))
    fig = _base_layout(fig, title="Capacity gap by lab-phase (minutes)")
    return fig


__all__ = ["phase_utilization_bar", "lab_phase_capacity_gap_bar"]
