# connectors/sqlite.py
# SQLite implementation of DBConnector.
# Uses sqlite3's built-in backup API (safe against corruption),
# NOT a raw file copy.

import sqlite3
import os
from connectors.base import DBConnector

class SQLiteConnector(DBConnector):
    def __init__(self, path):
        self.path = path

    def test_connection(self) -> bool:
        return os.path.exists(self.path)

    def backup(self, output_path: str) -> str:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        source_conn = sqlite3.connect(self.path)
        dest_conn = sqlite3.connect(output_path)
        with dest_conn:
            source_conn.backup(dest_conn)
        source_conn.close()
        dest_conn.close()

        return output_path

    def restore(self, backup_path: str) -> None:
        source_conn = sqlite3.connect(backup_path)
        dest_conn = sqlite3.connect(self.path)
        with dest_conn:
            source_conn.backup(dest_conn)
        source_conn.close()
        dest_conn.close()