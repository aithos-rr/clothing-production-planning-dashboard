"""Timeline UI component — TASK-027."""
from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.utils.constants import (
    STATUS_COLORS,
    TIMELINE_AT_RISK,
    TIMELINE_BLOCKED,
    TIMELINE_LATE,
    TIMELINE_ON_TRACK,
)

_STATUS_COLOR_MAP = {
    TIMELINE_ON_TRACK: STATUS_COLORS["safe"],
    TIMELINE_AT_RISK: STATUS_COLORS["at_risk"],
    TIMELINE_LATE: STATUS_COLORS["critical"],
    TIMELINE_BLOCKED: STATUS_COLORS["neutral"],
}


def render_timeline_chart(timeline_df: pd.DataFrame) -> go.Figure:
    """Render a Plotly Gantt-style chart from `timeline_df`."""
    if timeline_df is None or timeline_df.empty:
        fig = go.Figure()
        fig.update_layout(
            height=400,
            margin=dict(l=30, r=20, t=40, b=40),
            annotations=[
                dict(text="No orders to display", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
            ],
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
        )
        return fig

    df = timeline_df.copy()
    # px.timeline needs datetime-typed columns
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"])

    fig = px.timeline(
        df,
        x_start="start_date",
        x_end="end_date",
        y="order_id",
        color="status",
        color_discrete_map=_STATUS_COLOR_MAP,
        hover_data=["product_type", "deadline", "duration_days", "status", "assigned_lab"],
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        height=max(400, 40 * len(df) + 100),
        margin=dict(l=80, r=20, t=40, b=40),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(family="Inter, system-ui, sans-serif", color="#111827"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )

    # Vertical dashed line at today
    today = datetime.combine(date.today(), datetime.min.time())
    fig.add_vline(x=today, line=dict(color="#6B7280", width=1, dash="dash"))

    return fig


__all__ = ["render_timeline_chart"]
