
import sqlite3
import random
from pathlib import Path
from datetime import datetime, timedelta

# ----------------------------------
# CONFIGURATION
# ----------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "industrial_monitoring.db"

SEED = 20261022
rng = random.Random(SEED)

# Four scenarios, five equipment targets each
TARGETS_PER_SCENARIO = 5

# Preserve baseline data; create separate scenario records
SCENARIO_START = datetime(2026, 10, 3, 0, 0, 0)
READINGS_PER_SCENARIO = 12
INTERVAL_MINUTES = 5


def generate_faults():

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    try:

        # ----------------------------------
        # CHECK EXISTING SCENARIOS
        # ----------------------------------

        existing = cursor.execute("""
            SELECT COUNT(*)
            FROM ground_truth
            WHERE scenario_id LIKE 'FAULT-%'
        """).fetchone()[0]

        if existing:
            raise RuntimeError(
                "Fault scenarios already exist. "
                "Stopping to prevent duplicate injection."
            )

        # ----------------------------------
        # LOAD VALID EQUIPMENT
        # ----------------------------------

        pumps = cursor.execute("""
            SELECT pump_id, facility_id,
                   nominal_flow, nominal_pressure
            FROM pumps
            ORDER BY pump_id
        """).fetchall()

        pipes = cursor.execute("""
            SELECT p.pipe_id, p.facility_id,
                   p.source_node_id, p.target_node_id,
                   s.sensor_id
            FROM pipes p
            JOIN sensors s ON s.pipe_id = p.pipe_id
            WHERE s.sensor_type = 'FLOW'
            ORDER BY p.pipe_id
        """).fetchall()

        tank_sensors = cursor.execute("""
            SELECT s.sensor_id, s.facility_id, s.tank_id
            FROM sensors s
            WHERE s.sensor_type = 'LEVEL'
            ORDER BY s.sensor_id
        """).fetchall()

        pump_sensors = cursor.execute("""
            SELECT s.sensor_id, s.facility_id,
                   s.pump_id, s.sensor_type
            FROM sensors s
            WHERE s.pump_id IS NOT NULL
            ORDER BY s.sensor_id
        """).fetchall()

        if len(pipes) < TARGETS_PER_SCENARIO:
            raise RuntimeError("Insufficient pipe sensors")

        if len(pumps) < TARGETS_PER_SCENARIO:
            raise RuntimeError("Insufficient pumps")

        # ----------------------------------
        # SELECT TARGETS DETERMINISTICALLY
        # ----------------------------------

        selected_pipes = rng.sample(
            pipes, TARGETS_PER_SCENARIO
        )

        selected_pumps = rng.sample(
            pumps, TARGETS_PER_SCENARIO
        )

        selected_sensor_faults = rng.sample(
            pump_sensors + tank_sensors,
            TARGETS_PER_SCENARIO
        )

        selected_blockage_pipes = rng.sample(
            [p for p in pipes if p not in selected_pipes],
            TARGETS_PER_SCENARIO
        )

        scenario_counter = 1
        telemetry_inserted = 0
        truth_inserted = 0

        # ----------------------------------
        # HELPER: INJECT SCENARIO
        # ----------------------------------

        def inject_scenario(
            issue_type,
            facility_id,
            sensor_id,
            baseline,
            multiplier,
            description,
            scenario_id
        ):

            nonlocal telemetry_inserted
            nonlocal truth_inserted

            for index in range(READINGS_PER_SCENARIO):

                timestamp = (
                    SCENARIO_START
                    + timedelta(
                        minutes=INTERVAL_MINUTES * index
                    )
                    + timedelta(seconds=scenario_counter)
                )

                # Controlled fault with small variation
                value = baseline * multiplier

                value *= rng.uniform(0.97, 1.03)

                value = round(max(0, value), 3)

                # Store the anomalous telemetry
                cursor.execute("""
                    INSERT INTO telemetry
                    (
                        sensor_id,
                        timestamp,
                        reading,
                        quality_status
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    sensor_id,
                    timestamp.isoformat(timespec="seconds"),
                    value,
                    "SUSPECT"
                ))

                telemetry_id = cursor.lastrowid

                # Ground truth derives from the
                # documented scenario injection rule.
                cursor.execute("""
                    INSERT INTO ground_truth
                    (
                        telemetry_id,
                        sensor_id,
                        issue_type,
                        expected_label,
                        scenario_id,
                        description
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    telemetry_id,
                    sensor_id,
                    issue_type,
                    "ANOMALY",
                    scenario_id,
                    description
                ))

                telemetry_inserted += 1
                truth_inserted += 1

        # ----------------------------------
        # SCENARIO 1: WATER LEAK
        # ----------------------------------

        print("Injecting leak scenarios...")

        for pipe in selected_pipes:

            pipe_id, facility_id, source, target, sensor_id = pipe

            scenario_id = f"FAULT-{scenario_counter:03d}"

            inject_scenario(
                "LEAK",
                facility_id,
                sensor_id,
                120.0,
                0.55,
                f"Simulated leak on {pipe_id}: "
                "pipe flow reduced by approximately 45%.",
                scenario_id
            )

            scenario_counter += 1

        # ----------------------------------
        # SCENARIO 2: PIPE BLOCKAGE
        # ----------------------------------

        print("Injecting blockage scenarios...")

        for pipe in selected_blockage_pipes:

            pipe_id, facility_id, source, target, sensor_id = pipe

            scenario_id = f"FAULT-{scenario_counter:03d}"

            inject_scenario(
                "BLOCKAGE",
                facility_id,
                sensor_id,
                120.0,
                0.40,
                f"Simulated blockage on {pipe_id}: "
                "flow reduced by approximately 60%.",
                scenario_id
            )

            scenario_counter += 1

        # ----------------------------------
        # SCENARIO 3: PUMP DEGRADATION
        # ----------------------------------

        print("Injecting pump degradation scenarios...")

        for pump in selected_pumps:

            pump_id, facility_id, nominal_flow, nominal_pressure = pump

            flow_sensor = cursor.execute("""
                SELECT sensor_id
                FROM sensors
                WHERE pump_id = ?
                  AND sensor_type = 'FLOW'
            """, (pump_id,)).fetchone()

            if not flow_sensor:
                continue

            scenario_id = f"FAULT-{scenario_counter:03d}"

            inject_scenario(
                "PUMP_DEGRADATION",
                facility_id,
                flow_sensor[0],
                nominal_flow,
                0.60,
                f"Pump {pump_id} degradation: "
                "flow reduced by approximately 40%. "
                f"Nominal pressure: {nominal_pressure} bar.",
                scenario_id
            )

            scenario_counter += 1

        # ----------------------------------
        # SCENARIO 4: SENSOR FAULT
        # ----------------------------------

        print("Injecting sensor faults...")

        for sensor in selected_sensor_faults:

            sensor_id, facility_id, equipment_id = (
                sensor[0], sensor[1],
                sensor[2] if sensor[2] else sensor[0]
            )

            sensor_info = cursor.execute("""
                SELECT sensor_type, min_value, max_value
                FROM sensors
                WHERE sensor_id = ?
            """, (sensor_id,)).fetchone()

            sensor_type, min_value, max_value = sensor_info

            baseline = (
                float(min_value) + float(max_value)
            ) / 2

            scenario_id = f"FAULT-{scenario_counter:03d}"

            inject_scenario(
                "SENSOR_FAULT",
                facility_id,
                sensor_id,
                baseline,
                1.0,
                f"Sensor fault on {sensor_id}: "
                "simulated stuck reading.",
                scenario_id
            )

            scenario_counter += 1

        # ----------------------------------
        # COMMIT TRANSACTION
        # ----------------------------------

        conn.commit()

        print("\n================================")
        print("FAULT INJECTION COMPLETED")
        print("================================")

        print("Scenarios created:", scenario_counter - 1)
        print("Fault telemetry:", telemetry_inserted)
        print("Ground truth records:", truth_inserted)

        print("\nFault distribution:")

        results = cursor.execute("""
            SELECT issue_type, COUNT(*)
            FROM ground_truth
            WHERE scenario_id LIKE 'FAULT-%'
            GROUP BY issue_type
            ORDER BY issue_type
        """).fetchall()

        for issue_type, count in results:
            print(issue_type, count)

        print("\nDatabase integrity:")

        violations = cursor.execute("""
            PRAGMA foreign_key_check
        """).fetchall()

        print("Foreign key violations:", len(violations))

        if violations:
            raise RuntimeError("Foreign key validation failed")

        print("RESULT: PASSED")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    generate_faults()
