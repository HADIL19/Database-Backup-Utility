# Database Backup Utility

A production-style CLI tool for backing up and restoring databases — built around a clean connector architecture that makes adding new database engines a matter of implementing one interface, not rewriting the tool.

Supports **SQLite** and **MySQL** out of the box, with automatic **compression**, **structured logging**, secure credential handling, and disaster-recovery-tested restore logic.

**Project page:** <https://roadmap.sh/projects/database-backup-utility>

## Why this exists

Most backup scripts are a single function that calls `mysqldump` and hopes for the best. This project treats backup/restore as what it actually is in production systems: a reliability-critical operation that needs consistency guarantees, proper error handling, observability, and a design that scales to more database engines without becoming spaghetti.

## Features

- 🔌 **Pluggable database support** — SQLite and MySQL implemented today via a shared `DBConnector` interface (`test_connection`, `backup`, `restore`). Adding a new engine means writing one new class — zero changes to existing code.
- 🛡️ **Consistency-safe backups** — SQLite uses the native SQLite backup API instead of a raw file copy, avoiding corruption on a live database. MySQL uses `mysqldump --single-transaction` for a consistent snapshot without table locks.
- 📦 **Streaming compression** — every backup is gzip-compressed with chunked I/O, so large databases don't get fully loaded into memory during compression.
- ♻️ **Verified restore** — a full backup → restore round-trip, stress-tested by deliberately destroying data and confirming full recovery.
- 📊 **Structured logging** — every operation logs start time, status, duration, and errors to both console and a persistent audit log (`logs/backup_activity.log`), so failures are traceable, not silent.
- 🔒 **Secure credential handling** — database passwords are passed to underlying CLI tools via environment variables, never exposed in process listings or shell history.
- 🧯 **Fails loudly, not silently** — connection issues, missing files, and unexpected runtime errors are caught, logged, and surfaced with clear messages instead of raw stack traces.

## Architecture

```
db_backup_utility/
├── cli.py                  # Entry point — argument parsing and orchestration only
├── connectors/
│   ├── base.py              # Abstract DBConnector interface
│   ├── sqlite.py             # SQLite implementation
│   └── mysql.py               # MySQL implementation (mysqldump/mysql via subprocess)
├── backup/
│   └── compression.py       # gzip compress/decompress, shared across all connectors
├── logging_utils/
│   └── logger.py             # Centralized structured logging
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

MySQL support requires the `mysql` and `mysqldump` CLI tools on your system PATH (included with MySQL Server).

## Usage

**Backup a SQLite database:**

```bash
python cli.py backup --db-type sqlite --path test.db --output ./backups
```

**Backup a MySQL database:**

```bash
python cli.py backup --db-type mysql --host localhost --port 3306 --user root --password YOUR_PASSWORD --database testdb --output ./backups
```

**Restore:**

```bash
python cli.py restore --db-type sqlite --path test.db --backup-file ./backups/test.db.bak.gz
python cli.py restore --db-type mysql --host localhost --port 3306 --user root --password YOUR_PASSWORD --database testdb --backup-file ./backups/testdb.sql.gz
```

Add `--no-compress` to skip compression on backup. Run `python cli.py --help` for the full command reference.

## Tested against real failure

Every restore path in this project has been validated with an actual disaster-recovery drill: create data → back it up → deliberately destroy the live database → restore → confirm the exact original data comes back. Not "it ran without crashing" — actual byte-for-byte data recovery, verified.

## Logging output

```
2026-07-21 06:28:36 | INFO | Backup started | db_type=mysql
2026-07-21 06:28:36 | INFO | Backup completed | file=./backups/testdb.sql.gz | duration=0.13s
```

## Engineering decisions worth knowing

- **`mysqldump`/`mysql` over a custom exporter** — these are the tools DBAs rely on in production; reimplementing dump logic reinvents a problem that's already solved correctly.
- **SQLite's backup API over `shutil.copy`** — a raw file copy risks grabbing a file mid-write; the backup API guarantees a consistent snapshot even during concurrent writes.
- **Environment variables for credentials** — `--password=xxx` on a command line is visible to any process inspector; environment variables aren't.
- **Connector interface over if/else branching** — new database engines plug in without touching existing, tested code paths.

## Roadmap

Actively being built out:

- **MongoDB connector** — same `DBConnector` interface, backed by `mongodump`/`mongorestore`
- **Automated scheduling** — a built-in recurring-backup command, with cron/Task Scheduler as the production-recommended alternative
- Automated test suite (pytest) covering connectors and compression
- Cloud storage backends (S3 / GCS)
- Slack notifications on completion/failure
- Selective (table/collection-level) restore

## Tech stack

Python 3.10+ · [Click](https://click.palletsprojects.com/) · `sqlite3` · `mysqldump`/`mysql` CLI · `gzip`

## License

MIT
