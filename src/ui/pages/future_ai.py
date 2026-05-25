"""Page 7 — Future AI Layer (TASK-035).

Strategic showcase; intentionally non-functional.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.utils.constants import STATUS_COLORS

_FEATURES = [
    (
        "Predictive Delay Risk",
        "Classification model trained on historical orders to estimate the "
        "probability of delay before production starts. Requires historical delivery "
        "data and delay-cause annotations not currently available.",
    ),
    (
        "Anomaly Detection",
        "Detects unusual processing times, repeated bottlenecks, and sudden capacity "
        "drops — surfaces issues before they cascade into operational stress.",
    ),
    (
        "Forecasting",
        "Predicts future workload, lab saturation, and seasonal production peaks "
        "to inform hiring, sourcing, and deadline negotiations.",
    ),
    (
        "Optimization Engine",
        "Suggests optimal lab allocation, order-splitting strategies, and capacity "
        "rebalancing — replaces rule-based REALLOCATE/SPLIT with a true optimizer.",
    ),
    (
        "Digital Twin Simulation",
        "Lets planners stress-test disruptions and what-if production scenarios "
        "against a model of the actual factory floor.",
    ),
]


def _feature_card(title: str, description: str) -> str:
    color = STATUS_COLORS["neutral"]
    return f"""
    <div style="
        border: 1px solid {color};
        border-left: 4px solid {color};
        border-radius: 10px;
        padding: 18px 22px;
        background: #FFFFFF;
        margin-bottom: 12px;
    ">
        <div style="display:flex;justify-content:space-between;align-items:baseline">
            <div style="font-size:18px;font-weight:600;color:#111827">{title}</div>
            <div style="
                font-size:11px;
                font-weight:600;
                letter-spacing:0.06em;
                color:#6B7280;
                border:1px solid #D1D5DB;
                border-radius:999px;
                padding:2px 10px;
            ">PLANNED</div>
        </div>
        <div style="margin-top:8px;font-size:14px;color:#374151;line-height:1.5">{description}</div>
    </div>
    """


def render() -> None:
    st.title("Future AI Layer")
    st.write(
        "These features are intentionally **not implemented** in the MVP. "
        "They represent the strategic expansion path once the operational dashboard "
        "is in active use and historical data starts accumulating."
    )

    diagram = Path("assets/mockups/future_ai.png")
    if diagram.exists():
        st.image(str(diagram), use_column_width=True)
    else:
        st.caption(f"_(Roadmap diagram placeholder — drop a PNG at `{diagram}` to display it here.)_")

    for title, desc in _FEATURES:
        st.markdown(_feature_card(title, desc), unsafe_allow_html=True)

    st.divider()
    st.markdown(
        "> **Disclaimer.** The current MVP is rule-based and deterministic. "
        "AI extensions require additional historical data — actual deliveries, "
        "delay causes, lab performance over time — not currently available in the "
        "Excel workflow being digitalized."
    )
