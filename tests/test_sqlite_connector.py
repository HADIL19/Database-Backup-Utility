# tests/test_sqlite_connector.py
import sqlite3
from connectors.sqlite import SQLiteConnector


def test_backup_and_restore_roundtrip(tmp_path):
    """A backup should be restorable and contain the exact same data."""

    # 1. ARRANGE: create a real SQLite db with known data
    db_path = tmp_path / "original.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("INSERT INTO users (name) VALUES ('Ahmed')")
    conn.commit()
    conn.close()

    # 2. ACT: back it up
    backup_path = tmp_path / "backup.db"
    connector = SQLiteConnector(str(db_path))
    connector.backup(str(backup_path))

    # 3. ASSERT: the backup file has the same data
    backup_conn = sqlite3.connect(backup_path)
    rows = backup_conn.execute("SELECT * FROM users").fetchall()
    backup_conn.close()

    assert rows == [(1, 'Ahmed')]


def test_restore_recovers_dropped_data(tmp_path):
    """Simulates data loss and confirms restore brings it back — the real disaster-recovery test, automated."""

    db_path = tmp_path / "original.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("INSERT INTO users (name) VALUES ('Sara')")
    conn.commit()
    conn.close()

    backup_path = tmp_path / "backup.db"
    connector = SQLiteConnector(str(db_path))
    connector.backup(str(backup_path))

    # Simulate disaster: drop the table
    conn = sqlite3.connect(db_path)
    conn.execute("DROP TABLE users")
    conn.commit()
    conn.close()

    # Restore
    connector.restore(str(backup_path))

    # Confirm data is back
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT * FROM users").fetchall()
    conn.close()

    assert rows == [(1, 'Sara')]


def test_connection_fails_for_missing_file(tmp_path):
    """test_connection should return False if the db file doesn't exist."""
    fake_path = tmp_path / "does_not_exist.db"
    connector = SQLiteConnector(str(fake_path))

    assert connector.test_connection() is False