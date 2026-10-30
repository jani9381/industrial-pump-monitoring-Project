import sqlite3
from pathlib import Path

db = Path("data/industrial_monitoring.db")
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row

print("========== ALARMS BY TYPE AND STATUS ==========")

rows = conn.execute("""
    SELECT
        alarm_type,
        status,
        COUNT(*) AS total,
        COUNT(DISTINCT sensor_id) AS unique_sensors
    FROM alarms
    GROUP BY alarm_type, status
    ORDER BY alarm_type, status
""").fetchall()

for row in rows:
    print(dict(row))

print("\n========== GROUND TRUTH VS ALARM TYPES ==========")

rows = conn.execute("""
    SELECT
        g.issue_type,
        COUNT(DISTINCT g.sensor_id) AS affected_sensors,
        COUNT(*) AS ground_truth_records
    FROM ground_truth g
    GROUP BY g.issue_type
    ORDER BY g.issue_type
""").fetchall()

for row in rows:
    print(dict(row))

print("\nAUDIT COMPLETE")

conn.close()
