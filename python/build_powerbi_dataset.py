import csv
from dataclasses import dataclass
from pathlib import Path
import sqlite3
import sys
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "microsoft_financials.db"
)

OUTPUT_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "powerbi"
)


class ExportError(RuntimeError):
    """Raised when a Power BI dataset cannot be exported safely."""


@dataclass(frozen=True)
class ExportSpec:
    view_name: str
    file_name: str
    required_columns: tuple[str, ...]
    order_by: str
    expected_row_count: int | None = None


EXPORT_SPECS = (
    ExportSpec(
        view_name="vw_latest_quarter",
        file_name="latest_quarter.csv",
        required_columns=(
            "fiscal_year",
            "fiscal_period",
            "quarter_number",
            "revenue",
            "gross_profit",
            "operating_income",
            "net_income",
            "previous_quarter_revenue",
            "prior_year_quarter_revenue",
            "revenue_qoq_change",
            "revenue_qoq_growth_pct",
            "revenue_yoy_change",
            "revenue_yoy_growth_pct",
            "gross_margin_pct",
            "operating_margin_pct",
            "net_margin_pct",
        ),
        order_by="fiscal_year, quarter_number",
        expected_row_count=1,
    ),
    ExportSpec(
        view_name="vw_quarterly_analytics",
        file_name="quarterly_analytics.csv",
        required_columns=(
            "fiscal_year",
            "fiscal_period",
            "quarter_number",
            "revenue",
            "gross_profit",
            "operating_income",
            "net_income",
            "previous_quarter_revenue",
            "prior_year_quarter_revenue",
            "revenue_qoq_change",
            "revenue_qoq_growth_pct",
            "revenue_yoy_change",
            "revenue_yoy_growth_pct",
            "gross_margin_pct",
            "operating_margin_pct",
            "net_margin_pct",
        ),
        order_by="fiscal_year, quarter_number",
    ),
    ExportSpec(
        view_name="vw_annual_financials",
        file_name="annual_financials.csv",
        required_columns=(
            "fiscal_year",
            "revenue",
            "gross_profit",
            "operating_income",
            "net_income",
            "prior_year_revenue",
            "revenue_yoy_change",
            "revenue_yoy_growth_pct",
            "gross_margin_pct",
            "operating_margin_pct",
            "net_margin_pct",
            "operating_income_yoy_growth_pct",
            "net_income_yoy_growth_pct",
        ),
        order_by="fiscal_year",
    ),
    ExportSpec(
        view_name="vw_quarterly_financials",
        file_name="quarterly_financials.csv",
        required_columns=(
            "fiscal_year",
            "fiscal_period",
            "revenue",
            "gross_profit",
            "operating_income",
            "net_income",
        ),
        order_by=(
            "fiscal_year, "
            "CASE fiscal_period "
            "WHEN 'Q1' THEN 1 "
            "WHEN 'Q2' THEN 2 "
            "WHEN 'Q3' THEN 3 "
            "WHEN 'Q4' THEN 4 "
            "ELSE 5 END"
        ),
    ),
)


@dataclass(frozen=True)
class ExportedDataset:
    spec: ExportSpec
    columns: tuple[str, ...]
    rows: tuple[tuple, ...]

    @property
    def output_path(self) -> Path:
        return OUTPUT_DIRECTORY / self.spec.file_name


def connect_read_only(
    database_path: Path,
) -> sqlite3.Connection:
    if not database_path.exists():
        raise ExportError(
            f"SQLite database not found: {database_path}"
        )

    if not database_path.is_file():
        raise ExportError(
            f"SQLite database path is not a file: {database_path}"
        )

    try:
        connection = sqlite3.connect(
            f"{database_path.resolve().as_uri()}?mode=ro",
            uri=True,
        )
    except sqlite3.Error as error:
        raise ExportError(
            f"Could not open SQLite database: {error}"
        ) from error

    return connection


