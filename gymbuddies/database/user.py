"""Database API"""
from datetime import datetime, timezone
from typing import Optional, Any, List, Dict, Tuple
from sqlalchemy import Column
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from . import db
from . import schedule as db_schedule
from . import request as db_request


class UserAlreadyBlocked(Exception):
    """Exception raised in API call if attempting to block a user with a netid who is already
    blocked."""

    delnetid: str

    def __init__(self, delnetid: str):
        self.delnetid = delnetid
        super().__init__(f"User with netid '{delnetid}' already blocked.")


class UserNotBlocked(Exception):
    """Exception raised in API call if attempting to create a user with a netid already in the
    database."""

    delnetid: str

    def __init__(self, delnetid: str):
        self.delnetid = delnetid
        super().__init__(f"User with netid '{delnetid}' already blocked.")

class UserBlockedIsSelf(Exception):
    """Exception raise in API call if attempting to block oneself."""

    netid: str

    def __init__(self, netid: str):
        self.netid = netid
        super().__init__(f"User with netid '{netid}' cannot block themself.")

class UserAlreadyExists(Exception):
    """Exception raised in API call if attempting to create a user with a netid already in the
    database."""

    netid: str

    def __init__(self, netid: str):
        self.netid = netid
        super().__init__(f"User with netid '{netid}' already exists.")


class InvalidNetid(Exception):
    """Exception raised in API call if user required but not found in database."""

    def __init__(self):
        super().__init__("Invalid netid. Netid must consist of 1 or more alphanumeric characters.")


class UserNotFound(Exception):
    """Exception raised in API call if user required but not found in database."""

    netid: str

    def __init__(self, netid: str):
        self.netid = netid
        super().__init__(f"User with netid '{netid}' not found in the database.")


@db.session_decorator(commit=True)
def create(netid: str, *, session: Optional[Session] = None, **kwargs) -> None:
    """Attempts to create a user with netid and a profile provided by **kwargs. Does nothing if the
    user already exists."""
    assert session is not None

    if exists(netid, session=session):
        raise UserAlreadyExists(netid)

    if not netid:
        raise InvalidNetid

    profile: Dict[str, Any] = _default_profile()
    user = db.User(netid=netid)
    _update_user(session, user, **(profile | kwargs))
    session.add(user)


@db.session_decorator(commit=True)
def update(netid: str,
           *,
           session: Optional[Session] = None,
           update_schedule: bool = True,
           **kwargs) -> None:
    """Attempts to update the profile information of of a user with netid with the profile provided
    by **kwargs. Does nothing if the user does not exist."""
    assert session is not None
    _update_user(session,
                 get_user(netid, session=session),
                 update_schedule=update_schedule,
                 **kwargs)


def _default_profile() -> Dict[str, Any]:
    """Returns a default user profile configuration. Keys are the attribute names of db.User, and
    values are the default values."""
    return {
        "name":
            "",
        "contact":
            "",
        "level":
            db.Level.BEGINNER,
        "levelpreference":
            db.LevelPreference.ALL,
        "bio":
            "",
        "addinfo":
            "",
        "interests":
            db.get_interests_dict(
                cardio=True,
                upper=True,
                lower=True,
                losing=True,
                gaining=True,
            ),
        "schedule": [db.ScheduleStatus.UNAVAILABLE] * db.NUM_WEEK_BLOCKS,
        "open":
            False,
        "gender":
            db.Gender.NONBINARY,
        "okmale":
            True,
        "okfemale":
            True,
        "okbinary":
            True,
        "settings": {},
        "blocked": []
    }


def _update_user(session: Session,
                 user: db.MappedUser,
                 /,
                 update_schedule: bool = True,
                 **kwargs) -> None:
    """Updates the attributes of 'user' according to 'kwargs'. """
    assert "netid" not in kwargs and "lastupdated" not in kwargs

    print("_update_user: using these kwargs: ", kwargs)
    print("columns:", db.User.__table__.columns)
    for k, v in ((k, v) for k, v in kwargs.items() if k in db.User.__table__.columns):
        print("updating this: ", k, v)
        setattr(user, k, v)

    def postaction():
        user.lastupdated = datetime.now(timezone.utc)
        print(f"postaction for user {user.netid}:", user.lastupdated)

    session.info["postactions"].append(postaction)
    # user.lastupdated = datetime.now(timezone.utc)

    if user.lastupdated is not None:
        print("user.lastupdated:", user.lastupdated.timestamp())

    if update_schedule and kwargs.get("schedule") is not None:
        db_schedule.update_schedule(user.netid, user.schedule, session=session, update_user=False)


