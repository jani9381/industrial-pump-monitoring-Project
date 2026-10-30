import sqlite3

conn = sqlite3.connect("data/industrial_monitoring.db")

tables = conn.execute("""
    SELECT name FROM sqlite_master
    WHERE type = 'table'
      AND name NOT LIKE 'sqlite_%'
    ORDER BY name
""").fetchall()

for (table,) in tables:
    print(f"\nTABLE: {table}")
    foreign_keys = conn.execute(
        f'PRAGMA foreign_key_list("{table}")'
    ).fetchall()

    if foreign_keys:
        for fk in foreign_keys:
            print("FOREIGN KEY:", fk)
    else:
        print("No declared foreign keys")

conn.close()
