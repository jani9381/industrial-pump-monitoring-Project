
import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

# --------------------------------------------------
# DATABASE CONFIGURATION
# --------------------------------------------------

DB_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "industrial_monitoring.db"
)

TOTAL_RECORDS = 100_000
RANDOM_SEED = 20261022
INTERVAL_MINUTES = 5
BATCH_SIZE = 5000

random.seed(RANDOM_SEED)


# --------------------------------------------------
# TELEMETRY GENERATION
# --------------------------------------------------

def generate_telemetry():

    print("Starting telemetry generation...")

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    try:

        # --------------------------------------------------
        # FETCH ACTIVE SENSORS
        # --------------------------------------------------

        sensors = cursor.execute("""
            SELECT
                sensor_id,
                sensor_type,
                min_value,
                max_value,
                pump_id,
                tank_id
            FROM sensors
            WHERE status = 'ACTIVE'
            ORDER BY sensor_id
        """).fetchall()

        if not sensors:
            raise RuntimeError(
                "No active sensors found!"
            )

        print("Active sensors:", len(sensors))

        # --------------------------------------------------
        # FETCH PUMP INFORMATION
        # --------------------------------------------------

        pumps = {
            row[0]: {
                "nominal_flow": float(row[1]),
                "nominal_pressure": float(row[2])
            }
            for row in cursor.execute("""
                SELECT
                    pump_id,
                    nominal_flow,
                    nominal_pressure
                FROM pumps
            """).fetchall()
        }

        # --------------------------------------------------
        # FETCH TANK INFORMATION
        # --------------------------------------------------

        tanks = {
            row[0]: {
                "current_level": float(row[1]),
                "capacity_liters": float(row[2])
            }
            for row in cursor.execute("""
                SELECT
                    tank_id,
                    current_level,
                    capacity_liters
                FROM tanks
            """).fetchall()
        }

        start_time = datetime(
            2026, 10, 1, 0, 0, 0
        )

        records = []

        # --------------------------------------------------
        # GENERATE SENSOR READINGS
        # --------------------------------------------------

        for index in range(TOTAL_RECORDS):

            sensor = sensors[index % len(sensors)]

            (
                sensor_id,
                sensor_type,
                min_val,
                max_val,
                pump_id,
                tank_id
            ) = sensor

            min_val = float(min_val)
            max_val = float(max_val)

            if min_val >= max_val:
                raise ValueError(
                    f"Invalid sensor range: {sensor_id}"
                )

            # Default sensor baseline
            midpoint = (min_val + max_val) / 2

            # --------------------------------------------------
            # FLOW SENSOR
            # --------------------------------------------------

            if sensor_type == "FLOW" and pump_id in pumps:

                midpoint = pumps[pump_id]["nominal_flow"]

            # --------------------------------------------------
            # PRESSURE SENSOR
            # --------------------------------------------------

            elif sensor_type == "PRESSURE" and pump_id in pumps:

                midpoint = pumps[pump_id]["nominal_pressure"]

            # --------------------------------------------------
            # LEVEL SENSOR
            # --------------------------------------------------

            elif sensor_type == "LEVEL" and tank_id in tanks:

                tank = tanks[tank_id]

                capacity = tank["capacity_liters"]
                current_level = tank["current_level"]

                if capacity <= 0:
                    raise ValueError(
                        f"Invalid tank capacity: {tank_id}"
                    )

                # Convert litres into percentage
                midpoint = (
                    current_level / capacity
                ) * 100

                # Keep level within physical limits
                midpoint = max(
                    0.0,
                    min(100.0, midpoint)
                )

            # --------------------------------------------------
            # SENSOR VALIDATION
            # --------------------------------------------------

            midpoint = max(
                min_val,
                min(max_val, midpoint)
            )

            # --------------------------------------------------
            # ADD MEASUREMENT NOISE
            # --------------------------------------------------

            noise = random.gauss(
                0,
                (max_val - min_val) * 0.025
            )

            reading = midpoint + noise

            reading = max(
                min_val,
                min(max_val, reading)
            )

            # --------------------------------------------------
            # GENERATE TIMESTAMP
            # --------------------------------------------------

            timestamp = start_time + timedelta(
                minutes=INTERVAL_MINUTES
                * (index // len(sensors))
            )

            records.append((
                sensor_id,
                timestamp.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                round(reading, 3),
                "GOOD"
            ))

        print("Prepared records:", len(records))

        # --------------------------------------------------
        # REPLACE EXISTING TELEMETRY
        # --------------------------------------------------

        print(
            "Warning: Existing telemetry will be replaced."
        )

        cursor.execute("DELETE FROM telemetry")

        # --------------------------------------------------
        # INSERT TELEMETRY IN BATCHES
        # --------------------------------------------------

        for start in range(
            0,
            len(records),
            BATCH_SIZE
        ):

            batch = records[
                start:start + BATCH_SIZE
            ]

            cursor.executemany("""
                INSERT INTO telemetry (
                    sensor_id,
                    timestamp,
                    reading,
                    quality_status
                )
                VALUES (?, ?, ?, ?)
            """, batch)

            print(
                "Inserted:",
                min(start + BATCH_SIZE, len(records))
            )

        # --------------------------------------------------
        # VERIFY RECORD COUNT
        # --------------------------------------------------

        count = cursor.execute("""
            SELECT COUNT(*)
            FROM telemetry
        """).fetchone()[0]

        if count != TOTAL_RECORDS:
            raise RuntimeError(
                f"Record count mismatch! "
                f"Expected {TOTAL_RECORDS}, got {count}"
            )

        conn.commit()

        # --------------------------------------------------
        # GENERATION SUMMARY
        # --------------------------------------------------

        print("\n------------------------------")
        print("TELEMETRY GENERATION COMPLETE")
        print("------------------------------")
        print("Expected records:", TOTAL_RECORDS)
        print("Generated records:", count)
        print("Active sensors:", len(sensors))
        print("Random seed:", RANDOM_SEED)
        print("RESULT: PASSED")

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# --------------------------------------------------
# MAIN EXECUTION
# --------------------------------------------------

if __name__ == "__main__":
    generate_telemetry()
