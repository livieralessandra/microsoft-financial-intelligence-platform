import csv
import json
from datetime import date, datetime, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "microsoft_companyfacts.json"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "microsoft_quarterly_financials.csv"
)


METRICS = {
    "revenue": (
        "RevenueFromContractWithCustomerExcludingAssessedTax"
    ),
    "gross_profit": "GrossProfit",
    "operating_income": "OperatingIncomeLoss",
    "net_income": "NetIncomeLoss",
}

NON_NEGATIVE_METRICS = {
    "revenue",
    "gross_profit",
}


def load_sec_data() -> dict:
    with DATA_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def calculate_duration_days(
    start_date: str,
    end_date: str,
) -> int:
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    return (end - start).days + 1


def is_duration_between(
    observation: dict,
    minimum_days: int,
    maximum_days: int,
) -> bool:
    start_date = observation.get("start")
    end_date = observation.get("end")

    if not start_date or not end_date:
        return False

    duration_days = calculate_duration_days(
        start_date,
        end_date,
    )

    return minimum_days <= duration_days <= maximum_days


def derive_fiscal_period(
    end_date: str,
) -> str | None:
    end = date.fromisoformat(end_date)

    quarter_by_month = {
        9: "Q1",
        12: "Q2",
        3: "Q3",
    }

    return quarter_by_month.get(end.month)


def derive_fiscal_year(
    end_date: str,
) -> int | None:
    """
    Derives Microsoft's fiscal year from the period end date.

    Microsoft fiscal years end on June 30:
    - September and December periods belong to the next calendar year.
    - March and June periods belong to the current calendar year.
    """
    end = date.fromisoformat(end_date)

    if end.month in {9, 12}:
        return end.year + 1

    if end.month in {3, 6}:
        return end.year

    return None


def belongs_to_fiscal_period(
    observation: dict,
    fiscal_year: int,
    fiscal_period: str,
) -> bool:
    """
    Returns whether an observation is for the filing's own fiscal period.

    Company Facts includes comparative periods from earlier years in later
    filings. Their start and end dates describe the earlier period, while
    ``fy`` and ``fp`` identify the fiscal context of the filing that reported
    them. Requiring both to match prevents a later comparative filing from
    replacing the observation reported for the period itself.
    """
    try:
        observation_fiscal_year = int(observation.get("fy"))
    except (TypeError, ValueError):
        return False

    return (
        observation_fiscal_year == fiscal_year
        and observation.get("fp") == fiscal_period
    )


def keep_latest_observation(
    observations: dict,
    key: tuple,
    observation: dict,
) -> None:
    """
    Keeps the most recently filed observation for a key.
    """
    existing_observation = observations.get(key)

    if existing_observation is None:
        observations[key] = observation
        return

    new_filed_date = observation.get("filed") or ""
    existing_filed_date = (
        existing_observation.get("filed") or ""
    )

    if new_filed_date > existing_filed_date:
        observations[key] = observation


