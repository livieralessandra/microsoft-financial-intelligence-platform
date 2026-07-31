from pathlib import Path
import sqlite3
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "microsoft_financials.db"
)

SQL_FILE_PATH = (
    PROJECT_ROOT
    / "sql"
    / "create_views.sql"
)


def create_analytics_views() -> None:
    """
    Create or recreate all analytics views in the SQLite database.
    """

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    if not SQL_FILE_PATH.exists():
        raise FileNotFoundError(
            f"SQL file not found: {SQL_FILE_PATH}"
        )

    sql_script = SQL_FILE_PATH.read_text(
        encoding="utf-8"
    )

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        connection.executescript(sql_script)
        connection.commit()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'view'
            ORDER BY name;
            """
        )

        views = [
            row[0]
            for row in cursor.fetchall()
        ]

        print("Analytics views created successfully.")
        print()
        print("Database:")
        print(DATABASE_PATH)
        print()
        print("Views:")

        for view in views:
            print(f"- {view}")

    except sqlite3.Error as error:
        connection.rollback()

        raise RuntimeError(
            f"Failed to create analytics views: {error}"
        ) from error

    finally:
        connection.close()


def main() -> None:
    try:
        create_analytics_views()

    except (
        FileNotFoundError,
        RuntimeError,
    ) as error:
        print(f"Error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()