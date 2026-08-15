# Database Backup Utility

A production-style CLI tool for backing up and restoring databases — built around a clean connector architecture that makes adding new database engines a matter of implementing one interface, not rewriting the tool.

Supports **SQLite**, **MySQL**, and **MongoDB**, with automatic **compression**, **structured logging**, **scheduled backups**, secure credential handling, and disaster-recovery-tested restore logic across all three engines.

**Project page:** https://roadmap.sh/projects/database-backup-utility

## Why this exists

Most backup scripts are a single function that calls `mysqldump` and hopes for the best. This project treats backup/restore as what it actually is in production systems: a reliability-critical operation that needs consistency guarantees, proper error handling, observability, and a design that scales to more database engines without becoming spaghetti.

## Features

- 🔌 **Pluggable database support** — SQLite, MySQL, and MongoDB, all implemented via a shared `DBConnector` interface (`test_connection`, `backup`, `restore`). Adding a new engine means writing one new class — zero changes to existing code.
- 🛡️ **Consistency-safe backups** — SQLite uses the native SQLite backup API instead of a raw file copy, avoiding corruption on a live database. MySQL uses `mysqldump --single-transaction` for a consistent snapshot without table locks. MongoDB uses `mongodump`/`mongorestore --drop` for a clean, exact restore.
- 📦 **Streaming, format-aware compression** — file-based backups (SQLite, MySQL) are gzip-compressed; folder-based backups (MongoDB's BSON dump directory) are zip-compressed automatically. Chunked I/O throughout, so large databases don't get fully loaded into memory.
- ♻️ **Verified restore** — every connector has been stress-tested with a real disaster-recovery drill: create data, back it up, deliberately destroy it, restore, confirm byte-for-byte recovery.
- ⏰ **Scheduled backups** — a built-in recurring-backup command runs backups automatically on a configurable interval, no external tooling required (with cron/Task Scheduler documented as the production-grade alternative).
- 📊 **Structured logging** — every operation logs start time, status, duration, and errors to both console and a persistent audit log (`logs/backup_activity.log`).
- 🔒 **Secure credential handling** — database passwords are passed to underlying CLI tools via environment variables, never exposed in process listings or shell history.
- 🧯 **Fails loudly, not silently** — connection issues, missing files, and unexpected runtime errors are caught, logged, and surfaced with clear messages instead of raw stack traces.
- ✅ **Automated test coverage** — a pytest suite covering backup/restore round-trips, disaster recovery, connection handling, and compression, for both file-based and folder-based backups.

## Architecture

```
db_backup_utility/
├── cli.py                  # Entry point — argument parsing and orchestration only
├── connectors/
│   ├── base.py              # Abstract DBConnector interface
│   ├── sqlite.py             # SQLite implementation
│   ├── mysql.py               # MySQL implementation (mysqldump/mysql via subprocess)
│   └── mongo.py                # MongoDB implementation (mongodump/mongorestore via subprocess)
├── backup/
│   └── compression.py       # gzip (files) / zip (folders) compress & decompress
├── storage/
│   └── local.py              # Local disk storage abstraction
├── logging_utils/
│   └── logger.py             # Centralized structured logging
├── tests/
│   ├── test_sqlite_connector.py
│   ├── test_mongo_connector.py
│   └── test_compression.py
├── make_test_db.py          # Generates a sample SQLite DB for local testing
└── requirements.txt
```

**Core design principle:** `cli.py` contains zero database-specific logic. It parses arguments, resolves the correct connector through a factory function, and calls the same three methods regardless of database type. This is the Strategy pattern applied to backup operations — swap the implementation, keep the interface.

## Installation

```bash
git clone https://github.com/HADIL19/database-backup-utility.git
cd database-backup-utility
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**External tooling required per database:**
- MySQL: `mysql` and `mysqldump` CLI tools on your system PATH
- MongoDB: `mongod` (server) running, plus `mongodump`/`mongorestore` (MongoDB Database Tools) on your system PATH

## Usage

### Backup

```bash
# SQLite
python cli.py backup --db-type sqlite --path test.db --output ./backups

# MySQL
python cli.py backup --db-type mysql --host localhost --port 3306 --user root --password YOUR_PASSWORD --database testdb --output ./backups

# MongoDB
python cli.py backup --db-type mongo --host localhost --port 27017 --database testdb --output ./backups
```

Add `--no-compress` to skip compression.

### Restore

```bash
python cli.py restore --db-type sqlite --path test.db --backup-file ./backups/test.db.bak.gz
python cli.py restore --db-type mysql --host localhost --port 3306 --user root --password YOUR_PASSWORD --database testdb --backup-file ./backups/testdb.sql.gz
python cli.py restore --db-type mongo --host localhost --port 27017 --database testdb --backup-file ./backups/testdb.zip
```

### Scheduled backups

```bash
python cli.py schedule-backup --db-type sqlite --path test.db --output ./backups --interval-minutes 60
```

Runs continuously, triggering a backup immediately and then on every interval, until stopped with `Ctrl+C`. For production use, running the `backup` command via cron (Linux/Mac) or Task Scheduler (Windows) is the more robust option, since it survives reboots without needing a persistent process.

### Help

```bash
python cli.py --help
```

## Tested against real failure

Every restore path in this project — SQLite, MySQL, and MongoDB — has been validated with an actual disaster-recovery drill: create data → back it up → deliberately destroy the live database → restore → confirm the exact original data comes back, including MongoDB's original document IDs. Not "it ran without crashing" — actual verified data recovery, three times over, for three different database engines.

## Running the tests

```bash
pytest -v
```

```
tests/test_compression.py::test_compress_and_decompress_roundtrip PASSED
tests/test_compression.py::test_compress_removes_original_by_default PASSED
tests/test_mongo_connector.py::test_backup_and_restore_roundtrip PASSED
tests/test_mongo_connector.py::test_connection_succeeds_for_running_server PASSED
tests/test_sqlite_connector.py::test_backup_and_restore_roundtrip PASSED
tests/test_sqlite_connector.py::test_restore_recovers_dropped_data PASSED
tests/test_sqlite_connector.py::test_connection_fails_for_missing_file PASSED
```

## Logging output

```
2026-08-15 09:02:41 | INFO | Backup started | db_type=sqlite
2026-08-15 09:02:41 | INFO | Backup completed | file=./backups/test.db.bak.gz | duration=0.04s
```

## Engineering decisions worth knowing

- **`mysqldump`/`mongodump` over custom exporters** — these are the tools DBAs rely on in production; reimplementing dump logic reinvents a problem that's already solved correctly.
- **SQLite's backup API over `shutil.copy`** — a raw file copy risks grabbing a file mid-write; the backup API guarantees a consistent snapshot even during concurrent writes.
- **Format-aware compression** — MongoDB's `mongodump` produces a directory of BSON files, not a single file, unlike SQLite/MySQL. Rather than special-casing this in the CLI, `compress_file()`/`decompress_file()` auto-detect files vs. folders and branch to gzip or zip accordingly — callers never need to know the difference.
- **Environment variables for credentials** — `--password=xxx` on a command line is visible to any process inspector; environment variables aren't.
- **Connector interface over if/else branching** — new database engines plug in without touching existing, tested code paths. Confirmed in practice: the abstract base class caught a real bug during development when a required method was accidentally left out of a connector — Python refused to instantiate the class instead of failing silently later.
- **Shared `run_backup()` core logic** — the `backup` command and `schedule-backup` command both call the same underlying function rather than duplicating logic, so behavior can't silently drift between manual and scheduled runs.

## Roadmap

- PostgreSQL connector (architecture already supports it — same interface as the other three)
- Cloud storage backends (S3 / GCS)
- Slack notifications on completion/failure
- Selective (table/collection-level) restore
- Authentication support for MongoDB (currently assumes a local, unauthenticated instance)

## Tech stack

Python 3.10+ · [Click](https://click.palletsprojects.com/) · `sqlite3` · `mysqldump`/`mysql` CLI · `mongodump`/`mongorestore` CLI · `pymongo` · `schedule` · `pytest` · `gzip`/`zip`

## License

MIT