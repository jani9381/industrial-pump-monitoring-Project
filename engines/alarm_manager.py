import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

from fault_classifier import classify_faults

DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "industrial_monitoring.db"
)


def generate_alarms():

    classified = classify_faults()

    # Group records by sensor and fault type
    grouped_faults = defaultdict(list)

    for item in classified:
        key = (item["sensor_id"], item["fault_type"])
        grouped_faults[key].append(item)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    created = 0
    updated = 0

    try:
        for (sensor_id, fault_type), items in grouped_faults.items():

            # Records are ordered by timestamp by the classifier.
            latest = items[-1]

            reading = latest["reading"]
            baseline = latest["baseline"]
            latest_deviation = latest["deviation_percent"]

            # Use the highest deviation in this group for severity.
            peak_deviation = max(
                item["deviation_percent"] for item in items
            )

            severity = (
                "CRITICAL" if peak_deviation >= 70
                else "HIGH" if peak_deviation >= 50
                else "MEDIUM"
            )

            cursor.execute("""
                SELECT facility_id
                FROM sensors
                WHERE sensor_id = ?
            """, (sensor_id,))

            result = cursor.fetchone()

            if not result:
                continue

            facility_id = result[0]

            description = (
                f"{fault_type}: sensor {sensor_id}. "
                f"Latest reading: {reading:.2f}. "
                f"Baseline: {baseline:.2f}. "
                f"Latest deviation: {latest_deviation:.2f}%. "
                f"Peak deviation in analysis: {peak_deviation:.2f}%. "
                f"Matching telemetry records: {len(items)}."
            )

            # Find an existing active alarm.
            # Prefer ACKNOWLEDGED so its status is preserved.
            cursor.execute("""
                SELECT alarm_id
                FROM alarms
                WHERE sensor_id = ?
                  AND alarm_type = ?
                  AND status IN ('OPEN', 'ACKNOWLEDGED')
                ORDER BY
                    CASE
                        WHEN status = 'ACKNOWLEDGED' THEN 0
                        ELSE 1
                    END,
                    detected_at DESC
                LIMIT 1
            """, (sensor_id, fault_type))

            existing_alarm = cursor.fetchone()

            if existing_alarm:

                # Update the existing active alarm.
                # Do not change its status or alarm ID.
                alarm_id = existing_alarm[0]

                cursor.execute("""
                    UPDATE alarms
                    SET severity = ?,
                        description = ?
                    WHERE alarm_id = ?
                """, (
                    severity,
                    description,
                    alarm_id
                ))

                updated += 1

            else:

                # No active alarm exists. Create a new one.
                alarm_id = f"ALARM-{latest['telemetry_id']}"

                cursor.execute("""
                    INSERT OR IGNORE INTO alarms (
                        alarm_id,
                        facility_id,
                        sensor_id,
                        alarm_type,
                        severity,
                        description,
                        detected_at,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN')
                """, (
                    alarm_id,
                    facility_id,
                    sensor_id,
                    fault_type,
                    severity,
                    description,
                    datetime.now(timezone.utc).isoformat()
                ))

                if cursor.rowcount > 0:
                    created += 1

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    print("\n========== OPTIMIZED ALARM GENERATION ==========")
    print("Unique sensor/fault groups:", len(grouped_faults))
    print("New alarms created:", created)
    print("Existing alarms updated:", updated)
    print("Total groups processed:", created + updated)


if __name__ == "__main__":
    generate_alarms()