"""Database API"""
from typing import Optional
from sqlalchemy.orm import Session
import db

@db.session_decorator
def create_user(netid: str, /, *, session: Session, **kwargs) -> Optional[bool]:
    """Attempts to create a user with netid and a profile provided by **kwargs. Does nothing if the user already exists."""

    if session.query(db.User).filter(db.User.netid == netid).all():
        raise ValueError("User already exists. Skipping creation.")

    user = db.User(netid=netid, **kwargs)
    session.add(user)
    session.commit()

    return True


@db.session_decorator
def update_user(netid: str, /, *, session: Session, **kwargs) -> Optional[bool]:
    """Attempts to update the profile information of of a user with netid with the profile provided by **kwargs. Does nothing if the user does not
       exist."""

    user = session.query(db.User).filter(db.User.netid == netid).one()  # raises an error if no such user exists
    for k,v in kwargs.items():
        setattr(user, k, v)

    return True


@db.session_decorator
def delete_user(netid: str, /, *, session: Session) -> Optional[bool]:
    """Attempts to remove a user from the database, removing all related entries and references. Does nothing if the user does not exist."""

    user = session.query(db.User).filter(db.User.netid == netid).one()  # raises an error if no such user exists

    return False


### User information ###
# return name associated with userid
def get_name(userId: int) -> Optional[str]:
    return ""


# return bio associated with userid
def get_bio(userId: int) -> Optional[str]:
    return ""


# return level assciate with userid
def get_level(userId: int) -> Optional[str]:
    return ""


# return additional into associated with userid
def get_additionalInfo(userId: int) -> Optional[str]:
    return ""
