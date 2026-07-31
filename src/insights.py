"""Deterministic executive insights sourced only from approved datasets."""

from dataclasses import dataclass

import pandas as pd

from src.formatters import (
    direction_word,
    fiscal_label,
    format_billions,
    format_percent,
)


@dataclass(frozen=True)
class Insight:
    """A concise, source-grounded executive observation."""

    title: str
    body: str


def _growth_statement(
    value: float,
    comparison: str,
) -> str:
    if pd.isna(value):
        return f"Revenue growth {comparison} was unavailable"
    return (
        f"revenue {direction_word(value)} "
        f"{format_percent(abs(value))} {comparison}"
    )


def _margin_direction(
    latest: pd.Series,
    previous: pd.Series | None,
) -> str | None:
    if previous is None:
        return None
    comparisons = []
    labels = {
        "gross_margin_pct": "gross",
        "operating_margin_pct": "operating",
        "net_margin_pct": "net",
    }
    for column, label in labels.items():
        current = latest.get(column)
        prior = previous.get(column)
        if pd.isna(current) or pd.isna(prior):
            continue
        change = float(current) - float(prior)
        if abs(change) < 0.05:
            direction = "held steady"
        elif change > 0:
            direction = "improved"
        else:
            direction = "declined"
        comparisons.append(f"{label} margin {direction}")
    if not comparisons:
        return None
    if len(comparisons) == 1:
        return comparisons[0].capitalize() + "."
    return (
        ", ".join(comparisons[:-1]).capitalize()
        + f", and {comparisons[-1]} versus the prior quarter."
    )


def build_executive_insights(
    latest_frame: pd.DataFrame,
    quarterly_analytics: pd.DataFrame,
) -> list[Insight]:
    """Create factual insights without causal or strategic speculation."""
    latest = latest_frame.iloc[0]
    period = fiscal_label(
        latest["fiscal_year"], str(latest["fiscal_period"])
    )
    insights = [
        Insight(
            "Current scale",
            f"Microsoft reported {format_billions(latest['revenue'])} "
            f"in revenue for {period}.",
        ),
        Insight(
            "Growth momentum",
            (
                _growth_statement(
                    latest["revenue_yoy_growth_pct"],
                    "year over year",
                ).capitalize()
                + " and "
                + _growth_statement(
                    latest["revenue_qoq_growth_pct"],
                    "from the prior quarter",
                )
                + "."
            ),
        ),
        Insight(
            "Profitability",
            f"Gross margin was {format_percent(latest['gross_margin_pct'])}, "
            f"operating margin was "
            f"{format_percent(latest['operating_margin_pct'])}, and net "
            f"margin was {format_percent(latest['net_margin_pct'])}.",
        ),
    ]

    ordered = quarterly_analytics.sort_values(
        ["fiscal_year", "quarter_number"]
    ).reset_index(drop=True)
    matches = ordered[
        (ordered["fiscal_year"] == latest["fiscal_year"])
        & (ordered["fiscal_period"] == latest["fiscal_period"])
    ]
    previous = None
    if not matches.empty and matches.index[-1] > 0:
        previous = ordered.iloc[matches.index[-1] - 1]
    margin_text = _margin_direction(latest, previous)
    if margin_text:
        insights.append(Insight("What deserves attention", margin_text))
    return insights
