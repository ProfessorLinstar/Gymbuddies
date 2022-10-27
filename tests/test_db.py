"""Tests database initialization."""
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from gymbuddies.database import db
from gymbuddies import database

def main():
    """Basic test of database API."""
    engine = create_engine(db.DATABASE_URL, echo=True)

    Session = sessionmaker(engine)  # pylint: disable=invalid-name
    session = Session()

    for user in session.query(db.User):
        database.debug.printv(user)
        if user.name == "jon":
            return

    user = db.User(netid=1,
                   name="jon",
                   level=1,
                   addinfo="I like running!",
                   interests={
                       "Losing weight": 1,
                       "Building mass": -1
                   },
                   schedule="n" * db.NUM_WEEK_BLOCKS)

    session.add(user)
    session.commit()


if __name__ == "__main__":
    main()
