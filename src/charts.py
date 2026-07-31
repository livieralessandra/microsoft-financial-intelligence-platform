"""Plotly chart builders with consistent executive-dashboard styling."""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


BLUE = "#0078D4"
BLUE_LIGHT = "#5CAAE6"
TEAL = "#107C10"
PURPLE = "#744DA9"
INK = "#1B1A19"
MUTED = "#605E5C"
GRID = "#EDEBE9"


def add_period_label(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with a chronologically sortable fiscal label."""
    result = frame.copy()
    result["period_label"] = (
        "FY" + result["fiscal_year"].astype(int).astype(str)
        + " " + result["fiscal_period"].astype(str)
    )
    return result


def _style_figure(
    figure: go.Figure,
    height: int = 400,
) -> go.Figure:
    figure.update_layout(
        height=height,
        margin=dict(l=24, r=24, t=42, b=28),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family='"Segoe UI", Arial, sans-serif',
            color=INK,
            size=13,
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.04,
            xanchor="left", x=0,
            font=dict(size=12, color=MUTED),
            bgcolor="rgba(0,0,0,0)",
        ),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor="#D2D0CE",
            font=dict(color=INK, size=13),
        ),
    )
    figure.update_xaxes(
        showgrid=False,
        linecolor="#D2D0CE",
        tickfont=dict(color=MUTED, size=12),
        title_font=dict(color=MUTED, size=12),
        automargin=True,
    )
    figure.update_yaxes(
        gridcolor=GRID,
        gridwidth=1,
        zerolinecolor="#D2D0CE",
        tickfont=dict(color=MUTED, size=12),
        title_font=dict(color=MUTED, size=12),
        automargin=True,
    )
    return figure


def revenue_trend(frame: pd.DataFrame) -> go.Figure:
    """Build the executive quarterly revenue trend."""
    data = add_period_label(frame.dropna(subset=["revenue"]))
    annual_ticks = data[data["fiscal_period"] == "Q1"]
    figure = go.Figure(
        go.Scatter(
            x=data["period_label"],
            y=data["revenue"] / 1_000_000_000,
            mode="lines+markers",
            name="Revenue",
            line=dict(color=BLUE, width=3.25),
            marker=dict(
                size=7,
                color="#FFFFFF",
                line=dict(color=BLUE, width=2.5),
            ),
            hovertemplate="%{x}<br>$%{y:,.1f}B<extra></extra>",
        )
    )
    figure.update_yaxes(
        title="USD billions", ticksuffix="B", tickprefix="$"
    )
    figure.update_xaxes(
        tickmode="array",
        tickvals=annual_ticks["period_label"],
        ticktext=(
            "FY" + annual_ticks["fiscal_year"].astype(int).astype(str)
        ),
        tickangle=0,
    )
    return _style_figure(figure)


def quarterly_metric_trend(
    frame: pd.DataFrame,
    column: str,
    label: str,
) -> go.Figure:
    """Build a selected quarterly financial-metric trend."""
    data = add_period_label(frame.dropna(subset=[column]))
    figure = go.Figure(
        go.Scatter(
            x=data["period_label"],
            y=data[column] / 1_000_000_000,
            mode="lines+markers",
            name=label,
            line=dict(color=BLUE, width=3.25),
            marker=dict(
                size=7,
                color="#FFFFFF",
                line=dict(color=BLUE, width=2.5),
            ),
            hovertemplate="%{x}<br>$%{y:,.1f}B<extra></extra>",
        )
    )
    figure.update_yaxes(
        title="USD billions", ticksuffix="B", tickprefix="$"
    )
    return _style_figure(figure)


def margin_trend(frame: pd.DataFrame) -> go.Figure:
    """Build quarterly gross, operating, and net margin trends."""
    data = add_period_label(frame)
    figure = go.Figure()
    for column, label, color in (
        ("gross_margin_pct", "Gross margin", BLUE),
        ("operating_margin_pct", "Operating margin", TEAL),
        ("net_margin_pct", "Net margin", PURPLE),
    ):
        figure.add_trace(
            go.Scatter(
                x=data["period_label"],
                y=data[column],
                mode="lines",
                name=label,
                line=dict(color=color, width=2.75),
                hovertemplate=(
                    f"%{{x}}<br>{label}: %{{y:,.1f}}%<extra></extra>"
                ),
            )
        )
    figure.update_yaxes(title="Margin", ticksuffix="%")
    return _style_figure(figure)


def annual_revenue_and_growth(frame: pd.DataFrame) -> go.Figure:
    """Build annual revenue columns with the SQL-provided growth line."""
    labels = "FY" + frame["fiscal_year"].astype(int).astype(str)
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    figure.add_trace(
        go.Bar(
            x=labels,
            y=frame["revenue"] / 1_000_000_000,
            name="Annual revenue",
            marker=dict(
                color=BLUE,
                line=dict(color=BLUE_LIGHT, width=0.5),
            ),
            hovertemplate="%{x}<br>$%{y:,.1f}B<extra></extra>",
        ),
        secondary_y=False,
    )
    figure.add_trace(
        go.Scatter(
            x=labels,
            y=frame["revenue_yoy_growth_pct"],
            name="YoY growth",
            mode="lines+markers",
            line=dict(color=TEAL, width=3),
            marker=dict(
                size=7,
                color="#FFFFFF",
                line=dict(color=TEAL, width=2.5),
            ),
            hovertemplate="%{x}<br>%{y:,.1f}%<extra></extra>",
        ),
        secondary_y=True,
    )
    figure.update_yaxes(
        title_text="Revenue (USD billions)", tickprefix="$",
        ticksuffix="B", secondary_y=False,
    )
    figure.update_yaxes(
        title_text="YoY growth", ticksuffix="%",
        secondary_y=True, showgrid=False,
    )
    return _style_figure(figure)


def annual_margin_trend(frame: pd.DataFrame) -> go.Figure:
    """Build annual profitability margin trends."""
    labels = "FY" + frame["fiscal_year"].astype(int).astype(str)
    figure = go.Figure()
    for column, label, color in (
        ("gross_margin_pct", "Gross margin", BLUE),
        ("operating_margin_pct", "Operating margin", TEAL),
        ("net_margin_pct", "Net margin", PURPLE),
    ):
        figure.add_trace(
            go.Scatter(
                x=labels,
                y=frame[column],
                name=label,
                mode="lines+markers",
                line=dict(color=color, width=2.75),
                marker=dict(
                    size=6,
                    color="#FFFFFF",
                    line=dict(color=color, width=2),
                ),
                hovertemplate=(
                    f"%{{x}}<br>{label}: %{{y:,.1f}}%<extra></extra>"
                ),
            )
        )
    figure.update_yaxes(title="Margin", ticksuffix="%")
    return _style_figure(figure)
