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


def phase_utilization_bar(capacity_results_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of mean utilization per phase, colored by status."""
    if capacity_results_df.empty:
        return _empty_figure("No capacity data yet")

    per_phase = (
        capacity_results_df.groupby("phase_name")["utilization_rate"]
        .mean()
        .replace([float("inf"), float("-inf")], float("nan"))
        .dropna()
        .sort_values(ascending=True)
    )
    if per_phase.empty:
        return _empty_figure("All phases have undefined capacity")

    colors = [STATUS_COLORS[utilization_status(v)] for v in per_phase.values]
    fig = go.Figure(
        go.Bar(
            x=per_phase.values,
            y=per_phase.index,
            orientation="h",
            marker=dict(color=colors),
            hovertemplate="%{y}: %{x:.0%}<extra></extra>",
        )
    )
    fig.add_vline(
        x=CRITICAL_UTILIZATION_THRESHOLD,
        line=dict(color="#9CA3AF", width=1, dash="dash"),
    )
    fig = _base_layout(fig, title="Phase utilization (mean across orders)")
    fig.update_xaxes(tickformat=".0%", range=[0, max(1.2, per_phase.max() * 1.1)])
    return fig


def order_capacity_gap_bar(capacity_results_df: pd.DataFrame) -> go.Figure:
    """Bar chart of capacity gap per order (sum across phases). Negative in red."""
    if capacity_results_df.empty:
        return _empty_figure("No capacity data yet")

    per_order = capacity_results_df.groupby("order_id")["capacity_gap_minutes"].sum().sort_values()
    colors = [
        STATUS_COLORS["critical"] if v < 0 else STATUS_COLORS["safe"]
        for v in per_order.values
    ]
    fig = go.Figure(
        go.Bar(
            x=per_order.index,
            y=per_order.values,
            marker=dict(color=colors),
            hovertemplate="%{x}: %{y:.0f} min<extra></extra>",
        )
    )
    fig.add_hline(y=0, line=dict(color="#9CA3AF", width=1))
    fig = _base_layout(fig, title="Capacity gap by order (minutes)")
    return fig


__all__ = ["phase_utilization_bar", "order_capacity_gap_bar"]
