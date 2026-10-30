import sqlite3

conn = sqlite3.connect("data/industrial_monitoring.db")

print("FOREIGN KEY ENFORCEMENT:")
print(conn.execute("PRAGMA foreign_keys").fetchone()[0])

print("\nFOREIGN KEY VIOLATIONS:")
violations = conn.execute("PRAGMA foreign_key_check").fetchall()

if violations:
    for violation in violations:
        print(violation)
    print("RESULT: VIOLATIONS FOUND")
else:
    print("No foreign-key violations found.")
    print("RESULT: PASSED")

print("\nDATABASE INTEGRITY:")
print(conn.execute("PRAGMA integrity_check").fetchone()[0])

conn.close()
