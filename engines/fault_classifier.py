
import sqlite3
import statistics
from collections import defaultdict

DB_PATH = "data/industrial_monitoring.db"
THRESHOLD = 0.30


def classify_faults():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            t.telemetry_id,
            t.sensor_id,
            t.timestamp,
            t.reading,
            s.sensor_type,
            s.pump_id,
            s.pipe_id
        FROM telemetry t
        JOIN sensors s
            ON t.sensor_id = s.sensor_id
        ORDER BY t.sensor_id, t.timestamp
    """)

    records = cursor.fetchall()

    cursor.execute("""
        SELECT sensor_id, AVG(reading)
        FROM telemetry
        WHERE timestamp < '2026-10-03'
        GROUP BY sensor_id
    """)

    baselines = {
        sensor_id: average
        for sensor_id, average in cursor.fetchall()
    }

    # Group readings by sensor
    sensor_data = defaultdict(list)

    for row in records:
        sensor_data[row[1]].append(row)

    classified = []

    for sensor_id, readings in sensor_data.items():

        baseline = baselines.get(sensor_id)

        if baseline is None or baseline == 0:
            continue

        for row in readings:

            telemetry_id, _, timestamp, reading, sensor_type, pump_id, pipe_id = row

            if timestamp < "2026-10-03":
                continue

            deviation = abs(reading - baseline) / abs(baseline)

            if deviation < THRESHOLD:
                continue

            # Initial classification based on sensor mapping
            if pipe_id:
                fault_type = "PIPELINE_FLOW_ANOMALY"

            elif pump_id and sensor_type == "FLOW":
                fault_type = "PUMP_FLOW_ANOMALY"

            elif pump_id and sensor_type == "PRESSURE":
                fault_type = "PUMP_PRESSURE_ANOMALY"

            else:
                fault_type = "SENSOR_ANOMALY"

            classified.append({
                "telemetry_id": telemetry_id,
                "sensor_id": sensor_id,
                "fault_type": fault_type,
                "reading": reading,
                "baseline": round(baseline, 2),
                "deviation_percent": round(deviation * 100, 2)
            })

    conn.close()

    print("\n========== FAULT CLASSIFICATION ==========")
    print("Total classified records:", len(classified))

    counts = defaultdict(int)

    for item in classified:
        counts[item["fault_type"]] += 1

    for fault_type, count in sorted(counts.items()):
        print(f"{fault_type}: {count}")

    return classified


if __name__ == "__main__":
    classify_faults()
