# connectors/mongo.py
import subprocess
import os
from shutil import which
from connectors.base import DBConnector

class MongoConnector(DBConnector):
    def __init__(self, host, port, database):
        self.host = host
        self.port = port
        self.database = database

    def test_connection(self) -> bool:
        try:
            shell = "mongosh" if which("mongosh") else "mongo"
            result = subprocess.run(
                [shell, f"mongodb://{self.host}:{self.port}/{self.database}",
                 "--eval", "db.runCommand({ ping: 1 })"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except FileNotFoundError:
            try:
                from pymongo import MongoClient
                client = MongoClient(f"mongodb://{self.host}:{self.port}/", serverSelectionTimeoutMS=3000)
                client.admin.command("ping")
                client.close()
                return True
            except Exception:
                return False

    def backup(self, output_path: str) -> str:
        os.makedirs(output_path, exist_ok=True)
        result = subprocess.run(
            ["mongodump", f"--host={self.host}", f"--port={self.port}",
             f"--db={self.database}", f"--out={output_path}"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"mongodump failed: {result.stderr}")
        return output_path

    def restore(self, backup_path: str) -> None:
        db_dump_path = os.path.join(backup_path, self.database)
        result = subprocess.run(
            ["mongorestore", f"--host={self.host}", f"--port={self.port}",
             f"--db={self.database}", "--drop", db_dump_path],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"mongorestore failed: {result.stderr}")