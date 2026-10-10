"""Load seed_data.sql into tasks.db (no sqlite3 CLI needed)."""
import os
import sqlite3

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
conn = sqlite3.connect(os.path.join(root, "tasks.db"))
with open(os.path.join(root, "seed_data.sql"), encoding="utf-8") as f:
    conn.executescript(f.read())
conn.commit()
conn.close()
print("Seed data loaded.")
