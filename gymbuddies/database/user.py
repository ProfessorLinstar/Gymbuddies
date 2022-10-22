"""Database API"""

from typing import Optional
from sqlalchemy.orm import Session
from . import db


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
    for k, v in kwargs.items():
        setattr(user, k, v)

    return True


@db.session_decorator
def delete_user(netid: str, /, *, session: Session) -> Optional[bool]:
    """Attempts to remove a user from the database, removing all related entries and references. Does nothing if the user does not exist."""

    user = session.query(db.User).filter(db.User.netid == netid).one()  # raises an error if no such user exists

    session.delete(user)
    session.commit()

    return True


@db.session_decorator
def get_name(netid: str, /, *, session: Session) -> Optional[str]:
    """Attempts to return the name of a user."""
    return session.query(db.User).filter(db.User.netid == netid).one().name


@db.session_decorator
def get_bio(netid: str, /, *, session: Session) -> Optional[str]:
    """Attempts to return the bio of a user."""
    return session.query(db.User).filter(db.User.netid == netid).one().bio


@db.session_decorator
def get_level(netid: str, /, *, session: Session) -> Optional[str]:
    """Attempts to return the level of a user."""
    return session.query(db.User).filter(db.User.netid == netid).one().level


@db.session_decorator
def get_addinfo(netid: str, /, *, session: Session) -> Optional[str]:
    """Attempts to return the additional info of a user."""
    return session.query(db.User).filter(db.User.netid == netid).one().addinfo
