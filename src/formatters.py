"""Display formatting helpers that preserve missing and negative values."""

from numbers import Real

import pandas as pd


def format_billions(value: Real | None) -> str:
    """Format a numeric dollar value as USD billions."""
    if value is None or pd.isna(value):
        return "Not available"
    return f"${float(value) / 1_000_000_000:,.1f}B"


def format_percent(
    value: Real | None,
    include_sign: bool = False,
) -> str:
    """Format a percentage while preserving negative values."""
    if value is None or pd.isna(value):
        return "Not available"
    sign = "+" if include_sign and float(value) > 0 else ""
    return f"{sign}{float(value):,.1f}%"


def direction_word(
    value: Real | None,
    positive: str = "increased",
    negative: str = "declined",
) -> str:
    """Return a neutral direction phrase for a numeric change."""
    if value is None or pd.isna(value):
        return "was unavailable"
    if float(value) > 0:
        return positive
    if float(value) < 0:
        return negative
    return "was unchanged"


def fiscal_label(fiscal_year: Real, fiscal_period: str) -> str:
    """Build a consistent fiscal-period label."""
    return f"FY{int(fiscal_year)} {fiscal_period}"