def validate_required_views(
    connection: sqlite3.Connection,
) -> None:
    required_views = {
        spec.view_name
        for spec in EXPORT_SPECS
    }

    try:
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'view'
            """
        ).fetchall()
    except sqlite3.Error as error:
        raise ExportError(
            f"Could not inspect SQLite views: {error}"
        ) from error

    available_views = {
        row[0]
        for row in rows
    }
    missing_views = sorted(
        required_views - available_views
    )

    if missing_views:
        raise ExportError(
            "Required analytics view(s) missing: "
            f"{', '.join(missing_views)}"
        )


def load_dataset(
    connection: sqlite3.Connection,
    spec: ExportSpec,
) -> ExportedDataset:
    try:
        schema_cursor = connection.execute(
            f'SELECT * FROM "{spec.view_name}" LIMIT 0'
        )
        columns = tuple(
            description[0]
            for description in schema_cursor.description
        )
    except sqlite3.Error as error:
        raise ExportError(
            f"Could not inspect {spec.view_name}: {error}"
        ) from error

    missing_columns = [
        column
        for column in spec.required_columns
        if column not in columns
    ]

    if missing_columns:
        raise ExportError(
            f"{spec.view_name} is missing required column(s): "
            f"{', '.join(missing_columns)}"
        )

    query = (
        f'SELECT * FROM "{spec.view_name}" '
        f"ORDER BY {spec.order_by}"
    )

    try:
        cursor = connection.execute(query)
        query_columns = tuple(
            description[0]
            for description in cursor.description
        )
        rows = tuple(cursor.fetchall())
    except sqlite3.Error as error:
        raise ExportError(
            f"Could not read {spec.view_name}: {error}"
        ) from error

    if query_columns != columns:
        raise ExportError(
            f"{spec.view_name} returned inconsistent columns "
            "between schema validation and export."
        )

    if not rows:
        raise ExportError(
            f"{spec.view_name} returned no rows."
        )

    if (
        spec.expected_row_count is not None
        and len(rows) != spec.expected_row_count
    ):
        raise ExportError(
            f"{spec.view_name} must contain exactly "
            f"{spec.expected_row_count} row(s); found {len(rows)}."
        )

    return ExportedDataset(
        spec=spec,
        columns=columns,
        rows=rows,
    )


def write_csv(
    dataset: ExportedDataset,
    temporary_path: Path,
) -> None:
    try:
        with temporary_path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.writer(file)
            writer.writerow(dataset.columns)
            writer.writerows(dataset.rows)
    except OSError as error:
        raise ExportError(
            f"Could not write {dataset.output_path}: {error}"
        ) from error


def publish_datasets(
    datasets: Sequence[ExportedDataset],
) -> None:
    try:
        OUTPUT_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True,
        )
    except OSError as error:
        raise ExportError(
            f"Could not create output directory "
            f"{OUTPUT_DIRECTORY}: {error}"
        ) from error

    temporary_files: list[Path] = []

    try:
        for dataset in datasets:
            temporary_path = (
                OUTPUT_DIRECTORY
                / f".{dataset.spec.file_name}.tmp"
            )
            write_csv(dataset, temporary_path)
            temporary_files.append(temporary_path)

        for dataset, temporary_path in zip(
            datasets,
            temporary_files,
            strict=True,
        ):
            temporary_path.replace(dataset.output_path)
    except (ExportError, OSError) as error:
        for temporary_path in temporary_files:
            try:
                temporary_path.unlink(
                    missing_ok=True
                )
            except OSError:
                pass

        if isinstance(error, ExportError):
            raise

        raise ExportError(
            f"Could not publish Power BI exports: {error}"
        ) from error


def print_summary(
    datasets: Sequence[ExportedDataset],
) -> None:
    print("Power BI datasets exported successfully.")

    for dataset in datasets:
        print(
            f"- {dataset.spec.file_name}: "
            f"{len(dataset.rows)} rows, "
            f"{len(dataset.columns)} columns"
        )
        print(f"  {dataset.output_path}")


def build_powerbi_dataset() -> list[ExportedDataset]:
    connection = connect_read_only(DATABASE_PATH)

    try:
        validate_required_views(connection)
        datasets = [
            load_dataset(connection, spec)
            for spec in EXPORT_SPECS
        ]
    finally:
        connection.close()

    publish_datasets(datasets)
    return datasets


def main() -> None:
    try:
        datasets = build_powerbi_dataset()
    except ExportError as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    print_summary(datasets)


if __name__ == "__main__":
    main()
