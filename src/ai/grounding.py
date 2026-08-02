"""Build reusable grounding contexts from injected approved financial data."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING

import pandas as pd

from src.ai.schemas import (
    AnnualFacts,
    FigureUnit,
    GroundedFigure,
    GroundingContext,
    MetricName,
    PeriodFacts,
    ReportingPeriod,
    SourceReference,
)
from src.ai.business_drivers import load_business_driver_context

if TYPE_CHECKING:
    from src.data_loader import FinancialDatasets


CORE_METRICS = (
    "revenue",
    "gross_profit",
    "operating_income",
    "net_income",
)
PERIOD_METRICS = (
    *CORE_METRICS,
    "revenue_qoq_growth_pct",
    "revenue_yoy_growth_pct",
    "gross_margin_pct",
    "operating_margin_pct",
    "net_margin_pct",
)
COMPARISON_METRICS = (
    *CORE_METRICS,
    "gross_margin_pct",
    "operating_margin_pct",
    "net_margin_pct",
)
ANNUAL_METRICS = (
    *CORE_METRICS,
    "revenue_yoy_growth_pct",
    "gross_margin_pct",
    "operating_margin_pct",
    "net_margin_pct",
)
PERCENT_METRICS = {
    "revenue_qoq_growth_pct",
    "revenue_yoy_growth_pct",
    "gross_margin_pct",
    "operating_margin_pct",
    "net_margin_pct",
}


class GroundingError(RuntimeError):
    """Raised when approved data cannot ground the requested period."""


def _decimal_value(value: object, metric: str) -> Decimal:
    if isinstance(value, bool) or pd.isna(value):
        raise GroundingError(f"Missing or invalid value for {metric}.")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise GroundingError(
            f"Could not normalize {metric} as a decimal."
        ) from error
    if not result.is_finite():
        raise GroundingError(f"Non-finite value found for {metric}.")
    if metric not in PERCENT_METRICS:
        if result != result.to_integral_value():
            raise GroundingError(
                f"USD metric {metric} is not an integer dollar value."
            )
        result = result.quantize(Decimal("1"))
    return result


def _source_id(dataset: str, period_id: str) -> str:
    return f"{dataset}:{period_id}"


def _eligible_row(
    frame: pd.DataFrame,
    period: ReportingPeriod,
) -> pd.Series | None:
    matches = frame[
        (frame["fiscal_year"] == period.fiscal_year)
        & (frame["fiscal_period"] == period.fiscal_period)
    ]
    if len(matches) != 1:
        return None
    row = matches.iloc[0]
    if row[list(CORE_METRICS)].isna().any():
        return None
    return row


def _period_facts(
    row: pd.Series,
    period: ReportingPeriod,
    metrics: tuple[str, ...],
) -> PeriodFacts:
    source_id = _source_id("quarterly_analytics", period.identifier)
    figures = tuple(
        GroundedFigure(
            metric=MetricName(metric),
            value=_decimal_value(row[metric], metric),
            unit=(
                FigureUnit.PERCENT
                if metric in PERCENT_METRICS
                else FigureUnit.USD
            ),
            source_id=source_id,
        )
        for metric in metrics
        if metric in row.index and not pd.isna(row[metric])
    )
    return PeriodFacts(
        period=period,
        source_id=source_id,
        figures=figures,
    )


def _comparison_facts(
    frame: pd.DataFrame,
    period: ReportingPeriod,
) -> PeriodFacts | None:
    row = _eligible_row(frame, period)
    if row is None:
        return None
    return _period_facts(row, period, COMPARISON_METRICS)


def _annual_facts(
    annual: pd.DataFrame,
    requested_period: ReportingPeriod,
) -> AnnualFacts | None:
    """Select only annual results completed as of the requested quarter."""
    maximum_year = (
        requested_period.fiscal_year
        if requested_period.fiscal_period == "Q4"
        else requested_period.fiscal_year - 1
    )
    candidates = annual[annual["fiscal_year"] <= maximum_year].copy()
    candidates = candidates.dropna(subset=list(CORE_METRICS))
    if candidates.empty:
        return None
    row = candidates.sort_values("fiscal_year").iloc[-1]
    fiscal_year = int(row["fiscal_year"])
    period_id = f"FY{fiscal_year}"
    source_id = _source_id("annual_financials", period_id)
    figures = tuple(
        GroundedFigure(
            metric=MetricName(metric),
            value=_decimal_value(row[metric], metric),
            unit=(
                FigureUnit.PERCENT
                if metric in PERCENT_METRICS
                else FigureUnit.USD
            ),
            source_id=source_id,
        )
        for metric in ANNUAL_METRICS
        if metric in row.index and not pd.isna(row[metric])
    )
    return AnnualFacts(
        fiscal_year=fiscal_year,
        source_id=source_id,
        figures=figures,
    )


def build_grounding_context(
    datasets: FinancialDatasets,
    requested_period: ReportingPeriod | str,
) -> GroundingContext:
    """Build an as-of grounding context for any eligible fiscal quarter."""
    period = (
        ReportingPeriod.parse(requested_period)
        if isinstance(requested_period, str)
        else requested_period
    )
    if not isinstance(period, ReportingPeriod):
        raise TypeError(
            "requested_period must be a ReportingPeriod or canonical string."
        )

    analytics = datasets.quarterly_analytics
    current_row = _eligible_row(analytics, period)
    if current_row is None:
        raise GroundingError(
            f"{period.identifier} is unavailable or missing one or more "
            "core quarterly metrics."
        )

    current = _period_facts(current_row, period, PERIOD_METRICS)
    previous = _comparison_facts(analytics, period.previous_quarter())
    prior_year = _comparison_facts(
        analytics,
        period.prior_year_quarter(),
    )
    annual = _annual_facts(datasets.annual, period)

    facts = (current, previous, prior_year, annual)
    sources = []
    for item in facts:
        if item is None:
            continue
        if isinstance(item, AnnualFacts):
            dataset = "annual_financials"
            period_id = f"FY{item.fiscal_year}"
        else:
            dataset = "quarterly_analytics"
            period_id = item.period.identifier
        sources.append(
            SourceReference(
                source_id=item.source_id,
                dataset=dataset,
                period_id=period_id,
            )
        )

    return GroundingContext(
        requested_period=period,
        current_period=current,
        previous_quarter=previous,
        prior_year_quarter=prior_year,
        annual_context=annual,
        business_drivers=load_business_driver_context(period),
        sources=tuple(sources),
    )
