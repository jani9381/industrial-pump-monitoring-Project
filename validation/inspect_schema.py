import sqlite3

conn = sqlite3.connect("data/industrial_monitoring.db")

tables = conn.execute("""
    SELECT name FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name
""").fetchall()

for (table,) in tables:
    print(f"\n{'='*50}")
    print("TABLE:", table)

    columns = conn.execute(
        f'PRAGMA table_info("{table}")'
    ).fetchall()

    for col in columns:
        print(col)

conn.close()
