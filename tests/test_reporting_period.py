"""Tests for generic fiscal-period identification and transitions."""

import pytest
from pydantic import ValidationError

from src.ai.schemas import ReportingPeriod


def test_parse_and_canonical_identifier() -> None:
    period = ReportingPeriod.parse("FY2026-Q4")
    assert period.fiscal_year == 2026
    assert period.fiscal_period == "Q4"
    assert period.identifier == "FY2026-Q4"
    assert period.quarter_number == 4


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("2026-Q4", "format"),
        ("FY2026-Q5", "format"),
        ("FY26-Q4", "format"),
        ("FY2026-q4", "format"),
    ],
)
def test_rejects_invalid_identifiers(value: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        ReportingPeriod.parse(value)


def test_rejects_boolean_fiscal_year() -> None:
    with pytest.raises(ValidationError):
        ReportingPeriod(fiscal_year=True, fiscal_period="Q1")


@pytest.mark.parametrize(
    ("period", "previous"),
    [
        ("FY2026-Q1", "FY2025-Q4"),
        ("FY2026-Q2", "FY2026-Q1"),
        ("FY2026-Q3", "FY2026-Q2"),
        ("FY2026-Q4", "FY2026-Q3"),
    ],
)
def test_previous_quarter_is_generic(period: str, previous: str) -> None:
    assert ReportingPeriod.parse(period).previous_quarter().identifier == previous


def test_prior_year_quarter_is_generic() -> None:
    period = ReportingPeriod.parse("FY2024-Q2")
    assert period.prior_year_quarter().identifier == "FY2023-Q2"
