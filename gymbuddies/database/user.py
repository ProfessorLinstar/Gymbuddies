"""Database API"""

from typing import Optional
from sqlalchemy.orm import Session
from . import db


# TODO: process kwargs to make sure no extraneous keywords were supplied. Provide defaults if any
# are null
@db.session_decorator
def create(netid: str, *, session: Optional[Session] = None, **kwargs) -> Optional[bool]:
    """Attempts to create a user with netid and a profile provided by **kwargs. Does nothing if the
    user already exists."""
    assert session is not None

    if session.query(db.User).filter(db.User.netid == netid).all():
        raise ValueError("User already exists. Skipping creation.")

    user = db.User(netid=netid, **kwargs)
    session.add(user)
    session.commit()

    return True


# TODO: same here: process kwargs
@db.session_decorator
def update(netid: str, *, session: Optional[Session] = None, **kwargs) -> Optional[bool]:
    """Attempts to update the profile information of of a user with netid with the profile provided
    by **kwargs. Does nothing if the user does not exist."""
    assert session is not None

    user = session.query(db.User).filter(db.User.netid == netid).one()  # errors if no user exists
    for k, v in kwargs.items():
        setattr(user, k, v)

    return True


# TODO: more useful error handling (report a more useful error message)
@db.session_decorator
def delete(netid: str, *, session: Optional[Session] = None) -> Optional[bool]:
    """Attempts to remove a user from the database, removing all related entries and references.
    Does nothing if the user does not exist."""
    assert session is not None

    user = session.query(db.User).filter(db.User.netid == netid).one()  # errors if no user exists

    session.delete(user)
    session.commit()

    return True


# TODO: report more useful errors for these items
@db.session_decorator
def get_user(netid: str, *, session: Optional[Session] = None) -> Optional[str]:
    """Attempts to return a user object from the Users table given the netid of a user."""
    assert session is not None
    return session.query(db.User).filter(db.User.netid == netid).one()


@db.session_decorator
def get_name(netid: str, *, session: Optional[Session] = None) -> Optional[str]:
    """Attempts to return the name of a user."""
    assert session is not None
    return session.query(db.User).filter(db.User.netid == netid).one().name


@db.session_decorator
def get_bio(netid: str, *, session: Optional[Session] = None) -> Optional[str]:
    """Attempts to return the bio of a user."""
    assert session is not None
    return session.query(db.User).filter(db.User.netid == netid).one().bio


@db.session_decorator
def get_level(netid: str, *, session: Optional[Session] = None) -> Optional[str]:
    """Attempts to return the level of a user."""
    assert session is not None
    return session.query(db.User).filter(db.User.netid == netid).one().level


@db.session_decorator
def get_addinfo(netid: str, *, session: Optional[Session] = None) -> Optional[str]:
    """Attempts to return the additional info of a user."""
    assert session is not None
    return session.query(db.User).filter(db.User.netid == netid).one().addinfo
