"""Database schema and data class enumerations."""

import calendar
import functools
import os
import sys
import traceback

from datetime import datetime
from enum import Enum, IntFlag
from typing import Tuple, Callable, ParamSpec, TypeVar, Optional, Dict, List, Any

from sqlalchemy import Column, String, Integer, Boolean, PickleType
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Session

P = ParamSpec('P')
R = TypeVar('R')

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    raise ValueError("Database URL must be provided with the 'DATABASE_URL' environment variable.")

BASE = declarative_base()

BLOCK_LENGTH = 5  # minutes
NUM_HOUR_BLOCKS = 60 // BLOCK_LENGTH
NUM_DAY_BLOCKS = 24 * NUM_HOUR_BLOCKS
NUM_WEEK_BLOCKS = 7 * NUM_DAY_BLOCKS

engine = create_engine(DATABASE_URL)


# TODO: return exception to client
def session_decorator(*, commit: bool) -> Callable[[Callable[P, R]], Callable[P, Optional[R]]]:
    """Decorator factory for initializing a connection with the DATABASE_URL and returning a
    session. To use this decoration, a function must have a signature of the form
       func(..., *, session: Session=None, x, y, ..., **kwargs) -> R,
    where T is any type. The 'session' argument must be keyword only, and should be handled by this
    session_decorator. At the beginning of a decorated function, it should assert that 'session' is
    not None. The wrapper will return the result of the function if successful; otherwise, it will
    return None. The wrapper will call 'session.commit' after the function finishes, unless 'commit'
    is False or a 'session' is already provided.

    NOTE: if a function might not require 'session.commit', it is permissible to set 'commit' to
    False, and then call 'session.commit' manually where required. Beware, however, that this may
    result in multiple 'session.commit' calls, if, for instance, this function is called by another
    function decorated by '@session_decorator(commit=True)'. Because of this, it is recommended that
    any such function use 'commit=True' instead of manually calling 'session.commit'."""

    def decorator(func: Callable[P, R]) -> Callable[P, Optional[R]]:

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Optional[R]:
            if "session" in kwargs:  # A session can be provided manually
                return func(*args, **kwargs)  # propogate exception to outer session

            try:

                with Session(engine) as session:
                    kwargs["session"] = session
                    result = func(*args, **kwargs)
                    if commit:
                        session.commit()
                return result

            except Exception:
                traceback.print_exc(file=sys.stderr)

            return None

        return wrapper

    return decorator


class RequestStatus(int, Enum):
    """Request status enumeration. Includes pending, rejected, and finalized requests. Requests that
    become matches have a value of at least RequestStatus.FINALIZED. When reading the a request
    status from the Requests database, it should be cast to a RequestStatus enumeration.
    RequestStatus can have 5 states:
        0 - REJECTED:   request was rejected before finalization
        1 - PENDING:    request is currently pending
        2 - RETURN:     request modified by destination user, and is being returned for confirmation
        3 - FINALIZED:  request has been finalized (match completed)
        4 - TERMINATED: request was finalized, but has been terminated.
    """

    REJECTED = 0
    PENDING = 1
    RETURN = 2
    FINALIZED = 3
    TERMINATED = 4

    def to_readable(self) -> str:
        """Converts a Level to a human readable form."""
        return _REQUESTSTATUS_TO_READABLE_MAP[self]


_REQUESTSTATUS_TO_READABLE_MAP = {
    RequestStatus.REJECTED: "REJECTED",
    RequestStatus.PENDING: "PENDING",
    RequestStatus.RETURN: "RETURN",
    RequestStatus.FINALIZED: "FINALIZED",
    RequestStatus.TERMINATED: "TERMINATED",
}


class ScheduleStatus(IntFlag):
    """Time block status enumeration. Indicates user status in a particular time block.
    ScheduleStatus can have 4 states:
        0 - UNAVAILABLE: user indicated that they are not available at this time
        1 - AVAILABLE:   user indicated available at this time, and no pending or finalized matches
        2 - PENDING:     user indicated available at this time, but is waiting on a request
        3 - MATCHED:     user indicated available at this time, but has already been matched
    """

    UNAVAILABLE = 0
    MATCHED = 1
    PENDING = 2
    AVAILABLE = 4

    @classmethod
    def from_str(cls, status: str) -> "ScheduleStatus":
        """Returns a ScheduleStatus given a status string."""
        return cls(_SCHEDULE_STATUS_FROM_STR_MAP[status])

    def __repr__(self):  # Print self as an integer
        return str(int(self))

    def flags(self):
        """Returns string version of self as an IntFlag"""
        return super().__repr__()


