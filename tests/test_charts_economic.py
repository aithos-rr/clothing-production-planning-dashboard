import pandas as pd
import plotly.graph_objects as go

from src.components.charts import cost_vs_risk_scatter


def test_cost_vs_risk_returns_figure_with_points():
    df = pd.DataFrame({
        "label": ["L1", "L2"],
        "estimated_cost": [2000.0, 2400.0],
        "utilization": [0.96, 0.78],
    })
    fig = cost_vs_risk_scatter(df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_cost_vs_risk_empty_is_safe():
    fig = cost_vs_risk_scatter(pd.DataFrame(columns=["label", "estimated_cost", "utilization"]))
    assert isinstance(fig, go.Figure)
