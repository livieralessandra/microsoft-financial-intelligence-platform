"""Deterministic injected financial datasets and briefing fixtures."""

from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

from src.ai.schemas import (
    BriefingBusinessClaim,
    BriefingFigureClaim,
    BriefingInsight,
    ExecutiveBriefing,
    FactClassification,
    FigureUnit,
    MetricName,
    ReportingPeriod,
)
from src.data_loader import FinancialDatasets


FIXTURE_DIRECTORY = Path(__file__).parent / "fixtures"


def _quarter(
    fiscal_year: int,
    fiscal_period: str,
    revenue: int,
) -> dict:
    quarter_number = int(fiscal_period[1])
    return {
        "fiscal_year": fiscal_year,
        "fiscal_period": fiscal_period,
        "quarter_number": quarter_number,
        "revenue": revenue,
        "gross_profit": int(revenue * 0.67),
        "operating_income": int(revenue * 0.44),
        "net_income": int(revenue * 0.36),
        "revenue_qoq_growth_pct": 2.25,
        "revenue_yoy_growth_pct": 12.50,
        "gross_margin_pct": 67.00,
        "operating_margin_pct": 44.00,
        "net_margin_pct": 36.00,
    }


@pytest.fixture
def financial_datasets() -> FinancialDatasets:
    quarterly_analytics = pd.DataFrame(
        [
            _quarter(2025, "Q1", 64_000_000_000),
            _quarter(2025, "Q4", 76_000_000_000),
            _quarter(2026, "Q1", 78_000_000_000),
            _quarter(2026, "Q2", 81_000_000_000),
            _quarter(2026, "Q3", 83_000_000_000),
            _quarter(2026, "Q4", 90_000_000_000),
        ]
    )
    annual = pd.DataFrame(
        [
            {
                "fiscal_year": 2025,
                "revenue": 280_000_000_000,
                "gross_profit": 190_000_000_000,
                "operating_income": 125_000_000_000,
                "net_income": 100_000_000_000,
                "revenue_yoy_growth_pct": 14.50,
                "gross_margin_pct": 67.86,
                "operating_margin_pct": 44.64,
                "net_margin_pct": 35.71,
            },
            {
                "fiscal_year": 2026,
                "revenue": 332_000_000_000,
                "gross_profit": 225_000_000_000,
                "operating_income": 155_000_000_000,
                "net_income": 134_000_000_000,
                "revenue_yoy_growth_pct": 18.57,
                "gross_margin_pct": 67.77,
                "operating_margin_pct": 46.69,
                "net_margin_pct": 40.36,
            },
        ]
    )
    return FinancialDatasets(
        latest=quarterly_analytics.tail(1),
        quarterly_analytics=quarterly_analytics,
        annual=annual,
        quarterly_financials=quarterly_analytics[
            [
                "fiscal_year",
                "fiscal_period",
                "revenue",
                "gross_profit",
                "operating_income",
                "net_income",
            ]
        ],
    )


@pytest.fixture
def complete_briefing(financial_datasets: FinancialDatasets) -> ExecutiveBriefing:
    """A complete provider response grounded in the injected FY2026 Q4 data."""
    financial_source = "quarterly_analytics:FY2026-Q4"
    press_source = "msft_ir_fy2026_q4_press_release"
    call_source = "msft_ir_fy2026_q4_earnings_call"
    categories = (
        "overall_performance",
        "primary_drivers",
        "headwinds",
        "profitability_context",
        "attention",
        "investigate_next",
    )
    insights = []
    for category in categories:
        figure_claims = ()
        business_claims = ()
        source_ids = (press_source,)
        management_ids = ()
        if category == "overall_performance":
            source_ids = (financial_source,)
            figure_claims = (
                BriefingFigureClaim(
                    metric=MetricName.REVENUE,
                    value=Decimal("90000000000"),
                    unit=FigureUnit.USD,
                    source_id=financial_source,
                ),
            )
        elif category == "primary_drivers":
            business_claims = (
                BriefingBusinessClaim(
                    metric="segment.intelligent_cloud.contribution_pct",
                    value=Decimal("69.50"),
                    unit=FigureUnit.PERCENT,
                    classification=FactClassification.DERIVED,
                    source_ids=(press_source,),
                ),
            )
        elif category == "headwinds":
            source_ids = (call_source,)
            management_ids = ("windows_oem_weakness",)
        insights.append(
            BriefingInsight(
                category=category,
                title=category.replace("_", " ").title(),
                narrative="Approved context supports this executive observation.",
                classification=FactClassification.AI_INTERPRETATION,
                source_ids=source_ids,
                figure_claims=figure_claims,
                business_claims=business_claims,
                management_explanation_ids=management_ids,
            )
        )
    return ExecutiveBriefing(
        reporting_period=ReportingPeriod.parse("FY2026-Q4"),
        headline="Validated executive briefing",
        executive_summary="A synthesis of approved financial and driver context.",
        insights=tuple(insights),
        source_ids=(financial_source, press_source, call_source),
    )