_SCHEDULE_STATUS_FROM_STR_MAP = {
    "unavailable": ScheduleStatus.UNAVAILABLE,
    "matched": ScheduleStatus.MATCHED,
    "pending": ScheduleStatus.PENDING,
    "available": ScheduleStatus.AVAILABLE,
}


class Gender(int, Enum):
    """Integer derivative representing user gender. Provides conversion function to human
    readable forms. Integers map to the following genders
        0: Male
        1: Female
        2: Nonbinary
    """
    MALE = 0
    FEMALE = 1
    NONBINARY = 2

    def to_readable(self) -> str:
        """Converts Gender to a human readable form."""
        return _GENDER_TO_READABLE_MAP[self]


_GENDER_TO_READABLE_MAP = {
    Gender.MALE: "MALE",
    Gender.FEMALE: "FEMALE",
    Gender.NONBINARY: "NONBINARY",
}


class LevelPreference(int, Enum):
    """Integer derivative representing level preference. Provides conversion function to human
    readable forms. Integers map to the following levels preferences.
        0 : Equal
        1 : Lessequal
        2 : GreaterEqual
        3 : All
    """
    EQUAL = 0
    LESSEQUAL = 1
    GREATEREQUAL = 2
    ALL = 3

    def to_readable(self) -> str:
        """Converts a Level to a human readable form."""
        return _LEVEL_PREFERENCE_TO_READABLE_MAP[self]


_LEVEL_PREFERENCE_TO_READABLE_MAP = {
    LevelPreference.EQUAL: "EQUAL",
    LevelPreference.LESSEQUAL: "LESSEQUAL",
    LevelPreference.GREATEREQUAL: "GREATEREQUAL",
    LevelPreference.ALL: "ALL"
}


class TimeBlock(int):
    """Integer derivative representing a particular time block in a schedule. Provides conversion
    functions to human readable times and vice versa."""

    def __new__(cls, index: int):
        return super().__new__(cls, index)

    @classmethod
    def from_daytime(cls, day: int, time: int) -> "TimeBlock":
        """Converts a (day, time) tuple to a TimeBlock. 'day' is an integer from 0-6, corresponding
        to Monday, ..., Sunday. 'time' is an integer from 0-NUM_DAY_BLOCKS, corresponding to
        00:00-00:05, ..., 23:55-24:00."""
        return cls(day * NUM_DAY_BLOCKS + time)

    def to_readable(self) -> str:
        """Converts a TimeBlock to the human readable format 'Day, HH:MM'."""

        day, time = self.day_time()
        d = datetime.strptime(
            f"{time // NUM_HOUR_BLOCKS}:{BLOCK_LENGTH * (time % NUM_HOUR_BLOCKS)}", "%H:%M")

        return f"{calendar.day_name[day]}, {d.strftime('%I:%M %p')}"

    def day_time(self) -> Tuple[int, int]:
        """Converts a TimeBlock to a (day, time) tuple. 'day' is an integer from 0-6, corresponding
        to Monday, ..., Sunday. 'time' is an integer from 0-NUM_DAY_BLOCKS, corresponding to
        00:00-00:05, ..., 23:55-24:00."""
        return self // NUM_DAY_BLOCKS, self % NUM_DAY_BLOCKS


class Level(int, Enum):
    """Integer derivative representing a level. Provides conversion function to human readable
    forms. Integers map to the following levels.
        0 : Beginner
        1 : Intermediate
        2 : Advanced
    """

    BEGINNER = 0
    INTERMEDIATE = 1
    ADVANCED = 2

    def to_readable(self) -> str:
        """Converts a Level to a human readable form."""
        return _LEVEL_TO_READABLE_MAP[self]


