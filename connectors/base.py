# connectors/base.py
# Abstract interface every database connector must implement.
# This guarantees cli.py can treat MySQL, Postgres, MongoDB, and SQLite
# the same way, without knowing their internal details.

from abc import ABC, abstractmethod

class DBConnector(ABC):
    @abstractmethod
    def test_connection(self) -> bool:
        """Check the database is reachable/valid before doing anything."""
        pass

    @abstractmethod
    def backup(self, output_path: str) -> str:
        """Perform backup, return path to the created backup file."""
        pass

    @abstractmethod
    def restore(self, backup_path: str) -> None:
        """Restore the database from a backup file."""
        pass