@db.session_decorator(commit=True)
def delete(netid: str, *, session: Optional[Session] = None) -> None:
    """Attempts to remove a user from the database, removing all related entries and references.
    Does nothing if the user does not exist."""
    assert session is not None

    db_request.delete_all(netid)
    db_schedule.update_schedule(netid, [db.ScheduleStatus.UNAVAILABLE] * db.NUM_WEEK_BLOCKS,
                                session=session)
    session.delete(get_user(netid, session=session))


@db.session_decorator(commit=False)
def get_users(*criterions, session: Optional[Session] = None) -> List[db.MappedUser]:
    """Attempts to return a list of all users satisfying a particular criterion."""
    assert session is not None
    return session.query(db.User).filter(*criterions).all()


@db.session_decorator(commit=False)
def get_rand_users(number: int,
                   netid: str,
                   session: Optional[Session] = None) -> List[db.MappedUser]:
    """Attempts to return a <number> random sample of users, from which <userid> is not a user"""
    assert session is not None
    rows = session.query(db.User).filter(db.User.netid != netid).order_by(func.random()).all()
    if len(rows) <= number:
        return rows
    return rows[0:number]


@db.session_decorator(commit=False)
def get_user(netid: str, *, session: Optional[Session] = None) -> db.MappedUser:
    """Attempts to return a user object from the Users table given the netid of a user. If the user
    does not exist, raises an exception."""
    assert session is not None
    return _get(session, netid, (db.User,))


@db.session_decorator(commit=False)
def exists(netid: str, *, session: Optional[Session] = None) -> bool:
    """Checks if the database has a user object in the Users table with the given user netid. If the
    user does not exist, returns None."""
    assert session is not None
    return session.query(db.User.netid).filter(db.User.netid == netid).scalar() is not None


def _get(session: Session, netid: str, entities: Tuple[Column, ...]) -> Any:
    query = session.query(*entities).filter(db.User.netid == netid).scalar()
    if query is None:
        raise UserNotFound(netid)
    return query


def _get_column(session: Session, netid: str, column: Column) -> Any:
    return _get(session, netid, (column,))


@db.session_decorator(commit=False)
def get_name(netid: str, *, session: Optional[Session] = None) -> str:
    """Attempts to return the name of a user with netid 'netid'. Raises an error if the user does
    not exist."""
    assert session is not None
    return _get_column(session, netid, db.User.name)


@db.session_decorator(commit=False)
def get_contact(netid: str, *, session: Optional[Session] = None) -> str:
    """Attempts to return the additional info of a user with netid 'netid'. Raises an error if the
    user does not exist."""
    assert session is not None
    return _get_column(session, netid, db.User.contact)


@db.session_decorator(commit=False)
def get_level(netid: str, *, session: Optional[Session] = None) -> db.Level:
    """Attempts to return the level of a user with netid 'netid'. Raises an error if the user does
    not exist."""
    assert session is not None
    return db.Level(_get_column(session, netid, db.User.level))


@db.session_decorator(commit=False)
def get_level_str(netid: str, *, session: Optional[Session] = None) -> str:
    """Attempts to return the level of a user as a string. Raises an error if the user does not
    exist."""
    assert session is not None
    return db.Level(_get_column(session, netid, db.User.level)).to_readable()


@db.session_decorator(commit=False)
def get_bio(netid: str, *, session: Optional[Session] = None) -> str:
    """Attempts to return the bio of a user with netid 'netid'. Raises an error if the user does not
    exist."""
    assert session is not None
    return _get_column(session, netid, db.User.bio)


@db.session_decorator(commit=False)
def get_levelpreference(netid: str, *, session: Optional[Session] = None) -> int:
    """Attemps to return the level preference of a user."""
    assert session is not None
    return _get_column(session, netid, db.User.levelpreference)


@db.session_decorator(commit=False)
def get_addinfo(netid: str, *, session: Optional[Session] = None) -> str:
    """Attempts to return the additional info of a user with netid 'netid'. Raises an error if the
    user does not exist."""
    assert session is not None
    return _get_column(session, netid, db.User.addinfo)


@db.session_decorator(commit=False)
def get_interests(netid: str, *, session: Optional[Session] = None) -> Dict[str, Any]:
    """Attempts to return the interests of a user with netid 'netid'. Raises an error if the user
    does not exist."""
    assert session is not None
    return _get_column(session, netid, db.User.interests)


@db.session_decorator(commit=False)
def get_interests_string(netid: str, *, session: Optional[Session] = None) -> str:
    """Attempts to return the interests of a user with netid 'netid' as comma separated string.
    Raises an error if the user does not exist """
    assert session is not None
    interests = _get_column(session, netid, db.User.interests)
    return ", ".join((k for k, v in interests.items() if v))


@db.session_decorator(commit=False)
def get_schedule(netid: str, *, session: Optional[Session] = None) -> List[int]:
    """Attempts to return the schedule of a user with netid 'netid'. Raises an error if the user
    does not exist."""
    assert session is not None
    return _get_column(session, netid, db.User.schedule)


