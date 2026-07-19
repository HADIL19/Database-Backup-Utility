# cli.py
import click

@click.group()
def cli():
    pass

@cli.command()
@click.option('--db-type', required=True, type=click.Choice(['sqlite', 'mysql', 'postgres', 'mongo']))
@click.option('--path', help='For SQLite: path to db file')
def backup(db_type, path):
    click.echo(f"Backing up {db_type} db...")

if __name__ == '__main__':
    cli()