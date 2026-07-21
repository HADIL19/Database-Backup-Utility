# cli.py
import click
import os
import time
from connectors.sqlite import SQLiteConnector
from backup.compression import compress_file, decompress_file
from logging_utils.logger import get_logger

logger = get_logger()

@click.group()
def cli():
    """Database Backup Utility."""
    pass


@cli.command()
@click.option('--db-type', required=True, type=click.Choice(['sqlite', 'mysql', 'postgres', 'mongo']))
@click.option('--path', help='Path to the SQLite database file')
@click.option('--output', default='./backups', help='Folder to save the backup in')
@click.option('--compress/--no-compress', default=True, help='Compress the backup file (default: on)')
def backup(db_type, path, output, compress):
    """Backup a database."""
    start_time = time.time()
    logger.info(f"Backup started | db_type={db_type} | path={path}")

    try:
        if db_type == 'sqlite':
            connector = SQLiteConnector(path)
            if not connector.test_connection():
                logger.error(f"Backup failed | reason=database not found at {path}")
                click.echo(f"Error: could not find database at {path}")
                return

            dest = os.path.join(output, os.path.basename(path) + '.bak')
            connector.backup(dest)

            if compress:
                dest = compress_file(dest)

            duration = round(time.time() - start_time, 2)
            logger.info(f"Backup completed | file={dest} | duration={duration}s")
            click.echo(f"Backup saved to {dest}")
        else:
            logger.warning(f"Backup skipped | reason={db_type} not implemented yet")
            click.echo(f"{db_type} not implemented yet.")

    except Exception as e:
        duration = round(time.time() - start_time, 2)
        logger.error(f"Backup failed | error={str(e)} | duration={duration}s")
        click.echo(f"Backup failed: {e}")


@cli.command()
@click.option('--db-type', required=True, type=click.Choice(['sqlite', 'mysql', 'postgres', 'mongo']))
@click.option('--path', help='Path to the target SQLite database file (will be overwritten)')
@click.option('--backup-file', required=True, help='Path to the backup file to restore from')
def restore(db_type, path, backup_file):
    """Restore a database from a backup file."""
    start_time = time.time()
    logger.info(f"Restore started | db_type={db_type} | path={path} | backup_file={backup_file}")

    try:
        if db_type == 'sqlite':
            if not os.path.exists(backup_file):
                logger.error(f"Restore failed | reason=backup file not found at {backup_file}")
                click.echo(f"Error: backup file not found at {backup_file}")
                return

            actual_backup_file = backup_file
            if backup_file.endswith('.gz'):
                actual_backup_file = decompress_file(backup_file)

            connector = SQLiteConnector(path)
            connector.restore(actual_backup_file)

            if backup_file.endswith('.gz'):
                os.remove(actual_backup_file)

            duration = round(time.time() - start_time, 2)
            logger.info(f"Restore completed | path={path} | duration={duration}s")
            click.echo(f"Restored {path} from {backup_file}")
        else:
            logger.warning(f"Restore skipped | reason={db_type} not implemented yet")
            click.echo(f"{db_type} not implemented yet.")

    except Exception as e:
        duration = round(time.time() - start_time, 2)
        logger.error(f"Restore failed | error={str(e)} | duration={duration}s")
        click.echo(f"Restore failed: {e}")


if __name__ == '__main__':
    cli()