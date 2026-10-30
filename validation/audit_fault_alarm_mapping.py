import sqlite3

conn = sqlite3.connect("data/industrial_monitoring.db")
conn.row_factory = sqlite3.Row

print("========== GROUND TRUTH TO ALARM CLASSIFICATION ==========")

rows = conn.execute("""
    SELECT
        g.issue_type,
        a.alarm_type,
        COUNT(DISTINCT g.sensor_id) AS affected_sensors,
        COUNT(DISTINCT a.alarm_id) AS alarm_records
    FROM ground_truth g
    JOIN alarms a
        ON a.sensor_id = g.sensor_id
    GROUP BY g.issue_type, a.alarm_type
    ORDER BY g.issue_type, a.alarm_type
""").fetchall()

for row in rows:
    print(dict(row))

print("\n========== SENSOR-LEVEL MAPPING ==========")

rows = conn.execute("""
    SELECT DISTINCT
        g.issue_type,
        g.sensor_id,
        a.alarm_type
    FROM ground_truth g
    JOIN alarms a
        ON a.sensor_id = g.sensor_id
    ORDER BY g.issue_type, g.sensor_id, a.alarm_type
""").fetchall()

for row in rows:
    print(dict(row))

conn.close()
print("\nAUDIT COMPLETE")
