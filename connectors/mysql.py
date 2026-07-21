# connectors/mysql.py
# MySQL implementation of DBConnector.
# Wraps mysqldump/mysql CLI tools via subprocess rather than
# reimplementing dump logic — this is standard practice.
#The correct approach: pass the password via an environment variable that mysqldump reads securely, avoiding it ever appearing in the process list. We'll build this properly in the connector.
import subprocess
import os
from connectors.base import DBConnector

class MySQLConnector(DBConnector):
    def __init__(self, host, port, user, password, database):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database

    def _env(self):
        """Pass password via environment variable, not command-line args,
        to avoid exposing it in process listings."""
        env = os.environ.copy()
        env["MYSQL_PWD"] = self.password
        return env

    

    def backup(self, output_path: str) -> str:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w") as f_out:
            result = subprocess.run(
                ["mysqldump", "-h", self.host, "-P", str(self.port), "-u", self.user,
                 "--single-transaction", self.database],
                env=self._env(),
                stdout=f_out,
                stderr=subprocess.PIPE,
                text=True
            )

        if result.returncode != 0:
            raise RuntimeError(f"mysqldump failed: {result.stderr}")

        return output_path

    def restore(self, backup_path: str) -> None:
        with open(backup_path, "r") as f_in:
            result = subprocess.run(
                ["mysql", "-h", self.host, "-P", str(self.port), "-u", self.user,
                 self.database],
                env=self._env(),
                stdin=f_in,
                stderr=subprocess.PIPE,
                text=True
            )

        if result.returncode != 0:
            raise RuntimeError(f"mysql restore failed: {result.stderr}")