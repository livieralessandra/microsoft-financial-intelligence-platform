import csv
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "microsoft_quarterly_financials.csv"
)


EXPECTED_METRICS = {
    "revenue",
    "gross_profit",
    "operating_income",
    "net_income",
}

EXPECTED_PERIODS = {
    "Q1",
    "Q2",
    "Q3",
    "Q4",
}

VALIDATION_START_YEAR = 2013


def load_rows() -> list[dict]:
    with DATA_PATH.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader)


def print_section(title: str) -> None:
    print(f"\n{title}")
    print("-" * len(title))


def validate_metrics(rows: list[dict]) -> bool:
    metrics_found = {
        row["metric"]
        for row in rows
    }

    print_section("Metrics")

    for metric in sorted(EXPECTED_METRICS):
        if metric in metrics_found:
            print(f"✓ {metric}")
        else:
            print(f"✗ Missing metric: {metric}")

    unexpected_metrics = metrics_found - EXPECTED_METRICS

    for metric in sorted(unexpected_metrics):
        print(f"✗ Unexpected metric: {metric}")

    return (
        metrics_found == EXPECTED_METRICS
    )


def find_duplicate_periods(
    rows: list[dict],
) -> list[tuple]:
    counts = Counter(
        (
            row["metric"],
            row["fiscal_year"],
            row["fiscal_period"],
        )
        for row in rows
    )

    return [
        key
        for key, count in counts.items()
        if count > 1
    ]


def validate_duplicates(rows: list[dict]) -> bool:
    duplicates = find_duplicate_periods(rows)

    print_section("Duplicate Fiscal Periods")

    if not duplicates:
        print("✓ No duplicate fiscal periods found.")
        return True

    for metric, fiscal_year, fiscal_period in sorted(
        duplicates
    ):
        print(
            f"✗ {metric}: "
            f"FY{fiscal_year} {fiscal_period}"
        )

    return False


def find_missing_periods(
    rows: list[dict],
) -> list[tuple]:
    periods_by_metric_year = defaultdict(set)

    for row in rows:
        fiscal_year = int(row["fiscal_year"])

        if fiscal_year < VALIDATION_START_YEAR:
            continue

        key = (
            row["metric"],
            row["fiscal_year"],
        )


        periods_by_metric_year[key].add(
            row["fiscal_period"]
        )

    missing = []

    for (
        metric,
        fiscal_year,
    ), periods_found in periods_by_metric_year.items():
        missing_periods = (
            EXPECTED_PERIODS - periods_found
        )

        for period in sorted(missing_periods):
            missing.append(
                (
                    metric,
                    fiscal_year,
                    period,
                )
            )

    return missing


def validate_missing_periods(
    rows: list[dict],
) -> bool:
    missing_periods = find_missing_periods(rows)

    print_section("Missing Fiscal Periods")

    if not missing_periods:
        print("✓ No missing fiscal periods found.")
        return True

    for metric, fiscal_year, fiscal_period in sorted(
        missing_periods
    ):
        print(
            f"✗ {metric}: "
            f"FY{fiscal_year} missing {fiscal_period}"
        )

    return False


def validate_values(rows: list[dict]) -> bool:
    invalid_rows = []

    for row in rows:
        try:
            value = int(row["value"])
        except (TypeError, ValueError):
            invalid_rows.append(row)
            continue

        if value == 0:
            invalid_rows.append(row)

    print_section("Values")

    if not invalid_rows:
        print("✓ All values are valid numeric values.")
        return True

    for row in invalid_rows:
        print(
            f"✗ Invalid value: "
            f"{row['metric']} "
            f"FY{row['fiscal_year']} "
            f"{row['fiscal_period']} "
            f"value={row['value']}"
        )

    return False


def summarize_dataset(rows: list[dict]) -> None:
    fiscal_years = sorted(
        {
            int(row["fiscal_year"])
            for row in rows
            if row["fiscal_year"]
        }
    )

    print("================================")
    print("Microsoft Financial Data Review")
    print("================================")

    print(f"\nTotal rows: {len(rows)}")

    if fiscal_years:
        print(
            "Fiscal year range: "
            f"FY{fiscal_years[0]}–FY{fiscal_years[-1]}"
        )


def main() -> None:
    rows = load_rows()

    summarize_dataset(rows)

    results = [
        validate_metrics(rows),
        validate_duplicates(rows),
        validate_missing_periods(rows),
        validate_values(rows),
    ]

    print_section("Final Result")

    if all(results):
        print("✓ Validation passed.")
    else:
        print("✗ Validation failed.")


if __name__ == "__main__":
    main()