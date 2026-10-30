import sqlite3
import random
from pathlib import Path

# -----------------------------------
# PROJECT CONFIGURATION
# -----------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "data" / "industrial_monitoring.db"

SEED = 20261022
rng = random.Random(SEED)


def generate_master_data():

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        cursor = connection.cursor()

        # Prevent accidental duplicate generation
        tables = [
            "facilities",
            "network_nodes",
            "pumps",
            "tanks",
            "valves",
            "pipes",
            "sensors",
            "operating_modes"
        ]

        for table in tables:
            count = cursor.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            if count > 0:
                raise ValueError(
                    f"{table} already contains data. "
                    "Generator stopped to prevent duplicates."
                )

        # -----------------------------------
        # STEP 1: GENERATE FACILITIES
        # -----------------------------------

        facilities = [
            ("FAC-001", "North Water Treatment Plant", "Hyderabad"),
            ("FAC-002", "Central Water Processing Plant", "Mumbai"),
            ("FAC-003", "South Water Distribution Plant", "Chennai")
        ]

        cursor.executemany("""
            INSERT INTO facilities
            (facility_id, facility_name, location, status)
            VALUES (?, ?, ?, 'ACTIVE')
        """, facilities)

        print("3 facilities generated.")

        # -----------------------------------
        # STEP 2: DISTRIBUTE EQUIPMENT
        # -----------------------------------

        distribution = {
            "FAC-001": {"pumps": 7, "tanks": 10, "valves": 20},
            "FAC-002": {"pumps": 7, "tanks": 10, "valves": 20},
            "FAC-003": {"pumps": 6, "tanks": 10, "valves": 20}
        }

        node_counter = 1
        pump_counter = 1
        tank_counter = 1
        valve_counter = 1

        all_nodes = {
            facility_id: []
            for facility_id in distribution
        }

        # -----------------------------------
        # STEP 3: CREATE PUMPS
        # -----------------------------------

        for facility_id, counts in distribution.items():

            for _ in range(counts["pumps"]):

                pump_id = f"PUMP-{pump_counter:03d}"
                node_id = f"NODE-{node_counter:03d}"

                cursor.execute("""
                    INSERT INTO network_nodes
                    (node_id, facility_id, node_name, node_type)
                    VALUES (?, ?, ?, 'PUMP')
                """, (
                    node_id,
                    facility_id,
                    pump_id
                ))

                nominal_flow = round(
                    rng.uniform(80, 150), 2
                )

                nominal_pressure = round(
                    rng.uniform(3, 8), 2
                )

                cursor.execute("""
                    INSERT INTO pumps
                    (
                        pump_id,
                        facility_id,
                        node_id,
                        pump_name,
                        nominal_flow,
                        nominal_pressure,
                        nominal_speed,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 100, 'ACTIVE')
                """, (
                    pump_id,
                    facility_id,
                    node_id,
                    f"Industrial Pump {pump_counter}",
                    nominal_flow,
                    nominal_pressure
                ))

                all_nodes[facility_id].append(node_id)

                pump_counter += 1
                node_counter += 1

        print("20 pumps generated.")

        # -----------------------------------
        # STEP 4: CREATE TANKS
        # -----------------------------------

        for facility_id, counts in distribution.items():

            for _ in range(counts["tanks"]):

                tank_id = f"TANK-{tank_counter:03d}"
                node_id = f"NODE-{node_counter:03d}"

                capacity = round(
                    rng.uniform(5000, 20000), 2
                )

                level = round(
                    capacity * rng.uniform(0.25, 0.80), 2
                )

                cursor.execute("""
                    INSERT INTO network_nodes
                    (node_id, facility_id, node_name, node_type)
                    VALUES (?, ?, ?, 'TANK')
                """, (
                    node_id,
                    facility_id,
                    tank_id
                ))

                cursor.execute("""
                    INSERT INTO tanks
                    (
                        tank_id,
                        facility_id,
                        node_id,
                        tank_name,
                        capacity_liters,
                        current_level,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE')
                """, (
                    tank_id,
                    facility_id,
                    node_id,
                    f"Storage Tank {tank_counter}",
                    capacity,
                    level
                ))

                all_nodes[facility_id].append(node_id)

                tank_counter += 1
                node_counter += 1

        print("30 tanks generated.")

        # -----------------------------------
        # STEP 5: CREATE VALVES
        # -----------------------------------

        for facility_id, counts in distribution.items():

            for _ in range(counts["valves"]):

                valve_id = f"VALVE-{valve_counter:03d}"
                node_id = f"NODE-{node_counter:03d}"

                cursor.execute("""
                    INSERT INTO network_nodes
                    (node_id, facility_id, node_name, node_type)
                    VALUES (?, ?, ?, 'VALVE')
                """, (
                    node_id,
                    facility_id,
                    valve_id
                ))

                cursor.execute("""
                    INSERT INTO valves
                    (
                        valve_id,
                        facility_id,
                        node_id,
                        valve_name,
                        opening_percentage,
                        valve_state
                    )
                    VALUES (?, ?, ?, ?, 100, 'OPEN')
                """, (
                    valve_id,
                    facility_id,
                    node_id,
                    f"Control Valve {valve_counter}"
                ))

                all_nodes[facility_id].append(node_id)

                valve_counter += 1
                node_counter += 1

        print("60 valves generated.")

        # -----------------------------------
        # STEP 6: CREATE CONNECTED PIPES
        # -----------------------------------

        pipe_counter = 1

        for facility_id, nodes in all_nodes.items():

            # Connect consecutive equipment nodes.
            # This creates a connected network per facility.

            for index in range(len(nodes) - 1):

                pipe_id = f"PIPE-{pipe_counter:03d}"

                source_node = nodes[index]
                target_node = nodes[index + 1]

                length = round(
                    rng.uniform(10, 300), 2
                )

                diameter = round(
                    rng.uniform(50, 200), 2
                )

                cursor.execute("""
                    INSERT INTO pipes
                    (
                        pipe_id,
                        facility_id,
                        source_node_id,
                        target_node_id,
                        length_meters,
                        diameter_mm,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE')
                """, (
                    pipe_id,
                    facility_id,
                    source_node,
                    target_node,
                    length,
                    diameter
                ))

                pipe_counter += 1

        print(f"{pipe_counter - 1} connected pipes generated.")

        # -----------------------------------
        # STEP 7: CREATE SENSORS
        # -----------------------------------

        sensor_counter = 1

        # Pump flow and pressure sensors
        for row in cursor.execute(
            "SELECT pump_id, facility_id FROM pumps"
        ).fetchall():

            pump_id, facility_id = row

            for sensor_type, unit, min_val, max_val in [
                ("FLOW", "L/min", 0, 250),
                ("PRESSURE", "bar", 0, 20)
            ]:

                sensor_id = f"SNS-{sensor_counter:03d}"

                cursor.execute("""
                    INSERT INTO sensors
                    (
                        sensor_id,
                        facility_id,
                        sensor_name,
                        sensor_type,
                        unit,
                        pump_id,
                        min_value,
                        max_value
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sensor_id,
                    facility_id,
                    f"{sensor_type} Sensor {sensor_counter}",
                    sensor_type,
                    unit,
                    pump_id,
                    min_val,
                    max_val
                ))

                sensor_counter += 1

        # Tank level sensors
        for row in cursor.execute(
            "SELECT tank_id, facility_id FROM tanks"
        ).fetchall():

            tank_id, facility_id = row

            sensor_id = f"SNS-{sensor_counter:03d}"

            cursor.execute("""
                INSERT INTO sensors
                (
                    sensor_id,
                    facility_id,
                    sensor_name,
                    sensor_type,
                    unit,
                    tank_id,
                    min_value,
                    max_value
                )
                VALUES (?, ?, ?, 'LEVEL', '%', ?, 0, 100)
            """, (
                sensor_id,
                facility_id,
                f"Tank Level Sensor {sensor_counter}",
                tank_id
            ))

            sensor_counter += 1

        # Pipe flow sensors
        for row in cursor.execute(
            "SELECT pipe_id, facility_id FROM pipes"
        ).fetchall():

            pipe_id, facility_id = row

            sensor_id = f"SNS-{sensor_counter:03d}"

            cursor.execute("""
                INSERT INTO sensors
                (
                    sensor_id,
                    facility_id,
                    sensor_name,
                    sensor_type,
                    unit,
                    pipe_id,
                    min_value,
                    max_value
                )
                VALUES (?, ?, ?, 'FLOW', 'L/min', ?, 0, 250)
            """, (
                sensor_id,
                facility_id,
                f"Pipe Flow Sensor {sensor_counter}",
                pipe_id
            ))

            sensor_counter += 1

        print(f"{sensor_counter - 1} sensors generated.")

        # -----------------------------------
        # STEP 8: CREATE OPERATING MODES
        # -----------------------------------

        modes = [
            (
                "MODE-001",
                "FAC-001",
                "NORMAL",
                "Normal water processing operation",
                "2026-01-01"
            ),
            (
                "MODE-002",
                "FAC-002",
                "NORMAL",
                "Normal water processing operation",
                "2026-01-01"
            ),
            (
                "MODE-003",
                "FAC-003",
                "NORMAL",
                "Normal water processing operation",
                "2026-01-01"
            )
        ]

        cursor.executemany("""
            INSERT INTO operating_modes
            (
                mode_id,
                facility_id,
                mode_name,
                description,
                effective_from
            )
            VALUES (?, ?, ?, ?, ?)
        """, modes)

        print("3 operating modes generated.")

        # -----------------------------------
        # STEP 9: COMMIT
        # -----------------------------------

        connection.commit()

        print("\nMASTER DATA GENERATION COMPLETED!")

        for table in [
            "facilities",
            "pumps",
            "tanks",
            "valves",
            "pipes",
            "sensors",
            "network_nodes",
            "operating_modes"
        ]:

            count = cursor.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            print(f"{table}: {count}")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    generate_master_data()