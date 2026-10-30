import sqlite3
import tempfile
from pathlib import Path

from generators import master_data, telemetry, fault_injection

PROJECT = Path(__file__).resolve().parents[1]
SCHEMA = PROJECT / "database" / "schema.sql"

def create_db(path):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.close()

def generate(path):
    create_db(path)
    master_data.DB_PATH = path
    telemetry.DB_PATH = path
    fault_injection.DB_PATH = path

    import random
    master_data.rng = random.Random(20261022)
    telemetry.random.seed(20261022)
    fault_injection.rng = random.Random(20261022)

    telemetry.TOTAL_RECORDS = 100000

    master_data.generate_master_data()
    telemetry.generate_telemetry()
    fault_injection.generate_faults()

def inspect_table(db_a, db_b, table):
    a = sqlite3.connect(db_a)
    b = sqlite3.connect(db_b)

    columns = [
        row[1] for row in a.execute(
            f'PRAGMA table_info("{table}")'
        ).fetchall()
    ]

    rows_a = a.execute(
        f'SELECT * FROM "{table}" ORDER BY rowid'
    ).fetchall()

    rows_b = b.execute(
        f'SELECT * FROM "{table}" ORDER BY rowid'
    ).fetchall()

    print(f"\n========== {table} ==========")

    differences = 0

    for index, (row_a, row_b) in enumerate(zip(rows_a, rows_b)):
        for col, value_a, value_b in zip(columns, row_a, row_b):
            if value_a != value_b:
                print(f"Row {index + 1}, column {col}:")
                print(f"  Run A: {value_a}")
                print(f"  Run B: {value_b}")
                differences += 1

                if differences >= 10:
                    print("Showing first 10 differences only.")
                    break

        if differences >= 10:
            break

    if differences == 0 and len(rows_a) == len(rows_b):
        print("No row differences found.")

    a.close()
    b.close()

with tempfile.TemporaryDirectory() as folder:
    root = Path(folder)
    db_a = root / "run_a.db"
    db_b = root / "run_b.db"

    print("Generating isolated Run A...")
    generate(db_a)

    print("\nGenerating isolated Run B...")
    generate(db_b)

    inspect_table(db_a, db_b, "facilities")
    inspect_table(db_a, db_b, "network_nodes")
