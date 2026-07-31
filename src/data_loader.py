"""Validated, cached loading for the approved Power BI export datasets."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIRECTORY = PROJECT_ROOT / "data" / "powerbi"
MINIMUM_FISCAL_YEAR = 2019
FINANCIAL_COLUMNS = (
    "revenue",
    "gross_profit",
    "operating_income",
    "net_income",
)

DATASET_COLUMNS = {
    "latest_quarter.csv": (
        "fiscal_year", "fiscal_period", "quarter_number", "revenue",
        "gross_profit", "operating_income", "net_income",
        "previous_quarter_revenue", "prior_year_quarter_revenue",
        "revenue_qoq_change", "revenue_qoq_growth_pct",
        "revenue_yoy_change", "revenue_yoy_growth_pct",
        "gross_margin_pct", "operating_margin_pct", "net_margin_pct",
    ),
    "quarterly_analytics.csv": (
        "fiscal_year", "fiscal_period", "quarter_number", "revenue",
        "gross_profit", "operating_income", "net_income",
        "previous_quarter_revenue", "prior_year_quarter_revenue",
        "revenue_qoq_change", "revenue_qoq_growth_pct",
        "revenue_yoy_change", "revenue_yoy_growth_pct",
        "gross_margin_pct", "operating_margin_pct", "net_margin_pct",
    ),
    "annual_financials.csv": (
        "fiscal_year", "revenue", "gross_profit", "operating_income",
        "net_income", "prior_year_revenue", "revenue_yoy_change",
        "revenue_yoy_growth_pct", "gross_margin_pct",
        "operating_margin_pct", "net_margin_pct",
        "operating_income_yoy_growth_pct", "net_income_yoy_growth_pct",
    ),
    "quarterly_financials.csv": (
        "fiscal_year", "fiscal_period", "revenue", "gross_profit",
        "operating_income", "net_income",
    ),
}


class DataValidationError(RuntimeError):
    """Raised when an approved application dataset is missing or invalid."""


@dataclass(frozen=True)
class FinancialDatasets:
    """Validated datasets used by the three application pages."""

    latest: pd.DataFrame
    quarterly_analytics: pd.DataFrame
    annual: pd.DataFrame
    quarterly_financials: pd.DataFrame


def _read_and_validate(
    file_name: str,
    required_columns: tuple[str, ...],
) -> pd.DataFrame:
    path = DATA_DIRECTORY / file_name
    if not path.is_file():
        raise DataValidationError(
            f"Required dataset is missing: {path}. Run "
            "`python3 python/build_powerbi_dataset.py` from the repository root."
        )
    try:
        frame = pd.read_csv(path)
    except (OSError, pd.errors.ParserError) as error:
        raise DataValidationError(
            f"Could not read {file_name}: {error}"
        ) from error
    if frame.empty:
        raise DataValidationError(f"Required dataset is empty: {path}")
    missing = [
        column for column in required_columns
        if column not in frame.columns
    ]
    if missing:
        raise DataValidationError(
            f"{file_name} is missing required columns: {', '.join(missing)}"
        )
    return frame


def _coerce_numeric_columns(
    frame: pd.DataFrame,
    excluded: set[str],
) -> pd.DataFrame:
    result = frame.copy()
    for column in result.columns:
        if column not in excluded:
            result[column] = pd.to_numeric(result[column], errors="coerce")
    return result


def _complete_fiscal_years(quarterly: pd.DataFrame) -> set[int]:
    """Find years containing Q1-Q4 and all four MVP financial metrics."""
    required_periods = {"Q1", "Q2", "Q3", "Q4"}
    complete: set[int] = set()
    for fiscal_year, rows in quarterly.groupby("fiscal_year"):
        periods = set(rows["fiscal_period"].dropna())
        has_metrics = rows[list(FINANCIAL_COLUMNS)].notna().all().all()
        if periods == required_periods and has_metrics:
            complete.add(int(fiscal_year))
    return complete


@st.cache_data(show_spinner=False)
def load_financial_datasets() -> FinancialDatasets:
    """Load, validate, type, sort, and scope the approved CSV exports."""
    loaded = {
        name: _read_and_validate(name, columns)
        for name, columns in DATASET_COLUMNS.items()
    }
    latest = _coerce_numeric_columns(
        loaded["latest_quarter.csv"], {"fiscal_period"}
    )
    if len(latest) != 1:
        raise DataValidationError(
            "latest_quarter.csv must contain exactly one data row; "
            f"found {len(latest)}."
        )

    analytics = _coerce_numeric_columns(
        loaded["quarterly_analytics.csv"], {"fiscal_period"}
    )
    quarterly = _coerce_numeric_columns(
        loaded["quarterly_financials.csv"], {"fiscal_period"}
    )
    annual = _coerce_numeric_columns(
        loaded["annual_financials.csv"], set()
    )
    analytics = (
        analytics[analytics["fiscal_year"] >= MINIMUM_FISCAL_YEAR]
        .sort_values(["fiscal_year", "quarter_number"])
        .reset_index(drop=True)
    )

    quarter_order = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}
    quarterly = quarterly[
        quarterly["fiscal_year"] >= MINIMUM_FISCAL_YEAR
    ].copy()
    quarterly["quarter_number"] = quarterly["fiscal_period"].map(
        quarter_order
    )
    if quarterly["quarter_number"].isna().any():
        invalid = sorted(
            quarterly.loc[
                quarterly["quarter_number"].isna(), "fiscal_period"
            ].astype(str).unique()
        )
        raise DataValidationError(
            "quarterly_financials.csv contains unsupported fiscal periods: "
            f"{', '.join(invalid)}"
        )
    quarterly = quarterly.sort_values(
        ["fiscal_year", "quarter_number"]
    ).reset_index(drop=True)

    complete_years = _complete_fiscal_years(quarterly)
    annual = (
        annual[
            annual["fiscal_year"].isin(complete_years)
            & (annual["fiscal_year"] >= MINIMUM_FISCAL_YEAR)
        ]
        .sort_values("fiscal_year")
        .reset_index(drop=True)
    )
    if analytics.empty:
        raise DataValidationError(
            "No quarterly analytics are available from FY2019 onward."
        )
    if quarterly.empty:
        raise DataValidationError(
            "No quarterly financial data are available from FY2019 onward."
        )
    if annual.empty:
        raise DataValidationError(
            "No complete fiscal years are available from FY2019 onward."
        )
    return FinancialDatasets(latest, analytics, annual, quarterly)
