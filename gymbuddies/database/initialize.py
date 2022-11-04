"""Initialization script for database. Drops all metadata at the database url given by db.py and
recreates the database using metadata from db.py. Should be run with the parent module specified
(e.g. python -m database.initialize). This script can be used to rebase the database in the case
that the table structure is modified or the database is corrupted. All existing data will be erased;
any important information must be backed up. """

import sys
import click
from . import db

def reset_db():
    """Drops and creates database given by db DATABASE url, according to the metadata provided by
    db."""

    db.BASE.metadata.drop_all(db.engine)
    db.BASE.metadata.create_all(db.engine)


@click.command("init-db")
def init_db_cmd():
    """Drops and creates database given by db DATABASE url, according to the metadata provided by
    db."""

    reset_db()
    click.echo("Database re-initialized.")


def main():
    """Runs reset_db to recreate the database at DATABASE_URL, as specified by db.py."""

    if len(sys.argv) != 1:
        print("usage: python initialize.py", file=sys.stderr)
        sys.exit(1)
    try:
        reset_db()
    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
