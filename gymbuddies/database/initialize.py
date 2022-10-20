"""Initialization script for database. Drops all metadata at the database url given by db.py and recreates the database using metadata from db.py."""
import sys
from sqlalchemy import create_engine
from . import db

def reset_db():
    """Drops and creates database given by db DATABASE url, according to the metadata provided by db."""

    engine = create_engine(db.DATABASE_URL, echo=True)
    db.BASE.metadata.drop_all(engine)
    db.BASE.metadata.create_all(engine)


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
