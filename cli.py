# cli.py
# Entry point. Parses CLI arguments with Click and delegates
# to the correct connector. Contains no backup logic itself.

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

if __name__ == '__main__':
    cli()