@db.session_decorator(commit=False)
def get_open(netid: str, *, session: Optional[Session] = None) -> bool:
    """Attempts to return whether or not a user with netid 'netid' is open for matching. Raises an
    error if the user does not exist."""
    assert session is not None
    return _get_column(session, netid, db.User.open)


@db.session_decorator(commit=False)
def get_gender(netid: str, *, session: Optional[Session] = None) -> int:
    """Attempts to return whether or not a user with netid 'netid' is open for matching. Raises an
    error if the user does not exist."""
    assert session is not None
    return _get_column(session, netid, db.User.gender)


@db.session_decorator(commit=False)
def get_okmale(netid: str, *, session: Optional[Session] = None) -> bool:
    """Attempts to return whether or not a user with netid 'netid' is ok matching male. Raises an
    error if the user does not exist."""
    assert session is not None
    return _get_column(session, netid, db.User.okmale)


@db.session_decorator(commit=False)
def get_okfemale(netid: str, *, session: Optional[Session] = None) -> bool:
    """Attempts to return whether or not a user with netid 'netid' is ok matching female. Raises an
    error if the user does not exist."""
    assert session is not None
    return _get_column(session, netid, db.User.okfemale)


@db.session_decorator(commit=False)
def get_okbinary(netid: str, *, session: Optional[Session] = None) -> bool:
    """Attempts to return whether or not a user with netid 'netid' is ok matching nonbinary.
    Raises an error if the user does not exist."""
    assert session is not None
    return _get_column(session, netid, db.User.okbinary)


@db.session_decorator(commit=False)
def get_settings(netid: str, *, session: Optional[Session] = None) -> Dict[str, Any]:
    """Attempts to return the settings of a user with netid 'netid'. Raises an error if the user
    does not exist."""
    assert session is not None
    return _get_column(session, netid, db.User.settings)


@db.session_decorator(commit=False)
def get_lastupdated(netid: str, *, session: Optional[Session] = None) -> datetime:
    """Attempts to return the lastupdated of a user with netid 'netid'. Raises an error if the user
    does not exist."""
    assert session is not None
    return _get_column(session, netid, db.User.lastupdated)


@db.session_decorator(commit=False)
def get_blocked(netid: str, *, session: Optional[Session] = None) -> List[str]:
    """returns list of all users who have been blocked by this user"""
    assert session is not None
    return _get_column(session, netid, db.User.blocked)


@db.session_decorator(commit=False)
def is_blocked(netid: str, delnetid: str, *, session: Optional[Session] = None) -> bool:
    """returns whether this user and the other user are blocked"""
    assert session is not None
    return delnetid in _get_column(session, netid, db.User.blocked)


@db.session_decorator(commit=True)
def block_user(netid: str, delnetid: str, *, session: Optional[Session] = None) -> None:
    """blocks this user. They can no longer appear on find a buddy and cannot send requests to you,
    nor accept request"""
    assert session is not None
    user = get_user(netid, session=session)

    if delnetid == netid:
        raise UserBlockedIsSelf(netid)
    if delnetid in user.blocked:
        raise UserAlreadyBlocked(delnetid)

    deluser = get_user(delnetid, session=session)
    request = db_request.get_active_pair(netid, delnetid)
    if request is not None:
        db_request._deactivate(session, request)

    user.blocked.append(delnetid)
    _update_user(session, user) # trigger update of lastupdated
    _update_user(session, deluser)


@db.session_decorator(commit=True)
def unblock_user(netid: str, delnetid: str, *, session: Optional[Session] = None) -> None:
    """unblocks this user. Now they should be able to appear on find a buddy, rend requests to you,
    and accept requests"""
    assert session is not None
    user = get_user(netid, session=session)

    if delnetid not in user.blocked:
        raise UserNotBlocked(delnetid)

    user.blocked.remove(delnetid)
    _update_user(session, user) # trigger update of lastupdated
    _update_user(session, get_user(delnetid, session=session))


@db.session_decorator(commit=True)
def recieve_notification_on(netid: str, *, session: Optional[Session] = None) -> None:
    """turn on notifications for this user"""
    assert session is not None
    user = get_user(netid, session=session)
    user.settings["notifications"] = True


@db.session_decorator(commit=True)
def recieve_notification_off(netid: str, *, session: Optional[Session] = None) -> None:
    """turn off notifications for this user"""
    assert session is not None
    user = get_user(netid, session=session)
    user.settings["notifications"] = False


@db.session_decorator(commit=False)
def get_notification_status(netid: str, *, session: Optional[Session] = None) -> None:
    """get the notification status for this user. on or off"""
    assert session is not None
    user = get_user(netid, session=session)
    return user.settings.get("notifications", False)
