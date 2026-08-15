# cli.py
import click
import os
import shutil
import time
import schedule
from connectors.sqlite import SQLiteConnector
from connectors.mysql import MySQLConnector
from connectors.mongo import MongoConnector
from backup.compression import compress_file, decompress_file
from storage.local import LocalStorage
from logging_utils.logger import get_logger

logger = get_logger()

DEFAULT_PORTS = {
    'mysql': 3306,
    'mongo': 27017,
}


@click.group()
def cli():
    """Database Backup Utility."""
    pass


def get_connector(db_type, path, host, port, user, password, database):
    """Factory function: returns the right connector for the given db_type."""
    if db_type == 'sqlite':
        return SQLiteConnector(path)
    elif db_type == 'mysql':
        return MySQLConnector(host, port, user, password, database)
    elif db_type == 'mongo':
        return MongoConnector(host, port, database)
    else:
        return None


def run_backup(db_type, path, host, port, user, password, database, output, compress):
    """Core backup logic, callable directly (not just via CLI) so the scheduler can reuse it."""
    start_time = time.time()
    logger.info(f"Backup started | db_type={db_type}")

    if port is None:
        port = DEFAULT_PORTS.get(db_type, 0)

    try:
        connector = get_connector(db_type, path, host, port, user, password, database)
        if connector is None:
            logger.warning(f"Backup skipped | reason={db_type} not implemented yet")
            return False

        if not connector.test_connection():
            logger.error("Backup failed | reason=connection test failed")
            return False

        os.makedirs(output, exist_ok=True)
        storage = LocalStorage(output)

        if db_type == 'sqlite':
            filename = os.path.basename(path)
            temp_dest = os.path.join(output, f"{filename}.bak")
        elif db_type == 'mysql':
            temp_dest = os.path.join(output, f"{database}.sql")
        elif db_type == 'mongo':
            temp_dest = os.path.join(output, database)
        else:
            temp_dest = os.path.join(output, database or "backup")

        connector.backup(temp_dest)

        if compress:
            temp_dest = compress_file(temp_dest)

        final_path = storage.save(temp_dest)

        duration = round(time.time() - start_time, 2)
        logger.info(f"Backup completed | file={final_path} | duration={duration}s")
        return True

    except Exception as e:
        duration = round(time.time() - start_time, 2)
        logger.error(f"Backup failed | error={str(e)} | duration={duration}s")
        return False


@cli.command()
@click.option('--db-type', required=True, type=click.Choice(['sqlite', 'mysql', 'postgres', 'mongo']))
@click.option('--path', help='Path to the SQLite database file (SQLite only)')
@click.option('--host', default='localhost', help='DB host (MySQL/Postgres/Mongo)')
@click.option('--port', default=None, type=int, help='DB port (defaults per db-type if omitted)')
@click.option('--user', default='root', help='DB username (MySQL only)')
@click.option('--password', default='', help='DB password (MySQL only)')
@click.option('--database', help='Database name (MySQL/Postgres/Mongo)')
@click.option('--output', default='./backups', help='Folder to save the backup in')
@click.option('--compress/--no-compress', default=True, help='Compress the backup file (default: on)')
def backup(db_type, path, host, port, user, password, database, output, compress):
    """Backup a database."""
    success = run_backup(db_type, path, host, port, user, password, database, output, compress)
    if success:
        click.echo("Backup completed successfully.")
    else:
        click.echo("Backup failed. Check logs for details.")


@cli.command()
@click.option('--db-type', required=True, type=click.Choice(['sqlite', 'mysql', 'postgres', 'mongo']))
@click.option('--path', help='Path to the target SQLite database file (SQLite only)')
@click.option('--host', default='localhost')
@click.option('--port', default=None, type=int, help='DB port (defaults per db-type if omitted)')
@click.option('--user', default='root')
@click.option('--password', default='')
@click.option('--database', help='Database name (MySQL/Postgres/Mongo)')
@click.option('--backup-file', required=True, help='Path to the backup file/folder to restore from')
def restore(db_type, path, host, port, user, password, database, backup_file):
    """Restore a database from a backup file."""
    start_time = time.time()
    logger.info(f"Restore started | db_type={db_type} | backup_file={backup_file}")

    if port is None:
        port = DEFAULT_PORTS.get(db_type, 0)

    try:
        if not os.path.exists(backup_file):
            logger.error(f"Restore failed | reason=backup file not found at {backup_file}")
            click.echo(f"Error: backup file not found at {backup_file}")
            return

        actual_backup_file = backup_file
        is_compressed = backup_file.endswith('.gz') or backup_file.endswith('.zip')

        if is_compressed:
            actual_backup_file = decompress_file(backup_file)

        connector = get_connector(db_type, path, host, port, user, password, database)
        if connector is None:
            logger.warning(f"Restore skipped | reason={db_type} not implemented yet")
            click.echo(f"{db_type} not implemented yet.")
            return

        connector.restore(actual_backup_file)

        if is_compressed:
            if os.path.isdir(actual_backup_file):
                shutil.rmtree(actual_backup_file)
            else:
                os.remove(actual_backup_file)

        duration = round(time.time() - start_time, 2)
        logger.info(f"Restore completed | duration={duration}s")
        click.echo(f"Restored from {backup_file}")

    except Exception as e:
        duration = round(time.time() - start_time, 2)
        logger.error(f"Restore failed | error={str(e)} | duration={duration}s")
        click.echo(f"Restore failed: {e}")


@cli.command(name='schedule-backup')
@click.option('--db-type', required=True, type=click.Choice(['sqlite', 'mysql', 'postgres', 'mongo']))
@click.option('--path', help='Path to the SQLite database file (SQLite only)')
@click.option('--host', default='localhost')
@click.option('--port', default=None, type=int)
@click.option('--user', default='root')
@click.option('--password', default='')
@click.option('--database', help='Database name (MySQL/Postgres/Mongo)')
@click.option('--output', default='./backups')
@click.option('--compress/--no-compress', default=True)
@click.option('--interval-minutes', default=60, help='How often to run backup, in minutes')
def schedule_backup(db_type, path, host, port, user, password, database, output, compress, interval_minutes):
    """Run backup automatically on a recurring interval. Runs until stopped with Ctrl+C."""

    def job():
        click.echo(f"[{time.ctime()}] Running scheduled backup...")
        success = run_backup(db_type, path, host, port, user, password, database, output, compress)
        status = "succeeded" if success else "failed"
        click.echo(f"[{time.ctime()}] Scheduled backup {status}.")

    schedule.every(interval_minutes).minutes.do(job)
    click.echo(f"Scheduler started — backing up every {interval_minutes} minute(s). Press Ctrl+C to stop.")

    job()  # run once immediately, then wait for the interval

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    cli()