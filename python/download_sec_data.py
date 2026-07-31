import json
from pathlib import Path

import requests


SEC_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK0000789019.json"

HEADERS = {
    "User-Agent": "Microsoft Financial Intelligence Platform livieralessandra2005@outlook.com"
}

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "microsoft_companyfacts.json"


def download_sec_data() -> None:
    response = requests.get(SEC_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()

    data = response.json()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    print(f"SEC data saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    download_sec_data()