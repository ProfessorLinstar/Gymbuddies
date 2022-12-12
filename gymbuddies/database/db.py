"""Database schema and data class enumerations."""

import functools
import os
import random
import sys
import traceback
import time

from datetime import datetime, timezone
from enum import Enum, IntFlag
from typing import Tuple, Callable, ParamSpec, TypeVar, Dict, List, Any

from sqlalchemy import Column, String, Integer, Boolean, PickleType
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableList, MutableDict
from sqlalchemy.orm import Session

P = ParamSpec('P')
R = TypeVar('R')

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    raise ValueError("Database URL must be provided with the 'DATABASE_URL' environment variable.")

BASE = declarative_base()

TIMEOUT = 0.01  # seconds
RETRY_NUM = 10

BLOCK_LENGTH = 5  # minutes
NUM_HOUR_BLOCKS = 60 // BLOCK_LENGTH
NUM_DAY_BLOCKS = 24 * NUM_HOUR_BLOCKS
NUM_WEEK_BLOCKS = 7 * NUM_DAY_BLOCKS
DAY_NAMES = ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")

engine = create_engine(DATABASE_URL, execution_options={"isolation_level": "SERIALIZABLE"})


def session_decorator(*, commit: bool) -> Callable[[Callable[P, R]], Callable[P, R]]:
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
    function decorated by '@session_decorator(commit=True)'. This prevents a single API call from
    behaving like a single transaction, breaking the serializability guarantees of this API. Because
    of this, it is recommended that any such function use 'commit=True' instead of manually calling
    'session.commit'."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if "session" in kwargs:  # A session can be provided manually
                return func(*args, **kwargs)

            for retry in range(RETRY_NUM + 1):
                try:
                    with Session(engine) as session:
                        session.info["postactions"] = []
                        kwargs["session"] = session
                        result = func(*args, **kwargs)

                        if commit:
                            print("performing postactions: ", session.info["postactions"])
                            for post_action in session.info["postactions"]:
                                post_action()
                            session.commit()
                            print("commit completed at", datetime.now(timezone.utc))
                        return result

                except OperationalError as ex:
                    if retry == RETRY_NUM:
                        raise ex
                    time.sleep(TIMEOUT * (1 + random.random()) * 2**retry)
                    traceback.print_exception(ex, file=sys.stderr)
                    print(f"session_decorator: retrying {func.__name__}{args}{kwargs} for the {retry+1}th time.")

            raise RuntimeError("No result.")

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
    ScheduleStatus has 4 flags:
        0 - UNAVAILABLE: user indicated that they are not available at this time
        1 - AVAILABLE:   user indicated available at this time
        2 - PENDING:     user is awaiting a request at this time
        4 - MATCHED:     user is already matched with someone at this time
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
    Gender.MALE: "Male",
    Gender.FEMALE: "Female",
    Gender.NONBINARY: "Nonbinary",
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
        to Sunday, ..., Saturday. 'time' is an integer from 0-NUM_DAY_BLOCKS, corresponding to
        00:00-00:05, ..., 23:55-24:00."""
        return cls(day * NUM_DAY_BLOCKS + time)

    def to_readable(self, time_only: bool = False) -> str:
        """Converts a TimeBlock to the human readable format 'Day, HH:MM XM'. If 'end' is True,
        then returns the end time; otherwise, returns the start time of this block."""

        day, time = self.day_time()
        d = datetime.strptime(
            f"{time // NUM_HOUR_BLOCKS}:{BLOCK_LENGTH * (time % NUM_HOUR_BLOCKS)}", "%H:%M")

        return ("" if time_only else f"{DAY_NAMES[day]} ") + d.strftime('%-I:%M%p')

    def time_str(self) -> str:
        """Converts the time of day for a TimeBlock to a datetime."""
        _, time = self.day_time()
        return datetime.strptime(
            f"{time // NUM_HOUR_BLOCKS}:{BLOCK_LENGTH * (time % NUM_HOUR_BLOCKS)}",
            "%H:%M").strftime("%H:%M")

    def day_time(self) -> Tuple[int, int]:
        """Converts a TimeBlock to a (day, time) tuple. 'day' is an integer from 0-6, corresponding
        to Sunday, ..., Saturday. 'time' is an integer from 0-NUM_DAY_BLOCKS, corresponding to
        00:00-00:05, ..., 23:55-24:00."""
        return divmod(self, NUM_DAY_BLOCKS)


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
    Level.BEGINNER: "Beginner",
    Level.INTERMEDIATE: "Intermediate",
    Level.ADVANCED: "Advanced",
}


# note: use this function to get interests dict when adding user to db for first time
def get_interests_dict(cardio=False,
                       upper=False,
                       lower=False,
                       losing=False,
                       gaining=False) -> Dict[str, bool]:
    """Returns an interests hash table. Set interested parameters as True"""
    interests = {}
    interests["Cardiovascular Fitness"] = cardio
    interests["Upper Body"] = upper
    interests["Lower Body"] = lower
    interests["Losing Weight"] = losing
    interests["Gaining Mass"] = gaining
    return interests


# TODO: implement this function the same as above
def get_settings_dict():
    """Returns a settings hash table."""
    return None


def interests_to_readable(interests: Dict[str, bool]):
    """Converts an interests dictionary to a readable format."""
    return ", ".join(k for k, v in interests.items() if v)


def schedule_to_events(schedule: List[int] | List[ScheduleStatus]) -> List[List[TimeBlock]]:
    """Converts a schedule into a string representation as a comma separated list of events. Events
    are in the format (start, end), where start and end are timeblocks, and start is inclusive while
    end is exclusive."""
    assert len(schedule) == NUM_WEEK_BLOCKS

    blocks: List[List[TimeBlock]] = [[]]
    for t, status in enumerate(schedule):
        if (not (status & ScheduleStatus.AVAILABLE) or t % NUM_DAY_BLOCKS == 0) and blocks[-1]:
            blocks[-1].append(TimeBlock(t))
            blocks.append([])
        if status & ScheduleStatus.AVAILABLE and not blocks[-1]:
            blocks[-1].append(TimeBlock(t))

    if blocks[-1]:
        blocks[-1].append(TimeBlock(len(schedule)))
    else:
        blocks.pop()

    return blocks


def schedule_to_matchevents(schedule: List[int],
                            match_names: List[str]) -> List[List[Tuple[TimeBlock, str]]]:
    """Converts a schedule into a string representation as a comma separated list of events. Events
    are in the format (start, end), where start and end are timeblocks, and start is inclusive while
    end is exclusive."""
    assert len(schedule) == NUM_WEEK_BLOCKS

    blocks: List[List[Tuple[TimeBlock, str]]] = [[]]
    for t, status in enumerate(schedule):
        # print(matchNames[t])
        if blocks[-1] and (status != ScheduleStatus.AVAILABLE or t % NUM_DAY_BLOCKS == 0 or
                           match_names[t]):
            blocks[-1].append((TimeBlock(t), blocks[-1][0][1]))
            blocks.append([])
        if status == ScheduleStatus.AVAILABLE and not blocks[-1]:
            blocks[-1].append((TimeBlock(t), match_names[t]))

    if blocks[-1]:
        blocks[-1].append((TimeBlock(len(schedule)), match_names[-1]))
    else:
        blocks.pop()

    return blocks


def schedule_to_modifyevents(schedule: List[int],
                             requests: List[int]) -> List[List[Tuple[TimeBlock, int]]]:
    """Converts a schedule into a string representation as a comma separated list of events. Events
    are in the format (start, end), where start and end are timeblocks, and start is inclusive while
    end is exclusive."""
    assert len(schedule) == NUM_WEEK_BLOCKS

    blocks: List[List[Tuple[TimeBlock, int]]] = [[]]
    for t, status in enumerate(schedule):
        if blocks[-1] and (status != ScheduleStatus.AVAILABLE or t % NUM_DAY_BLOCKS == 0 or
                           blocks[-1][0][1] != requests[t]):
            blocks[-1].append((TimeBlock(t), blocks[-1][0][1]))
            blocks.append([])
        if status == ScheduleStatus.AVAILABLE and not blocks[-1]:
            blocks[-1].append((TimeBlock(t), requests[t]))

    if blocks[-1]:
        blocks[-1].append((TimeBlock(len(schedule)), requests[-1]))
    else:
        blocks.pop()

    return blocks


def schedule_to_readable(schedule: List[ScheduleStatus] | List[int]) -> List[str]:
    """Converts schedule into a list of readable strings."""
    return [
        f"{s.to_readable()}-{e.to_readable(time_only=True)}"
        for s, e in schedule_to_events(schedule)
    ]


# TODO limit the size of columns in the database
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

    settings = Column(MutableDict.as_mutable(PickleType))  # Notification and account settings
    lastupdated = Column(PickleType)  # timestamp for last related database update

    blocked = Column(
        MutableList.as_mutable(PickleType))  # list of users who are blocked for this user


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
    lastupdated: datetime

    blocked: List[str]


class Request(BASE):
    """Requests table. Includes requests that are pending, rejected, or finalized (i.e. completed
    matches)."""
    __tablename__ = "requests"

    requestid = Column(Integer, primary_key=True)  # unique auto-incrementing request transaction id
    srcnetid = Column(String)  # user who makes the request
    destnetid = Column(String)  # user who receives the request
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