def extract_quarterly_observations(
    sec_data: dict,
) -> list[dict]:
    """
    Extracts Q1-Q3 from 10-Q filings and derives Q4 using:

        Q4 = Full-year 10-K value
             - Nine-month Q3 10-Q value
    """
    rows = []

    annual_observations = {}
    nine_month_observations = {}

    us_gaap_facts = sec_data["facts"]["us-gaap"]

    for metric_name, sec_metric in METRICS.items():
        metric_data = us_gaap_facts.get(sec_metric)

        if not metric_data:
            print(
                f"Warning: SEC metric not found: "
                f"{sec_metric}"
            )
            continue

        usd_observations = (
            metric_data
            .get("units", {})
            .get("USD", [])
        )

        for observation in usd_observations:
            form = observation.get("form")
            start_date = observation.get("start")
            end_date = observation.get("end")
            value = observation.get("val")

            if (
                not start_date
                or not end_date
                or value is None
            ):
                continue

            fiscal_year = derive_fiscal_year(
                end_date
            )

            if fiscal_year is None:
                continue

            # Q1, Q2, and Q3 individual quarter values.
            if (
                form == "10-Q"
                and is_duration_between(
                    observation,
                    80,
                    100,
                )
            ):
                fiscal_period = derive_fiscal_period(
                    end_date
                )

                if fiscal_period not in {
                    "Q1",
                    "Q2",
                    "Q3",
                }:
                    continue

                if not belongs_to_fiscal_period(
                    observation,
                    fiscal_year,
                    fiscal_period,
                ):
                    continue

                rows.append(
                    {
                        "metric": metric_name,
                        "sec_metric": sec_metric,
                        "start_date": start_date,
                        "end_date": end_date,
                        "fiscal_year": fiscal_year,
                        "fiscal_period": fiscal_period,
                        "value": value,
                        "form": form,
                        "filed_date": observation.get(
                            "filed"
                        ),
                        "accession_number": observation.get(
                            "accn"
                        ),
                    }
                )

                continue

            # Nine-month cumulative value from the Q3 10-Q.
            if (
                form == "10-Q"
                and is_duration_between(
                    observation,
                    260,
                    285,
                )
            ):
                key = (
                    metric_name,
                    fiscal_year,
                )

                if not belongs_to_fiscal_period(
                    observation,
                    fiscal_year,
                    "Q3",
                ):
                    continue

                keep_latest_observation(
                    nine_month_observations,
                    key,
                    observation,
                )

                continue

            # Full-year value from the 10-K.
            if (
                form == "10-K"
                and is_duration_between(
                    observation,
                    350,
                    380,
                )
            ):
                key = (
                    metric_name,
                    fiscal_year,
                )

                if not belongs_to_fiscal_period(
                    observation,
                    fiscal_year,
                    "FY",
                ):
                    continue

                keep_latest_observation(
                    annual_observations,
                    key,
                    observation,
                )

    # Derive Q4 after gathering annual and nine-month values.
    for key, annual_observation in annual_observations.items():
        metric_name, fiscal_year = key

        nine_month_observation = (
            nine_month_observations.get(key)
        )

        if nine_month_observation is None:
            print(
                f"Warning: Could not derive "
                f"{metric_name} FY{fiscal_year} Q4 "
                f"because the nine-month value is missing."
            )
            continue

        full_year_value = annual_observation.get("val")
        nine_month_value = nine_month_observation.get(
            "val"
        )

        if (
            full_year_value is None
            or nine_month_value is None
        ):
            continue

        annual_end_date = date.fromisoformat(
            annual_observation["end"]
        )

        nine_month_end_date = date.fromisoformat(
            nine_month_observation["end"]
        )

        if nine_month_end_date >= annual_end_date:
            print(
                f"Warning: Could not derive "
                f"{metric_name} FY{fiscal_year} Q4 "
                f"because the period dates are inconsistent."
            )
            continue

        q4_value = (
            full_year_value
            - nine_month_value
        )

        if (
            q4_value < 0
            and metric_name in NON_NEGATIVE_METRICS
        ):
            print(
                f"Warning: Could not derive "
                f"{metric_name} FY{fiscal_year} Q4 "
                f"because the calculated value is negative."
            )
            continue

        q4_start_date = (
            nine_month_end_date
            + timedelta(days=1)
        ).isoformat()

        q4_end_date = annual_end_date.isoformat()

        rows.append(
            {
                "metric": metric_name,
                "sec_metric": METRICS[metric_name],
                "start_date": q4_start_date,
                "end_date": q4_end_date,
                "fiscal_year": fiscal_year,
                "fiscal_period": "Q4",
                "value": q4_value,
                "form": "DERIVED",
                "filed_date": annual_observation.get(
                    "filed"
                ),
                "accession_number": (
                    f"{annual_observation.get('accn')} | "
                    f"{nine_month_observation.get('accn')}"
                ),
            }
        )

    return rows


def filed_date_sort_value(
    row: dict,
) -> datetime:
    filed_date = row.get("filed_date")

    if not filed_date:
        return datetime.min

    return datetime.fromisoformat(filed_date)


def remove_duplicate_observations(
    rows: list[dict],
) -> list[dict]:
    """
    Keeps the most recently filed observation for each
    metric, fiscal year, and fiscal quarter.
    """
    latest_observations = {}

    for row in rows:
        key = (
            row["metric"],
            row["fiscal_year"],
            row["fiscal_period"],
        )

        existing_row = latest_observations.get(key)

        if existing_row is None:
            latest_observations[key] = row
            continue

        if filed_date_sort_value(
            row
        ) > filed_date_sort_value(existing_row):
            latest_observations[key] = row

    return list(latest_observations.values())


def sort_rows(
    rows: list[dict],
) -> list[dict]:
    period_order = {
        "Q1": 1,
        "Q2": 2,
        "Q3": 3,
        "Q4": 4,
    }

    return sorted(
        rows,
        key=lambda row: (
            int(row["fiscal_year"]),
            period_order[row["fiscal_period"]],
            row["metric"],
        ),
    )


def save_to_csv(
    rows: list[dict],
) -> None:
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "metric",
        "sec_metric",
        "start_date",
        "end_date",
        "fiscal_year",
        "fiscal_period",
        "value",
        "form",
        "filed_date",
        "accession_number",
    ]

    with OUTPUT_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    sec_data = load_sec_data()

    rows = extract_quarterly_observations(
        sec_data
    )

    rows = remove_duplicate_observations(
        rows
    )

    rows = sort_rows(
        rows
    )

    save_to_csv(
        rows
    )

    print(
        f"Processed {len(rows)} "
        "quarterly financial observations."
    )

    print("Saved to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