_LEVEL_TO_READABLE_MAP = {
    Level.BEGINNER: "BEGINNER",
    Level.INTERMEDIATE: "BEGINNER",
    Level.ADVANCED: "BEGINNER",
}


# note: use this function to get interests dict when adding user to db for first time
def getInterestDict(self, cardio=False, upper=False, lower=False, losing=False,
    gaining=False) -> Dict[str, bool]:
    """Returns an interests hash table. Set interested parameters as True"""
    interests = {}
    interests["cardio"] = cardio
    interests["upper"] = upper
    interests["lower"] = lower
    interests["losing"] = losing
    interests["gaining"] = gaining
    return interests


# TODO: implement this function the same as above
def getSettingsDict():
    return None


class User(BASE):
    """Users database. Maps each netid to their Gymbuddies profile information."""
    __tablename__ = "users"

    netid = Column(String, primary_key=True)  # unique user id
    name = Column(String)  # alias displayed in system, e.g. mrpieguy
    contact = Column(String)  # Contact information
    level = Column(Integer)  # level of experience (e.g. beginner, intermediate, expert)
    levelpreference = Column(Integer)  # preferred level match of user
    bio = Column(String)  # short bio for user
    addinfo = Column(String)  # additional info in user profile
    interests = Column(PickleType)  # Dictionary indicating interests
    schedule = Column(MutableList.as_mutable(PickleType))  # int[2016] with status for each block
    open = Column(Boolean)  # open for matching

    gender = Column(Integer)  # gender of user
    okmale = Column(Boolean)  # is user ok being matched with male users
    okfemale = Column(Boolean)  # is user ok being matched with female users
    okbinary = Column(Boolean)  # is user ok being matched with nonbinary users

    settings = Column(PickleType)  # Notification and account settings


class MappedUser(User):
    """An extension of the User class which casts each column to its respective Python type. Enables
    LSP and static type checkers to infer the correct type of a row."""
    netid: str
    name: str
    contact: str
    level: int
    levelpreference: int
    bio: str
    addinfo: str
    interests: Dict[str, Any]

    schedule: List[int]
    open: bool

    settings: Dict[str, Any]


class Request(BASE):
    """Requests table. Includes requests that are pending, rejected, or finalized (i.e. completed
    matches)."""
    __tablename__ = "requests"

    requestid = Column(Integer, primary_key=True)  # unique auto-incrementing request transaction id
    srcnetid = Column(String)  # user who makes the request
    destnetid = Column(String)  # user who recieves the request
    maketimestamp = Column(PickleType)  # timestamp when the request was made
    finalizedtimestamp = Column(PickleType)  # timestamp when the request was finalized
    deletetimestamp = Column(PickleType)  # timestamp when the request was deleted
    status = Column(Integer)  # status of the request
    schedule = Column(PickleType)  # 2016-character schedule sequence (same format as user.schedule)
    prevrequestid = Column(Integer)  # Id of previous request; 0 if no such request


class MappedRequest(BASE):
    """An extension of the Request class which casts each column to its respective Python type.
    Enables LSP and static type checkers to infer the correct type of a row."""
    __tablename__ = "requests"

    requestid: int
    srcnetid: str
    destnetid: str
    maketimestamp: datetime
    finalizedtimestamp: datetime
    deletetimestamp: datetime
    status: int
    schedule: List[int]


class Schedule(BASE):
    """Schedule table. Maps each 5-minute time block throughout the week to users and statuses."""
    __tablename__ = "schedule"

    timeblock = Column(Integer, primary_key=True)  # a particular time block during the week
    netid = Column(String, primary_key=True)  # netid for a particular time block
    matched = Column(Boolean)  # user has been matched at this time
    pending = Column(Boolean)  # user is awaiting a pending request for this time
    available = Column(Boolean)  # user is available at this time

    def get_status(self) -> ScheduleStatus:
        """Returns this entry as a ScheduleStatus."""
        return ScheduleStatus(self.matched | self.pending | self.available)


class MappedSchedule(BASE):
    """An extension of the Schedule class which casts each column to its respective Python type.
    Enables LSP and static type checkers to infer the correct type of a row."""
    __tablename__ = "schedule"

    timeblock: int
    netid: str
    status: int
    matched: bool
    pending: bool
    available: bool
