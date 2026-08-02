"""Tests for strict grounding and executive-briefing schemas."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.ai.schemas import (
    FigureUnit,
    GroundedFigure,
    MetricName,
    ReportingPeriod,
    SourceReference,
)


def test_models_forbid_extra_fields() -> None:
    with pytest.raises(ValidationError, match="Extra inputs"):
        ReportingPeriod(
            fiscal_year=2026,
            fiscal_period="Q4",
            extra_field="not allowed",
        )


@pytest.mark.parametrize("value", ["NaN", "Infinity", True])
def test_figure_rejects_non_finite_or_boolean_values(value: object) -> None:
    with pytest.raises(ValidationError):
        GroundedFigure(
            metric=MetricName.REVENUE,
            value=value,
            unit=FigureUnit.USD,
            source_id="quarterly_analytics:FY2026-Q4",
        )


def test_usd_figure_requires_integer_dollars() -> None:
    with pytest.raises(ValidationError, match="integer dollar"):
        GroundedFigure(
            metric=MetricName.REVENUE,
            value=Decimal("10.50"),
            unit=FigureUnit.USD,
            source_id="quarterly_analytics:FY2026-Q4",
        )


def test_metric_requires_correct_unit() -> None:
    with pytest.raises(ValidationError, match="must use unit percent"):
        GroundedFigure(
            metric=MetricName.GROSS_MARGIN_PCT,
            value=Decimal("67.20"),
            unit=FigureUnit.USD,
            source_id="quarterly_analytics:FY2026-Q4",
        )


def test_source_id_must_be_deterministic() -> None:
    with pytest.raises(ValidationError, match="expected"):
        SourceReference(
            source_id="quarterly_analytics:latest",
            dataset="quarterly_analytics",
            period_id="FY2026-Q4",
        )


def test_valid_source_id_identifies_dataset_and_period() -> None:
    source = SourceReference(
        source_id="annual_financials:FY2026",
        dataset="annual_financials",
        period_id="FY2026",
    )
    assert source.source_id == "annual_financials:FY2026"
