
import sqlite3
import random
from pathlib import Path

# Database configuration
DB_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "industrial_monitoring.db"
)

RANDOM_SEED = 20261022
random.seed(RANDOM_SEED)


def fix_level_telemetry():

    print("Starting LEVEL telemetry correction...")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    try:
        # Record counts before correction
        total_before = cursor.execute(
            "SELECT COUNT(*) FROM telemetry"
        ).fetchone()[0]

        suspect_before = cursor.execute("""
            SELECT COUNT(*)
            FROM telemetry
            WHERE quality_status = 'SUSPECT'
        """).fetchone()[0]

        ground_truth_before = cursor.execute(
            "SELECT COUNT(*) FROM ground_truth"
        ).fetchone()[0]

        # Get LEVEL sensors and their tank information
        sensors = cursor.execute("""
            SELECT
                s.sensor_id,
                s.min_value,
                s.max_value,
                s.tank_id,
                t.current_level,
                t.capacity_liters
            FROM sensors s
            JOIN tanks t ON s.tank_id = t.tank_id
            WHERE s.sensor_type = 'LEVEL'
              AND s.status = 'ACTIVE'
            ORDER BY s.sensor_id
        """).fetchall()

        if not sensors:
            raise RuntimeError("No active LEVEL sensors found.")

        updated_records = 0

        for sensor in sensors:

            (
                sensor_id,
                min_value,
                max_value,
                tank_id,
                current_level,
                capacity
            ) = sensor

            min_value = float(min_value)
            max_value = float(max_value)
            current_level = float(current_level)
            capacity = float(capacity)

            if capacity <= 0:
                raise ValueError(
                    f"Invalid capacity for {tank_id}"
                )

            # Correct tank level percentage
            midpoint = (
                current_level / capacity
            ) * 100

            midpoint = max(
                min_value,
                min(max_value, midpoint)
            )

            # Read only normal GOOD telemetry
            records = cursor.execute("""
                SELECT telemetry_id
                FROM telemetry
                WHERE sensor_id = ?
                  AND quality_status = 'GOOD'
                ORDER BY telemetry_id
            """, (sensor_id,)).fetchall()

            for (telemetry_id,) in records:

                # Preserve realistic measurement variation
                noise = random.gauss(
                    0,
                    (max_value - min_value) * 0.025
                )

                reading = midpoint + noise

                reading = max(
                    min_value,
                    min(max_value, reading)
                )

                cursor.execute("""
                    UPDATE telemetry
                    SET reading = ?
                    WHERE telemetry_id = ?
                      AND quality_status = 'GOOD'
                """, (
                    round(reading, 3),
                    telemetry_id
                ))

                updated_records += 1

        # Verify record counts before committing
        total_after = cursor.execute(
            "SELECT COUNT(*) FROM telemetry"
        ).fetchone()[0]

        suspect_after = cursor.execute("""
            SELECT COUNT(*)
            FROM telemetry
            WHERE quality_status = 'SUSPECT'
        """).fetchone()[0]

        ground_truth_after = cursor.execute(
            "SELECT COUNT(*) FROM ground_truth"
        ).fetchone()[0]

        if total_before != total_after:
            raise RuntimeError("Telemetry count changed!")

        if suspect_before != suspect_after:
            raise RuntimeError("SUSPECT record count changed!")

        if ground_truth_before != ground_truth_after:
            raise RuntimeError("Ground truth count changed!")

        conn.commit()

        print("\nLEVEL TELEMETRY CORRECTION COMPLETE")
        print("-----------------------------------")
        print("Active LEVEL sensors:", len(sensors))
        print("Updated GOOD readings:", updated_records)
        print("Total telemetry:", total_after)
        print("SUSPECT records preserved:", suspect_after)
        print("Ground truth preserved:", ground_truth_after)
        print("RESULT: PASSED")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    fix_level_telemetry()
