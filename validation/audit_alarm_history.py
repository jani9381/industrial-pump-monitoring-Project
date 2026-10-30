import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "industrial_monitoring.db"


def quote(name):
    return '"' + name.replace('"', '""') + '"'


def inspect_table(conn, table):
    print(f"\n========== {table.upper()} ==========")

    columns = conn.execute(
        f"PRAGMA table_info({quote(table)})"
    ).fetchall()

    print("Columns:")
    for column in columns:
        print(f"  {column[1]} ({column[2]})")

    count = conn.execute(
        f"SELECT COUNT(*) FROM {quote(table)}"
    ).fetchone()[0]

    print("Total records:", count)

    if count:
        rows = conn.execute(
            f"SELECT * FROM {quote(table)} LIMIT 10"
        ).fetchall()

        names = [column[1] for column in columns]
        print("Sample records:")
        for row in rows:
            print(dict(zip(names, row)))


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        print("DATABASE:", DB_PATH)

        for table in ("alarms", "equipment_state_events"):
            inspect_table(conn, table)

        alarm_columns = {
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(alarms)"
            ).fetchall()
        }

        print("\n========== ALARM STATUS COUNTS ==========")

        if "status" in alarm_columns:
            for row in conn.execute("""
                SELECT status, COUNT(*) AS total
                FROM alarms
                GROUP BY status
                ORDER BY status
            """):
                print(dict(row))

        print("\n========== POSSIBLE DUPLICATE ALARMS ==========")

        grouping = [
            column for column in ("sensor_id", "fault_type")
            if column in alarm_columns
        ]

        if grouping:
            group_sql = ", ".join(quote(column) for column in grouping)
            query = f"""
                SELECT {group_sql}, COUNT(*) AS total
                FROM alarms
                GROUP BY {group_sql}
                HAVING COUNT(*) > 1
                ORDER BY total DESC
                LIMIT 20
            """

            duplicates = conn.execute(query).fetchall()
            print("Grouping columns:", grouping)
            print("Duplicate groups:", len(duplicates))

            for row in duplicates:
                print(dict(row))
        else:
            print(
                "Could not identify sensor_id and fault_type "
                "columns together. Review the schema above."
            )

        print("\n========== GROUND TRUTH ISSUE COUNTS ==========")

        for row in conn.execute("""
            SELECT issue_type, COUNT(*) AS total
            FROM ground_truth
            GROUP BY issue_type
            ORDER BY issue_type
        """):
            print(dict(row))

        print("\nAUDIT COMPLETE - READ ONLY")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
