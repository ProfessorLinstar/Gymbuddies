"""Tests database initialization."""
import json
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from gymbuddies.flaskr.database import db


def __main__():
    engine = create_engine(db.DB_STRING, echo=True)
    # BASE.metadata.drop_all(engine)
    db.BASE.metadata.create_all(engine)

    Session = sessionmaker(engine)  # pylint: disable=invalid-name
    session = Session()

    for user in session.query(db.User):
        print(json.dumps({k: v for k, v in vars(user).items() if "_" not in k}, sort_keys=True, indent=4))
        if user.name == "jon":
            return

    user = db.User(userid=1,
                name="jon",
                level=1,
                addinfo="I like running!",
                interests={
                    "Losing weight": 1,
                    "Building mass": -1
                },
                schedule="n" * db.NUM_TIME_BLOCKS)

    session.add(user)
    session.commit()


if __name__ == "__main__":
    __main__()
