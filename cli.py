# cli.py
import click
import os
from connectors.sqlite import SQLiteConnector

@click.group()
def cli():
    """Database Backup Utility."""
    pass

@cli.command()
@click.option('--db-type', required=True, type=click.Choice(['sqlite', 'mysql', 'postgres', 'mongo']))
@click.option('--path', help='Path to the SQLite database file')
@click.option('--output', default='./backups', help='Folder to save the backup in')
def backup(db_type, path, output):
    """Backup a database."""
    if db_type == 'sqlite':
        connector = SQLiteConnector(path)
        if not connector.test_connection():
            click.echo(f"Error: could not find database at {path}")
            return
        dest = os.path.join(output, os.path.basename(path) + '.bak')
        connector.backup(dest)
        click.echo(f"Backup saved to {dest}")
    else:
        click.echo(f"{db_type} not implemented yet.")

@cli.command()
@click.option('--db-type', required=True, type=click.Choice(['sqlite', 'mysql', 'postgres', 'mongo']))
@click.option('--path', help='Path to the target SQLite database file (will be overwritten)')
@click.option('--backup-file', required=True, help='Path to the backup file to restore from')
def restore(db_type, path, backup_file):
    """Restore a database from a backup file."""
    if db_type == 'sqlite':
        if not os.path.exists(backup_file):
            click.echo(f"Error: backup file not found at {backup_file}")
            return

        connector = SQLiteConnector(path)
        connector.restore(backup_file)
        click.echo(f"Restored {path} from {backup_file}")
    else:
        click.echo(f"{db_type} not implemented yet.")

if __name__ == '__main__':
    cli()