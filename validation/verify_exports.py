import csv
import json
import sqlite3
import hashlib
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
EXPORT_DIR = BASE_DIR / "data" / "exports"
MANIFEST_PATH = EXPORT_DIR / "export_manifest.json"


def sha256_file(path):
    digest = hashlib.sha256()

    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def main():
    manifest = json.loads(
        MANIFEST_PATH.read_text(encoding="utf-8")
    )

    print("========== CSV AND JSON VALIDATION ==========")

    expected_total = 0
    all_passed = True

    for table, details in manifest["tables"].items():
        expected = details["records"]
        expected_total += expected

        csv_path = EXPORT_DIR / details["csv_file"]
        json_path = EXPORT_DIR / details["json_file"]

        with open(csv_path, newline="", encoding="utf-8-sig") as file:
            csv_count = sum(1 for _ in csv.reader(file)) - 1

        json_records = json.loads(
            json_path.read_text(encoding="utf-8")
        )
        json_count = len(json_records)

        csv_hash_ok = (
            sha256_file(csv_path) == details["csv_sha256"]
        )
        json_hash_ok = (
            sha256_file(json_path) == details["json_sha256"]
        )

        passed = (
            csv_count == expected
            and json_count == expected
            and csv_hash_ok
            and json_hash_ok
        )

        print(
            f"{table}: expected={expected}, "
            f"CSV={csv_count}, JSON={json_count}, "
            f"{'PASS' if passed else 'FAIL'}"
        )

        if not passed:
            all_passed = False

    print("\n========== SQL RESTORE TEST ==========")

    sql_path = EXPORT_DIR / manifest["sql_file"]

    if sha256_file(sql_path) != manifest["sql_sha256"]:
        raise RuntimeError("SQL dump checksum mismatch")

    with tempfile.TemporaryDirectory() as folder:
        restored_db = Path(folder) / "restored.db"

        conn = sqlite3.connect(restored_db)

        try:
            conn.executescript(
                sql_path.read_text(encoding="utf-8")
            )

            integrity = conn.execute(
                "PRAGMA integrity_check"
            ).fetchone()[0]

            foreign_keys = conn.execute(
                "PRAGMA foreign_key_check"
            ).fetchall()

            for table, details in manifest["tables"].items():
                count = conn.execute(
                    f'SELECT COUNT(*) FROM "{table}"'
                ).fetchone()[0]

                passed = count == details["records"]

                print(
                    f"{table}: restored={count}, "
                    f"expected={details['records']}, "
                    f"{'PASS' if passed else 'FAIL'}"
                )

                if not passed:
                    all_passed = False

            print("SQLite integrity:", integrity)
            print("Foreign-key violations:", len(foreign_keys))

            if integrity != "ok" or foreign_keys:
                all_passed = False

        finally:
            conn.close()

    print("\n========== FINAL EXPORT VALIDATION ==========")
    print("Expected total records:", expected_total)
    print("RESULT:", "PASSED" if all_passed else "FAILED")

    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
