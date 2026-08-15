# tests/test_mongo_connector.py
import pytest
from pymongo import MongoClient
from connectors.mongo import MongoConnector

MONGO_HOST = "localhost"
MONGO_PORT = 27017
TEST_DB = "pytest_mongo_test"


@pytest.fixture
def mongo_client():
    client = MongoClient(f"mongodb://{MONGO_HOST}:{MONGO_PORT}/")
    yield client
    client.drop_database(TEST_DB)
    client.close()


def test_backup_and_restore_roundtrip(tmp_path, mongo_client):
    """A MongoDB backup should be restorable and contain the exact same documents."""
    db = mongo_client[TEST_DB]
    db.users.insert_many([{"name": "Ahmed"}, {"name": "Sara"}])

    connector = MongoConnector(MONGO_HOST, MONGO_PORT, TEST_DB)
    backup_path = str(tmp_path / "mongo_backup")
    connector.backup(backup_path)

    db.users.drop()
    assert list(db.users.find()) == []

    connector.restore(backup_path)

    names = sorted(doc["name"] for doc in db.users.find())
    assert names == ["Ahmed", "Sara"]


def test_connection_succeeds_for_running_server():
    connector = MongoConnector(MONGO_HOST, MONGO_PORT, TEST_DB)
    assert connector.test_connection() is True