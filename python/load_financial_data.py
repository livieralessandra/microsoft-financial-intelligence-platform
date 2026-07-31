import csv
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CSV_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "microsoft_quarterly_financials.csv"
)

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "microsoft_financials.db"
)


def load_csv_rows() -> list[dict]:
    with CSV_PATH.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader)


def create_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS quarterly_financials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric TEXT NOT NULL,
            sec_metric TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            fiscal_year INTEGER NOT NULL,
            fiscal_period TEXT NOT NULL,
            value INTEGER NOT NULL,
            form TEXT NOT NULL,
            filed_date TEXT,
            accession_number TEXT,
            UNIQUE (
                metric,
                fiscal_year,
                fiscal_period
            )
        )
        """
    )


def clear_existing_data(
    connection: sqlite3.Connection,
) -> None:
    connection.execute(
        "DELETE FROM quarterly_financials"
    )


def insert_rows(
    connection: sqlite3.Connection,
    rows: list[dict],
) -> None:
    connection.executemany(
        """
        INSERT INTO quarterly_financials (
            metric,
            sec_metric,
            start_date,
            end_date,
            fiscal_year,
            fiscal_period,
            value,
            form,
            filed_date,
            accession_number
        )
        VALUES (
            :metric,
            :sec_metric,
            :start_date,
            :end_date,
            :fiscal_year,
            :fiscal_period,
            :value,
            :form,
            :filed_date,
            :accession_number
        )
        """,
        rows,
    )


def count_rows(
    connection: sqlite3.Connection,
) -> int:
    result = connection.execute(
        """
        SELECT COUNT(*)
        FROM quarterly_financials
        """
    ).fetchone()

    return result[0]


def main() -> None:
    rows = load_csv_rows()

    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with sqlite3.connect(DATABASE_PATH) as connection:
        create_table(connection)
        clear_existing_data(connection)
        insert_rows(connection, rows)

        connection.commit()

        total_rows = count_rows(connection)

    print(
        f"Loaded {total_rows} financial observations "
        "into SQLite."
    )

    print("Database saved to:")
    print(DATABASE_PATH)


if __name__ == "__main__":
    main()