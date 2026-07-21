# cli.py
import click
import os
import time
from connectors.sqlite import SQLiteConnector
from connectors.mysql import MySQLConnector
from backup.compression import compress_file, decompress_file
from logging_utils.logger import get_logger

logger = get_logger()

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
    else:
        return None


@cli.command()
@click.option('--db-type', required=True, type=click.Choice(['sqlite', 'mysql', 'postgres', 'mongo']))
@click.option('--path', help='Path to the SQLite database file (SQLite only)')
@click.option('--host', default='localhost', help='DB host (MySQL/Postgres/Mongo)')
@click.option('--port', default=3306, type=int, help='DB port')
@click.option('--user', default='root', help='DB username')
@click.option('--password', default='', help='DB password')
@click.option('--database', help='Database name (MySQL/Postgres/Mongo)')
@click.option('--output', default='./backups', help='Folder to save the backup in')
@click.option('--compress/--no-compress', default=True, help='Compress the backup file (default: on)')
def backup(db_type, path, host, port, user, password, database, output, compress):
    """Backup a database."""
    start_time = time.time()
    logger.info(f"Backup started | db_type={db_type}")

    try:
        connector = get_connector(db_type, path, host, port, user, password, database)
        if connector is None:
            logger.warning(f"Backup skipped | reason={db_type} not implemented yet")
            click.echo(f"{db_type} not implemented yet.")
            return

        if not connector.test_connection():
            logger.error(f"Backup failed | reason=connection test failed")
            click.echo("Error: could not connect to database.")
            return

        filename = database if db_type != 'sqlite' else os.path.basename(path)
        dest = os.path.join(output, f"{filename}.sql" if db_type != 'sqlite' else f"{filename}.bak")

        os.makedirs(output, exist_ok=True)
        connector.backup(dest)

        if compress:
            dest = compress_file(dest)

        duration = round(time.time() - start_time, 2)
        logger.info(f"Backup completed | file={dest} | duration={duration}s")
        click.echo(f"Backup saved to {dest}")

    except Exception as e:
        duration = round(time.time() - start_time, 2)
        logger.error(f"Backup failed | error={str(e)} | duration={duration}s")
        click.echo(f"Backup failed: {e}")


@cli.command()
@click.option('--db-type', required=True, type=click.Choice(['sqlite', 'mysql', 'postgres', 'mongo']))
@click.option('--path', help='Path to the target SQLite database file (SQLite only)')
@click.option('--host', default='localhost')
@click.option('--port', default=3306, type=int)
@click.option('--user', default='root')
@click.option('--password', default='')
@click.option('--database', help='Database name (MySQL/Postgres/Mongo)')
@click.option('--backup-file', required=True, help='Path to the backup file to restore from')
def restore(db_type, path, host, port, user, password, database, backup_file):
    """Restore a database from a backup file."""
    start_time = time.time()
    logger.info(f"Restore started | db_type={db_type} | backup_file={backup_file}")

    try:
        if not os.path.exists(backup_file):
            logger.error(f"Restore failed | reason=backup file not found at {backup_file}")
            click.echo(f"Error: backup file not found at {backup_file}")
            return

        actual_backup_file = backup_file
        if backup_file.endswith('.gz'):
            actual_backup_file = decompress_file(backup_file)

        connector = get_connector(db_type, path, host, port, user, password, database)
        if connector is None:
            logger.warning(f"Restore skipped | reason={db_type} not implemented yet")
            click.echo(f"{db_type} not implemented yet.")
            return

        connector.restore(actual_backup_file)

        if backup_file.endswith('.gz'):
            os.remove(actual_backup_file)

        duration = round(time.time() - start_time, 2)
        logger.info(f"Restore completed | duration={duration}s")
        click.echo(f"Restored from {backup_file}")

    except Exception as e:
        duration = round(time.time() - start_time, 2)
        logger.error(f"Restore failed | error={str(e)} | duration={duration}s")
        click.echo(f"Restore failed: {e}")


if __name__ == '__main__':
    cli()