
import sqlite3
import statistics
from collections import defaultdict

DB_PATH = "data/industrial_monitoring.db"

# A 30% change from the normal baseline is suspicious.
THRESHOLD = 0.30

def detect_anomalies():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            t.telemetry_id,
            t.sensor_id,
            t.timestamp,
            t.reading,
            s.sensor_type
        FROM telemetry t
        JOIN sensors s
            ON t.sensor_id = s.sensor_id
        ORDER BY t.sensor_id, t.timestamp
    """)

    records = cursor.fetchall()
    conn.close()

    # Separate normal historical readings from injected faults.
    normal_data = defaultdict(list)
    all_data = defaultdict(list)

    for row in records:
        telemetry_id, sensor_id, timestamp, reading, sensor_type = row

        all_data[sensor_id].append(row)

        if timestamp < "2026-10-03":
            normal_data[sensor_id].append(reading)

    # Calculate baseline for each sensor.
    baselines = {}

    for sensor_id, values in normal_data.items():
        if values:
            baselines[sensor_id] = statistics.median(values)

    anomalies = []

    for sensor_id, readings in all_data.items():

        baseline = baselines.get(sensor_id)

        if baseline is None or baseline == 0:
            continue

        for row in readings:

            telemetry_id, _, timestamp, reading, sensor_type = row

            # Only evaluate injected-period readings.
            if timestamp < "2026-10-03":
                continue

            deviation = abs(reading - baseline) / abs(baseline)

            if deviation >= THRESHOLD:
                anomalies.append({
                    "telemetry_id": telemetry_id,
                    "sensor_id": sensor_id,
                    "reading": reading,
                    "baseline": round(baseline, 2),
                    "deviation_percent": round(deviation * 100, 2),
                    "reason": "Significant deviation from baseline"
                })

    print("\n========== BASELINE DETECTION ==========")
    print("Total telemetry records:", len(records))
    print("Sensors with baselines:", len(baselines))
    print("Detected anomalies:", len(anomalies))

    return anomalies


if __name__ == "__main__":
    detect_anomalies()
