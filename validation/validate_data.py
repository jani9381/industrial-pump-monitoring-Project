
import sqlite3
from pathlib import Path

DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "industrial_monitoring.db"
)


def validate_database():
    print("\nINDUSTRIAL PUMP MONITORING - DATA VALIDATION")
    print("=" * 55)

    if not DB_PATH.exists():
        print("FAILED: Database file not found:", DB_PATH)
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    errors = []

    try:
        # 1. Database integrity
        integrity = conn.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        print(f"\n1. Database integrity: {integrity}")

        if integrity != "ok":
            errors.append("Database integrity check failed")

        # 2. Required tables
        required_tables = [
            "facilities", "network_nodes", "pumps", "tanks",
            "valves", "pipes", "sensors", "telemetry",
            "ground_truth"
        ]

        existing_tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }

        missing_tables = [
            table for table in required_tables
            if table not in existing_tables
        ]

        print("\n2. Required tables")

        if missing_tables:
            print("Missing:", missing_tables)
            errors.append("Required tables are missing")
        else:
            print("PASSED: All required tables exist")

        if "telemetry" not in existing_tables:
            print("Cannot continue: telemetry table is missing.")
            return

        # 3. Telemetry count
        total = conn.execute(
            "SELECT COUNT(*) FROM telemetry"
        ).fetchone()[0]

        print(f"\n3. Total telemetry records: {total:,}")

        if total == 0:
            errors.append("No telemetry records found")

        # 4. Quality distribution
        quality_rows = conn.execute("""
            SELECT quality_status, COUNT(*) AS total
            FROM telemetry
            GROUP BY quality_status
        """).fetchall()

        print("\n4. Telemetry quality distribution")

        for row in quality_rows:
            print(f"{row['quality_status']}: {row['total']:,}")

        # 5. Missing required values
        missing = conn.execute("""
            SELECT COUNT(*)
            FROM telemetry
            WHERE reading IS NULL
               OR timestamp IS NULL
               OR sensor_id IS NULL
        """).fetchone()[0]

        print(f"\n5. Missing required telemetry values: {missing}")

        if missing > 0:
            errors.append("Missing telemetry values detected")

        # 6. Sensor range validation
        out_of_range = conn.execute("""
            SELECT COUNT(*)
            FROM telemetry t
            JOIN sensors s ON t.sensor_id = s.sensor_id
            WHERE t.reading < s.min_value
               OR t.reading > s.max_value
        """).fetchone()[0]

        print(f"\n6. Readings outside sensor range: {out_of_range}")

        if out_of_range > 0:
            errors.append("Sensor readings outside configured ranges")

        # 7. Tank level validation
        level_stats = conn.execute("""
            SELECT
                COUNT(*) AS total,
                AVG(t.reading) AS average_level,
                MIN(t.reading) AS minimum_level,
                MAX(t.reading) AS maximum_level
            FROM telemetry t
            JOIN sensors s ON t.sensor_id = s.sensor_id
            WHERE s.sensor_type = 'LEVEL'
              AND t.quality_status = 'GOOD'
        """).fetchone()

        print("\n7. Tank LEVEL telemetry")

        if level_stats["total"] > 0:
            print(f"LEVEL readings: {level_stats['total']:,}")
            print(f"Average: {level_stats['average_level']:.2f}%")
            print(f"Minimum: {level_stats['minimum_level']:.2f}%")
            print(f"Maximum: {level_stats['maximum_level']:.2f}%")

            tank_rows = conn.execute("""
                SELECT
                    s.sensor_id,
                    s.tank_id,
                    AVG(t.reading) AS actual_average,
                    k.current_level,
                    k.capacity_liters
                FROM sensors s
                JOIN tanks k ON s.tank_id = k.tank_id
                JOIN telemetry t ON t.sensor_id = s.sensor_id
                WHERE s.sensor_type = 'LEVEL'
                  AND t.quality_status = 'GOOD'
                GROUP BY s.sensor_id
            """).fetchall()

            inconsistent = 0

            for row in tank_rows:
                capacity = row["capacity_liters"]

                if not capacity or capacity <= 0:
                    inconsistent += 1
                    continue

                expected = (
                    row["current_level"] / capacity
                ) * 100

                actual = row["actual_average"]

                if abs(actual - expected) > 15:
                    inconsistent += 1

            print(
                "Tank sensors with large average deviation:",
                inconsistent
            )

            if inconsistent > 0:
                errors.append(
                    "Unexpected tank-level telemetry deviations"
                )
        else:
            print("WARNING: No GOOD LEVEL telemetry found")

        # 8. Ground truth
        if "ground_truth" in existing_tables:
            ground_truth_count = conn.execute(
                "SELECT COUNT(*) FROM ground_truth"
            ).fetchone()[0]

            print(f"\n8. Ground truth records: {ground_truth_count:,}")

        # 9. Final report
        print("\n" + "=" * 55)

        if errors:
            print("RESULT: FAILED")
            for error in errors:
                print("-", error)
        else:
            print("RESULT: PASSED")
            print("No critical data quality issues detected.")

    finally:
        conn.close()


if __name__ == "__main__":
    validate_database()
