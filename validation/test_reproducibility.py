import sqlite3
import hashlib
import tempfile
import random
from pathlib import Path

from generators import master_data, telemetry, fault_injection

PROJECT = Path(__file__).resolve().parents[1]
SCHEMA = PROJECT / "database" / "schema.sql"

SEED = 20261022
TOTAL_RECORDS = 100_000

TABLES = [
    "facilities",
    "network_nodes",
    "pumps",
    "tanks",
    "valves",
    "pipes",
    "sensors",
    "operating_modes",
    "telemetry",
    "ground_truth",
]

# Audit timestamps are intentionally excluded from
# reproducibility comparison.
IGNORED_COLUMNS = {"created_at", "updated_at"}


def create_test_database(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.close()


def generate_dataset(db_path):
    create_test_database(db_path)

    master_data.DB_PATH = db_path
    telemetry.DB_PATH = db_path
    fault_injection.DB_PATH = db_path

    master_data.rng = random.Random(SEED)
    telemetry.random.seed(SEED)
    fault_injection.rng = random.Random(SEED)

    telemetry.TOTAL_RECORDS = TOTAL_RECORDS

    master_data.generate_master_data()
    telemetry.generate_telemetry()
    fault_injection.generate_faults()

    return calculate_checksums(db_path)


def calculate_checksums(db_path):
    conn = sqlite3.connect(db_path)
    results = {}

    for table in TABLES:
        columns = [
            row[1]
            for row in conn.execute(
                f'PRAGMA table_info("{table}")'
            ).fetchall()
            if row[1] not in IGNORED_COLUMNS
        ]

        column_sql = ", ".join(
            f'"{column}"' for column in columns
        )

        rows = conn.execute(
            f'SELECT {column_sql} FROM "{table}" ORDER BY rowid'
        ).fetchall()

        payload = repr(rows).encode("utf-8")

        results[table] = {
            "rows": len(rows),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }

    violations = conn.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    conn.close()

    if violations:
        raise RuntimeError(
            f"Foreign-key violations found: {violations}"
        )

    return results


def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)

        print("========== GENERATION RUN A ==========")
        result_a = generate_dataset(root / "run_a.db")

        print("\n========== GENERATION RUN B ==========")
        result_b = generate_dataset(root / "run_b.db")

        print("\n========== CHECKSUM COMPARISON ==========")

        all_match = True

        for table in TABLES:
            a = result_a[table]
            b = result_b[table]

            same = (
                a["rows"] == b["rows"]
                and a["sha256"] == b["sha256"]
            )

            print(
                f"{table}: "
                f"A={a['rows']}, B={b['rows']}, "
                f"{'MATCH' if same else 'MISMATCH'}"
            )

            if not same:
                all_match = False

        print("\n========== FINAL RESULT ==========")
        print(
            "REPRODUCIBILITY PASSED"
            if all_match
            else "REPRODUCIBILITY FAILED"
        )

        if not all_match:
            raise SystemExit(1)


if __name__ == "__main__":
    main()