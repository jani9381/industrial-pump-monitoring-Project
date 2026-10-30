import sqlite3

DB_PATH = "data/industrial_monitoring.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("\n========== FAULT DATA VALIDATION ==========\n")

# 1. Count scenarios
cursor.execute("""
    SELECT issue_type, COUNT(DISTINCT scenario_id), COUNT(*)
    FROM ground_truth
    GROUP BY issue_type
""")

print("Fault distribution:")
for row in cursor.fetchall():
    print(
        f"{row[0]}: "
        f"{row[1]} scenarios, "
        f"{row[2]} ground-truth records"
    )

# 2. Check fault telemetry
cursor.execute("""
    SELECT COUNT(*)
    FROM ground_truth gt
    JOIN telemetry t
        ON gt.telemetry_id = t.telemetry_id
    WHERE gt.expected_label = 'ANOMALY'
""")

print("\nAnomaly telemetry records:", cursor.fetchone()[0])

# 3. Check missing telemetry references
cursor.execute("""
    SELECT COUNT(*)
    FROM ground_truth gt
    LEFT JOIN telemetry t
        ON gt.telemetry_id = t.telemetry_id
    WHERE t.telemetry_id IS NULL
""")

print("Missing telemetry references:", cursor.fetchone()[0])

# 4. Check duplicate ground-truth labels
cursor.execute("""
    SELECT COUNT(*)
    FROM (
        SELECT telemetry_id
        FROM ground_truth
        GROUP BY telemetry_id
        HAVING COUNT(*) > 1
    )
""")

print("Duplicate telemetry labels:", cursor.fetchone()[0])

conn.close()