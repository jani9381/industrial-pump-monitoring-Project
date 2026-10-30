import sqlite3
from database.db import DB_PATH

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

checks = {
    "Sensor/equipment facility mismatch": """
        SELECT COUNT(*)
        FROM sensors s
        LEFT JOIN pumps p ON s.pump_id = p.pump_id
        LEFT JOIN tanks t ON s.tank_id = t.tank_id
        LEFT JOIN valves v ON s.valve_id = v.valve_id
        LEFT JOIN pipes pi ON s.pipe_id = pi.pipe_id
        WHERE
            (s.pump_id IS NOT NULL AND s.facility_id != p.facility_id)
            OR (s.tank_id IS NOT NULL AND s.facility_id != t.facility_id)
            OR (s.valve_id IS NOT NULL AND s.facility_id != v.facility_id)
            OR (s.pipe_id IS NOT NULL AND s.facility_id != pi.facility_id)
    """,

    "Alarm/sensor facility mismatch": """
        SELECT COUNT(*)
        FROM alarms a
        JOIN sensors s ON a.sensor_id = s.sensor_id
        WHERE a.facility_id != s.facility_id
    """,

    "Ground-truth telemetry/sensor mismatch": """
        SELECT COUNT(*)
        FROM ground_truth g
        JOIN telemetry t ON g.telemetry_id = t.telemetry_id
        WHERE g.sensor_id IS NOT NULL
          AND g.sensor_id != t.sensor_id
    """,

    "Equipment event type mismatch": """
        SELECT COUNT(*)
        FROM equipment_state_events
        WHERE
            (equipment_type = 'PUMP' AND pump_id IS NULL)
            OR (equipment_type = 'TANK' AND tank_id IS NULL)
            OR (equipment_type = 'VALVE' AND valve_id IS NULL)
            OR (equipment_type = 'PIPE' AND pipe_id IS NULL)
            OR (equipment_type != 'PUMP' AND pump_id IS NOT NULL)
            OR (equipment_type != 'TANK' AND tank_id IS NOT NULL)
            OR (equipment_type != 'VALVE' AND valve_id IS NOT NULL)
            OR (equipment_type != 'PIPE' AND pipe_id IS NOT NULL)
    """,

    "Telemetry without a sensor": """
        SELECT COUNT(*)
        FROM telemetry t
        LEFT JOIN sensors s ON t.sensor_id = s.sensor_id
        WHERE s.sensor_id IS NULL
    """,

    "Simulation inputs without a simulation": """
        SELECT COUNT(*)
        FROM simulation_inputs i
        LEFT JOIN simulation_runs r
            ON i.simulation_id = r.simulation_id
        WHERE r.simulation_id IS NULL
    """
}

print("========== RELATIONSHIP VALIDATION ==========")

failed = False

for name, query in checks.items():
    count = conn.execute(query).fetchone()[0]
    status = "PASS" if count == 0 else "FAIL"

    print(f"{name}: {count} [{status}]")

    if count:
        failed = True

print("\n========== FOREIGN KEY VALIDATION ==========")

violations = conn.execute("PRAGMA foreign_key_check").fetchall()
print("Foreign-key violations:", len(violations))

if violations:
    failed = True

conn.close()

print("\nFINAL RESULT:", "FAILED" if failed else "PASSED")
