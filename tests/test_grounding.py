"""Tests for reusable, as-of grounding-context construction."""

from decimal import Decimal

import pandas as pd
import pytest

from src.ai.grounding import GroundingError, build_grounding_context
from src.ai.schemas import MetricName
from src.data_loader import FinancialDatasets, load_financial_datasets


def _figures_by_metric(facts: object) -> dict:
    return {figure.metric: figure.value for figure in facts.figures}


@pytest.mark.parametrize("quarter", ["Q1", "Q2", "Q3"])
def test_interim_quarters_do_not_leak_same_year_annual_results(
    financial_datasets: FinancialDatasets,
    quarter: str,
) -> None:
    context = build_grounding_context(
        financial_datasets,
        f"FY2026-{quarter}",
    )
    assert context.annual_context is not None
    assert context.annual_context.fiscal_year == 2025
    assert context.annual_context.source_id == "annual_financials:FY2025"


def test_q4_may_include_same_year_completed_annual_result(
    financial_datasets: FinancialDatasets,
) -> None:
    context = build_grounding_context(financial_datasets, "FY2026-Q4")
    assert context.annual_context is not None
    assert context.annual_context.fiscal_year == 2026
    assert context.annual_context.source_id == "annual_financials:FY2026"


def test_q1_previous_quarter_crosses_fiscal_year(
    financial_datasets: FinancialDatasets,
) -> None:
    context = build_grounding_context(financial_datasets, "FY2026-Q1")
    assert context.previous_quarter is not None
    assert context.previous_quarter.period.identifier == "FY2025-Q4"


def test_context_uses_decimal_and_specific_source_ids(
    financial_datasets: FinancialDatasets,
) -> None:
    context = build_grounding_context(financial_datasets, "FY2026-Q4")
    figures = _figures_by_metric(context.current_period)
    assert figures[MetricName.REVENUE] == Decimal("90000000000")
    assert figures[MetricName.REVENUE_YOY_GROWTH_PCT] == Decimal("12.5")
    assert context.current_period.source_id == (
        "quarterly_analytics:FY2026-Q4"
    )
    assert {source.source_id for source in context.sources} >= {
        "quarterly_analytics:FY2026-Q4",
        "annual_financials:FY2026",
    }


def test_incomplete_core_metrics_are_ineligible(
    financial_datasets: FinancialDatasets,
) -> None:
    analytics = financial_datasets.quarterly_analytics.copy()
    analytics.loc[
        (analytics["fiscal_year"] == 2026)
        & (analytics["fiscal_period"] == "Q2"),
        "net_income",
    ] = pd.NA
    incomplete = FinancialDatasets(
        latest=financial_datasets.latest,
        quarterly_analytics=analytics,
        annual=financial_datasets.annual,
        quarterly_financials=financial_datasets.quarterly_financials,
    )
    with pytest.raises(GroundingError, match="missing one or more core"):
        build_grounding_context(incomplete, "FY2026-Q2")


def test_missing_period_fails_clearly(
    financial_datasets: FinancialDatasets,
) -> None:
    with pytest.raises(GroundingError, match="unavailable"):
        build_grounding_context(financial_datasets, "FY2030-Q1")


def test_approved_csv_integration_for_first_validation_case() -> None:
    context = build_grounding_context(
        load_financial_datasets(),
        "FY2026-Q4",
    )
    figures = _figures_by_metric(context.current_period)
    assert figures[MetricName.REVENUE] == Decimal("90007000000")
    assert context.annual_context is not None
    assert context.annual_context.fiscal_year == 2026
