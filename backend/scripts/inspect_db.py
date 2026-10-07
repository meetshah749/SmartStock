import sqlite3, os

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'smartstock_dev.db')
print(f"DB path: {db_path}")
print(f"Exists: {os.path.exists(db_path)}")
print(f"Size: {os.path.getsize(db_path)} bytes")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print(f"\nTables: {tables}")

if 'users' in tables:
    cursor.execute("SELECT email, is_admin, is_active, is_verified FROM users")
    rows = cursor.fetchall()
    print(f"\nUsers ({len(rows)}):")
    for r in rows:
        print(f"  email={r[0]}  admin={r[1]}  active={r[2]}  verified={r[3]}")
    if not rows:
        print("  (no users found)")
else:
    print("\nNo 'users' table found!")

conn.close()
