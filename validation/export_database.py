import csv
import json
import sqlite3
import hashlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "industrial_monitoring.db"
EXPORT_DIR = BASE_DIR / "data" / "exports"


def sha256_file(path):
    digest = hashlib.sha256()

    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def quote_identifier(name):
    return '"' + name.replace('"', '""') + '"'


def export_database():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    manifest = {
        "database": DB_PATH.name,
        "format": ["CSV", "JSON", "SQL"],
        "tables": {},
    }

    try:
        conn.execute("BEGIN")

        tables = conn.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()

        for item in tables:
            table = item["name"]
            quoted_table = quote_identifier(table)

            cursor = conn.execute(
                f"SELECT * FROM {quoted_table} ORDER BY rowid"
            )

            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()

            # CSV export
            csv_path = EXPORT_DIR / f"{table}.csv"

            with open(csv_path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(columns)

                for row in rows:
                    writer.writerow([row[column] for column in columns])

            # JSON export
            json_path = EXPORT_DIR / f"{table}.json"

            records = [
                {column: row[column] for column in columns}
                for row in rows
            ]

            with open(json_path, "w", encoding="utf-8") as file:
                json.dump(
                    records,
                    file,
                    indent=2,
                    ensure_ascii=False,
                    default=str,
                )

            manifest["tables"][table] = {
                "records": len(rows),
                "csv_file": csv_path.name,
                "json_file": json_path.name,
            }

            print(f"{table}: {len(rows)} records exported")

        # Complete SQL database dump
        sql_path = EXPORT_DIR / "industrial_monitoring.sql"

        with open(sql_path, "w", encoding="utf-8") as file:
            for statement in conn.iterdump():
                file.write(statement + "\n")

        conn.commit()

        # Export checksums
        for table, details in manifest["tables"].items():
            for key in ("csv_file", "json_file"):
                path = EXPORT_DIR / details[key]
                details[key.replace("_file", "_sha256")] = sha256_file(path)

        manifest["sql_file"] = sql_path.name
        manifest["sql_sha256"] = sha256_file(sql_path)

        manifest_path = EXPORT_DIR / "export_manifest.json"

        with open(manifest_path, "w", encoding="utf-8") as file:
            json.dump(manifest, file, indent=2)

        print("\n========== EXPORT COMPLETED ==========")
        print("Tables exported:", len(manifest["tables"]))
        print("SQL dump:", sql_path)
        print("Manifest:", manifest_path)
        print("Total table records:", sum(
            item["records"] for item in manifest["tables"].values()
        ))
        print("RESULT: PASSED")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    export_database()
