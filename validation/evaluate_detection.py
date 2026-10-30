
import sqlite3
import statistics
from collections import defaultdict
from pathlib import Path

DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "industrial_monitoring.db"
)

THRESHOLD = 0.30
FAULT_START_DATE = "2026-10-03"

def evaluate_detection():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                telemetry_id,
                sensor_id,
                timestamp,
                reading,
                quality_status
            FROM telemetry
            ORDER BY sensor_id, timestamp
        """)

        records = cursor.fetchall()

        cursor.execute("""
            SELECT telemetry_id
            FROM ground_truth
            WHERE expected_label = 'ANOMALY'
        """)

        actual_anomalies = {
            row[0] for row in cursor.fetchall()
        }

    finally:
        conn.close()

    # Build normal operating baselines
    normal_data = defaultdict(list)

    for telemetry_id, sensor_id, timestamp, reading, quality in records:
        if timestamp < FAULT_START_DATE and quality == "GOOD":
            normal_data[sensor_id].append(reading)

    baselines = {
        sensor_id: statistics.median(values)
        for sensor_id, values in normal_data.items()
        if values
    }

    # Detect anomalies after fault start date
    predicted_anomalies = set()

    for telemetry_id, sensor_id, timestamp, reading, quality in records:

        if timestamp < FAULT_START_DATE:
            continue

        baseline = baselines.get(sensor_id)

        if baseline is None or baseline == 0:
            continue

        deviation = abs(reading - baseline) / abs(baseline)

        if deviation >= THRESHOLD:
            predicted_anomalies.add(telemetry_id)

    # Calculate evaluation metrics
    tp = len(actual_anomalies & predicted_anomalies)
    fp = len(predicted_anomalies - actual_anomalies)
    fn = len(actual_anomalies - predicted_anomalies)

    evaluation_records = {
        row[0] for row in records
        if row[2] >= FAULT_START_DATE
    }

    tn = len(
        evaluation_records
        - actual_anomalies
        - predicted_anomalies
    )

    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0
    )

    print("\n========== ANOMALY DETECTION EVALUATION ==========")
    print("Total telemetry records:", len(records))
    print("Evaluation records:", len(evaluation_records))
    print("Baseline sensors:", len(baselines))
    print("Actual anomalies:", len(actual_anomalies))
    print("Predicted anomalies:", len(predicted_anomalies))

    print("\nConfusion Matrix")
    print("True Positives:", tp)
    print("False Positives:", fp)
    print("True Negatives:", tn)
    print("False Negatives:", fn)

    print("\nPerformance Metrics")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")

    print("\nThreshold:", THRESHOLD * 100, "%")
    print("RESULT: Evaluation completed")

if __name__ == "__main__":
    evaluate_detection()
