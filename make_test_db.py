# make_test_db.py
# One-off script to create a dummy SQLite database for testing backup/restore.

import sqlite3

conn = sqlite3.connect("test.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
cursor.execute("INSERT INTO users (name, email) VALUES ('Ahmed', 'ahmed@example.com')")
cursor.execute("INSERT INTO users (name, email) VALUES ('Sara', 'sara@example.com')")
conn.commit()
conn.close()
print("test.db created")