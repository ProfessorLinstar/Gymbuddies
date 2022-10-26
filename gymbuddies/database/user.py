"""Database API"""
from typing import Optional, Any, List, Dict
from sqlalchemy.orm import Session
from . import db
from . import schedule as db_schedule


# TODO: process kwargs to make sure no extraneous keywords were supplied. Provide defaults if any
# are null
@db.session_decorator(commit=True)
def create(netid: str, *, session: Optional[Session] = None, **kwargs) -> Optional[bool]:
    """Attempts to create a user with netid and a profile provided by **kwargs. Does nothing if the
    user already exists."""
    assert session is not None

    if session.query(db.User).filter(db.User.netid == netid).all():
        raise ValueError("User already exists. Skipping creation.")

    profile: Dict[str, Any] = _default_profile()
    user = db.User()
    _update_user(session, user, **(profile | kwargs))
    setattr(user, "netid", netid)

    session.add(user)

    return True


# TODO: same here: process kwargs
@db.session_decorator(commit=True)
def update(netid: str, *, session: Optional[Session] = None, **kwargs) -> Optional[bool]:
    """Attempts to update the profile information of of a user with netid with the profile provided
    by **kwargs. Does nothing if the user does not exist."""
    assert session is not None

    user: db.User = session.query(db.User).filter(db.User.netid == netid).one()  # errors if no user
    _update_user(session, user, **kwargs)

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


def _update_user(session: Session, user: db.User, /, **kwargs) -> None:
    """Updates the attributes of 'user' according to 'kwargs'. Uses default properties to fill in
    null values."""

    for k, v in ((k, v) for k, v in kwargs.items() if k in db.User.__table__.columns):
        setattr(user, k, v)

    schedule: Optional[List[db.ScheduleStatus]] = kwargs.get("schedule")
    if schedule is None:
        return

    # need to handle case where user row does not yet exist
    # for i, status in enumerate(schedule):
    #     if status == db.ScheduleStatus.UNAVAILABLE:
    #         continue
    #     db_schedule.add_time_status(user.netid, db.TimeBlock(i), status, session=session)


# TODO: more useful error handling (report a more useful error message)
@db.session_decorator(commit=True)
def delete(netid: str, *, session: Optional[Session] = None) -> Optional[bool]:
    """Attempts to remove a user from the database, removing all related entries and references.
    Does nothing if the user does not exist."""
    assert session is not None

    user: db.User = session.query(db.User).filter(db.User.netid == netid).one()  # errors if no user
    session.delete(user)

    return True


# TODO: report more useful errors for these items
@db.session_decorator(commit=False)
def get_users(*criterions, session: Optional[Session] = None) -> Optional[List[db.User]]:
    """Attempts to return a list of all users satisfying a particular criterion."""
    print(db.DATABASE_URL)
    assert session is not None
    return session.query(db.User).filter(*criterions).all()


# TODO: provide debug mode with diagnostics
@db.session_decorator(commit=False)
def get_user(netid: str, *, session: Optional[Session] = None) -> Optional[str]:
    """Attempts to return a user object from the Users table given the netid of a user."""
    assert session is not None
    print(f"querying this user: '{netid}'")
    return session.query(db.User).filter(db.User.netid == netid).one()


@db.session_decorator(commit=False)
def get_name(netid: str, *, session: Optional[Session] = None) -> Optional[str]:
    """Attempts to return the name of a user."""
    assert session is not None
    return session.query(db.User).filter(db.User.netid == netid).one().name


@db.session_decorator(commit=False)
def get_bio(netid: str, *, session: Optional[Session] = None) -> Optional[str]:
    """Attempts to return the bio of a user."""
    assert session is not None
    return session.query(db.User).filter(db.User.netid == netid).one().bio


@db.session_decorator(commit=False)
def get_level(netid: str, *, session: Optional[Session] = None) -> Optional[str]:
    """Attempts to return the level of a user."""
    assert session is not None
    return session.query(db.User).filter(db.User.netid == netid).one().level


@db.session_decorator(commit=False)
def get_addinfo(netid: str, *, session: Optional[Session] = None) -> Optional[str]:
    """Attempts to return the additional info of a user."""
    assert session is not None
    return session.query(db.User).filter(db.User.netid == netid).one().addinfo
