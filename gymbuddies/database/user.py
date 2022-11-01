"""Database API"""
from typing import Optional, Any, List, Dict, Tuple
from sqlalchemy import Column
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from . import db
from . import schedule as db_schedule


class UserNotFound(Exception):
    """Exception raised in API call if user required but not found in database."""

    def __init__(self, netid: str):
        super().__init__(f"User with netid '{netid}' not found in the database.")


@db.session_decorator(commit=True)
def create(netid: str, *, session: Optional[Session] = None, **kwargs) -> bool:
    """Attempts to create a user with netid and a profile provided by **kwargs. Does nothing if the
    user already exists."""
    assert session is not None

    if has_user(netid, session=session):
        raise ValueError("User already exists. Skipping creation.")

    profile: Dict[str, Any] = _default_profile()
    user = db.User()
    _update_user(session, user, **(profile | kwargs | {"netid": netid}))
    session.add(user)

    return True


@db.session_decorator(commit=True)
def update(netid: str, *, session: Optional[Session] = None, **kwargs) -> bool:
    """Attempts to update the profile information of of a user with netid with the profile provided
    by **kwargs. Does nothing if the user does not exist."""
    assert session is not None
    _update_user(session, get_user(netid, session=session), **kwargs)
    return True


def _default_profile() -> Dict[str, Any]:
    """Returns a default user profile configuration. Keys are the attribute names of db.User, and
    values are the default values."""
    return {
        "netid": "",
        "name": "",
        "contact": "",
        "level": "0",
        "addinfo": "",
        "interests": {},
        "schedule": [db.ScheduleStatus.UNAVAILABLE] * db.NUM_WEEK_BLOCKS,
        "open": False,
        "settings": {},
    }


def _update_user(session: Session, user: db.MappedUser, /, **kwargs) -> None:
    """Updates the attributes of 'user' according to 'kwargs'. """

    for k, v in ((k, v) for k, v in kwargs.items() if k in db.User.__table__.columns):
        setattr(user, k, v)

    if kwargs.get("schedule") is not None:
        db_schedule.update_schedule(user.netid, user.schedule, session=session, update_user=False)


@db.session_decorator(commit=True)
def delete(netid: str, *, session: Optional[Session] = None) -> bool:
    """Attempts to remove a user from the database, removing all related entries and references.
    Does nothing if the user does not exist."""
    assert session is not None

    user = get_user(netid, session=session)
    session.delete(user)

    return True


@db.session_decorator(commit=False)
def get_users(*criterions, session: Optional[Session] = None) -> Optional[List[db.MappedUser]]:
    """Attempts to return a list of all users satisfying a particular criterion."""
    assert session is not None
    return session.query(db.User).filter(*criterions).all()


@db.session_decorator(commit=False)
def get_rand_users(number: int,
                   netid: str,
                   session: Optional[Session] = None) -> Optional[List[db.MappedUser]]:
    """Attempts to return a <number> random sample of users, from which <userid> is not a user"""
    assert session is not None
    rows = session.query(db.User).filter(db.User.netid != netid).order_by(func.random()).all()
    if len(rows) <= 10:
        return rows
    return rows[0:number]


@db.session_decorator(commit=False)
def get_user(netid: str, *, session: Optional[Session] = None) -> db.MappedUser:
    """Attempts to return a user object from the Users table given the netid of a user. If the user
    does not exist, raises an exception."""
    assert session is not None

    return _get(session, netid)


@db.session_decorator(commit=False)
def has_user(netid: str, *, session: Optional[Session] = None) -> bool:
    """Checks if the database has a user object in the Users table with the given user netid. If the
    user does not exist, returns None."""
    assert session is not None
    return session.query(db.User.netid).filter(db.User.netid == netid).scalar() is not None


def _get(session: Session, netid: str, entities: Tuple[Column, ...] = (db.User,)) -> Any:
    query = session.query(*entities).filter(db.User.netid == netid).scalar()
    if query is None:
        raise UserNotFound(netid)
    return query


def _get_column(session: Session, netid: str, column: Column) -> Any:
    return _get(session, netid, (column,))[0]


@db.session_decorator(commit=False)
def get_name(netid: str, *, session: Optional[Session] = None) -> Optional[str]:
    """Attempts to return the name of a user with netid 'netid'. Raises an error if the user does
    not exist."""
    assert session is not None
    return _get_column(session, netid, db.User.name)


@db.session_decorator(commit=False)
def get_contact(netid: str, *, session: Optional[Session] = None) -> Optional[str]:
    """Attempts to return the additional info of a user with netid 'netid'. Raises an error if the
    user does not exist."""
    assert session is not None
    return _get_column(session, netid, db.User.contact)


@db.session_decorator(commit=False)
def get_level(netid: str, *, session: Optional[Session] = None) -> Optional[db.Level]:
    """Attempts to return the level of a user with netid 'netid'. Raises an error if the user does
    not exist."""
    assert session is not None
    return db.Level(_get_column(session, netid, db.User.level))


@db.session_decorator(commit=False)
def get_level_str(netid: str, *, session: Optional[Session] = None) -> Optional[str]:
    """Attempts to return the level of a user as a string. Raises an error if the user does not
    exist."""
    assert session is not None
    return db.Level(_get_column(session, netid, db.User.level)).to_readable()


@db.session_decorator(commit=False)
def get_bio(netid: str, *, session: Optional[Session] = None) -> Optional[str]:
    """Attempts to return the bio of a user with netid 'netid'. Raises an error if the user does not
    exist."""
    assert session is not None
    return _get_column(session, netid, db.User.bio)


@db.session_decorator(commit=False)
def get_level_preference(netid: str, *, session: Optional[Session] = None) -> Optional[int]:
    """Attemps to return the level preference of a user."""
    assert session is not None
    return _get_column(session, netid, db.User.levelpreference)


@db.session_decorator(commit=False)
def get_addinfo(netid: str, *, session: Optional[Session] = None) -> Optional[str]:
    """Attempts to return the additional info of a user with netid 'netid'. Raises an error if the
    user does not exist."""
    assert session is not None
    return _get_column(session, netid, db.User.addinfo)


@db.session_decorator(commit=False)
def get_interests(netid: str, *, session: Optional[Session] = None) -> Optional[Dict[str, Any]]:
    """Attempts to return the interests of a user with netid 'netid'. Raises an error if the user
    does not exist."""
    assert session is not None
    return _get_column(session, netid, db.User.interests)


@db.session_decorator(commit=False)
def get_schedule(netid: str, *, session: Optional[Session] = None) -> Optional[List[int]]:
    """Attempts to return the schedule of a user with netid 'netid'. Raises an error if the user
    does not exist."""
    assert session is not None
    return _get_column(session, netid, db.User.schedule)


@db.session_decorator(commit=False)
def get_open(netid: str, *, session: Optional[Session] = None) -> Optional[bool]:
    """Attempts to return whether or not a user with netid 'netid' is open for matching. Raises an
    error if the user does not exist."""
    assert session is not None
    return _get_column(session, netid, db.User.open)


@db.session_decorator(commit=False)
def get_settings(netid: str, *, session: Optional[Session] = None) -> Optional[Dict[str, Any]]:
    """Attempts to return the settings of a user with netid 'netid'. Raises an error if the user
    does not exist."""
    assert session is not None
    return _get_column(session, netid, db.User.settings)
