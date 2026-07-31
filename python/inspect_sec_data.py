import json
from datetime import date
from pathlib import Path


DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "raw"
    / "microsoft_companyfacts.json"
)


def load_sec_data() -> dict:
    with DATA_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def search_metrics(search_term: str) -> None:
    data = load_sec_data()
    us_gaap_facts = data["facts"].get("us-gaap", {})

    matches = []

    for metric_name, metric_details in us_gaap_facts.items():
        label = metric_details.get("label", "")
        description = metric_details.get("description", "")

        searchable_text = f"{metric_name} {label} {description}".lower()

        if search_term.lower() in searchable_text:
            matches.append((metric_name, label))

    print(f'\nResults for "{search_term}": {len(matches)} matches\n')

    for metric_name, label in matches:
        print(f"- {metric_name}")
        print(f"  Label: {label}\n")


def calculate_duration_days(start_date: str, end_date: str) -> int:
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    return (end - start).days + 1


def classify_duration(duration_days: int) -> str:
    if 80 <= duration_days <= 100:
        return "Quarter"
    if 170 <= duration_days <= 195:
        return "Six Months"
    if 260 <= duration_days <= 285:
        return "Nine Months"
    if 350 <= duration_days <= 380:
        return "Full Year"

    return "Other"


def preview_metric(metric_name: str, limit: int = 10) -> None:
    data = load_sec_data()
    metric = data["facts"]["us-gaap"].get(metric_name)

    if metric is None:
        print(f'Metric "{metric_name}" was not found.')
        return

    print(f"\nMetric: {metric_name}")
    print(f"Label: {metric.get('label')}")
    print(f"Description: {metric.get('description')}")

    units = metric.get("units", {})

    for unit_name, observations in units.items():
        print(f"\nUnit: {unit_name}")
        print(f"Total observations: {len(observations)}")

        for observation in observations[-limit:]:
            start_date = observation.get("start")
            end_date = observation.get("end")

            if start_date and end_date:
                duration_days = calculate_duration_days(
                    start_date,
                    end_date,
                )
                duration_type = classify_duration(duration_days)
            else:
                duration_days = None
                duration_type = "Instant"

            print(
                f"- Start: {start_date} | "
                f"End: {end_date} | "
                f"Days: {duration_days} | "
                f"Type: {duration_type} | "
                f"Value: {observation.get('val')} | "
                f"FY: {observation.get('fy')} | "
                f"Period: {observation.get('fp')} | "
                f"Form: {observation.get('form')} | "
                f"Filed: {observation.get('filed')}"
            )


if __name__ == "__main__":
    preview_metric(
        "RevenueFromContractWithCustomerExcludingAssessedTax"
    )