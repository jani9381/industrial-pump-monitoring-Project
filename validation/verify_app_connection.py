from database.db import get_connection

conn = get_connection()

print("APPLICATION DATABASE CONNECTION:")
print("Foreign key enforcement:", conn.execute("PRAGMA foreign_keys").fetchone()[0])

print("\nDATABASE INTEGRITY:")
print(conn.execute("PRAGMA integrity_check").fetchone()[0])

print("\nFOREIGN KEY VIOLATIONS:")
violations = conn.execute("PRAGMA foreign_key_check").fetchall()
print("Count:", len(violations))

conn.close()
