import sqlite3
from pathlib import Path

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database location
DB_PATH = BASE_DIR / "data" / "industrial_monitoring.db"

# SQL schema location
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"


def get_connection():
    """Create a SQLite database connection."""

    connection = sqlite3.connect(DB_PATH)

    # Enable foreign key validation
    connection.execute("PRAGMA foreign_keys = ON")

    # Return rows as dictionary-like objects
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    """Create database and all required tables."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Schema file not found: {SCHEMA_PATH}"
        )

    connection = get_connection()

    try:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        connection.executescript(schema)

        print("Database initialized successfully!")
        print(f"Database location: {DB_PATH}")

    finally:
        connection.close()


def get_all_tables():
    """Return all database table names."""

    connection = get_connection()

    try:
        cursor = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)

        return [row["name"] for row in cursor.fetchall()]

    finally:
        connection.close()


if __name__ == "__main__":

    initialize_database()

    print("\nCreated database tables:")

    for table in get_all_tables():
        print(f" - {table}")