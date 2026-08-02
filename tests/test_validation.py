"""Tests for structured figure and source validation."""

from decimal import Decimal
from pathlib import Path

import pytest

from src.ai.schemas import (
    BriefingFigureClaim,
    BriefingInsight,
    ExecutiveBriefing,
    FigureUnit,
    GroundingContext,
    MetricName,
    ReportingPeriod,
)
from src.ai.validation import BriefingValidationError, validate_briefing


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def context() -> GroundingContext:
    return GroundingContext.model_validate_json(
        (FIXTURES / "fy2026_q4_grounding_context.json").read_text()
    )


@pytest.fixture
def briefing() -> ExecutiveBriefing:
    return ExecutiveBriefing.model_validate_json(
        (FIXTURES / "fy2026_q4_executive_briefing.json").read_text()
    )


def _briefing_with_claim(
    claim: BriefingFigureClaim,
    source_ids: tuple[str, ...] = (
        "quarterly_analytics:FY2026-Q4",
    ),
    period: ReportingPeriod | None = None,
) -> ExecutiveBriefing:
    return ExecutiveBriefing(
        reporting_period=period or ReportingPeriod.parse("FY2026-Q4"),
        headline="Validated financial result",
        executive_summary="A structured claim is validated against context.",
        insights=(
            BriefingInsight(
                category="current_performance",
                title="Validated claim",
                narrative="The approved figure is presented for review.",
                figure_claims=(claim,),
            ),
        ),
        source_ids=source_ids,
    )


def test_deterministic_json_fixtures_validate(
    briefing: ExecutiveBriefing,
    context: GroundingContext,
) -> None:
    validate_briefing(briefing, context)


def test_integer_dollar_claims_must_match_exactly(
    context: GroundingContext,
) -> None:
    claim = BriefingFigureClaim(
        metric=MetricName.REVENUE,
        value=Decimal("90007000001"),
        unit=FigureUnit.USD,
        source_id="quarterly_analytics:FY2026-Q4",
    )
    with pytest.raises(BriefingValidationError, match="Figure mismatch"):
        validate_briefing(_briefing_with_claim(claim), context)


@pytest.mark.parametrize("value", ["17.74", "17.75", "17.76"])
def test_percentage_claims_use_documented_tolerance(
    value: str,
    context: GroundingContext,
) -> None:
    claim = BriefingFigureClaim(
        metric=MetricName.REVENUE_YOY_GROWTH_PCT,
        value=Decimal(value),
        unit=FigureUnit.PERCENT,
        source_id="quarterly_analytics:FY2026-Q4",
    )
    validate_briefing(_briefing_with_claim(claim), context)


def test_percentage_outside_tolerance_fails(
    context: GroundingContext,
) -> None:
    claim = BriefingFigureClaim(
        metric=MetricName.REVENUE_YOY_GROWTH_PCT,
        value=Decimal("17.761"),
        unit=FigureUnit.PERCENT,
        source_id="quarterly_analytics:FY2026-Q4",
    )
    with pytest.raises(BriefingValidationError, match="Figure mismatch"):
        validate_briefing(_briefing_with_claim(claim), context)


def test_claim_metric_is_part_of_grounding_key(
    context: GroundingContext,
) -> None:
    claim = BriefingFigureClaim(
        metric=MetricName.NET_INCOME,
        value=Decimal("90007000000"),
        unit=FigureUnit.USD,
        source_id="quarterly_analytics:FY2026-Q4",
    )
    with pytest.raises(BriefingValidationError, match="Unsupported figure"):
        validate_briefing(_briefing_with_claim(claim), context)


def test_unsupported_source_id_fails(
    context: GroundingContext,
) -> None:
    claim = BriefingFigureClaim(
        metric=MetricName.REVENUE,
        value=Decimal("90007000000"),
        unit=FigureUnit.USD,
        source_id="quarterly_analytics:FY2027-Q1",
    )
    briefing = _briefing_with_claim(
        claim,
        source_ids=("quarterly_analytics:FY2027-Q1",),
    )
    with pytest.raises(BriefingValidationError, match="Unsupported"):
        validate_briefing(briefing, context)


def test_claim_source_must_be_declared(
    context: GroundingContext,
) -> None:
    claim = BriefingFigureClaim(
        metric=MetricName.REVENUE,
        value=Decimal("90007000000"),
        unit=FigureUnit.USD,
        source_id="quarterly_analytics:FY2026-Q4",
    )
    briefing = _briefing_with_claim(claim, source_ids=("other:source",))
    with pytest.raises(
        BriefingValidationError,
        match="undeclared source IDs",
    ):
        validate_briefing(briefing, context)


def test_reporting_period_must_match_context(
    context: GroundingContext,
) -> None:
    claim = BriefingFigureClaim(
        metric=MetricName.REVENUE,
        value=Decimal("90007000000"),
        unit=FigureUnit.USD,
        source_id="quarterly_analytics:FY2026-Q4",
    )
    briefing = _briefing_with_claim(
        claim,
        period=ReportingPeriod.parse("FY2025-Q4"),
    )
    with pytest.raises(BriefingValidationError, match="reporting period"):
        validate_briefing(briefing, context)


def test_narrative_text_is_not_broadly_parsed_in_phase_one(
    briefing: ExecutiveBriefing,
    context: GroundingContext,
) -> None:
    """Phase 1 validates structured claims, not arbitrary prose numbers."""
    validate_briefing(briefing, context)
