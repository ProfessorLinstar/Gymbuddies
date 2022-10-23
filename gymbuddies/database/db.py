"""Database schema and data class enumerations."""

import calendar
import functools
import os
import sys

from datetime import datetime
from dataclasses import dataclass
from enum import Enum, flag, auto
from typing import Tuple, Callable, Any, cast

from sqlalchemy import Column, String, Integer, Boolean, PickleType
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MultableList

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    raise ValueError("Database URL must be provided with the 'DATABASE_URL' environment variable.")
DATABASE_URL = cast(str, DATABASE_URL)

BASE = declarative_base()

BLOCK_LENGTH = 5  # minutes
NUM_HOUR_BLOCKS = 60 // BLOCK_LENGTH
NUM_DAY_BLOCKS = 24 * NUM_HOUR_BLOCKS
NUM_WEEK_BLOCKS = 7 * NUM_DAY_BLOCKS


class User(BASE):
    """Users database. Maps each netid to their Gymbuddies profile information."""
    __tablename__ = "users"

    netid = Column(String, primary_key=True)  # unique user id
    name = Column(String)  # alias displayed in system, e.g. mrpieguy
    contact = Column(String)  # Contact information
    level = Column(Integer)  # level of experience (e.g. beginner, intermediate, expert)
    addinfo = Column(String)  # additional info in user profile
    interests = Column(PickleType)  # Dictionary indicating interests

    schedule = Column(MutableList.as_mutable(PickleType))  # a sequence of 2016 characters indicating status for each time block
    open = Column(Boolean)  # open for matching

    settings = Column(PickleType)  # Notification and account settings


class Request(BASE):
    """Requests table. Includes requests that are pending, rejected, or
    finalized (i.e. completed matches)."""
    __tablename__ = "requests"

    requestid = Column(Integer, primary_key=True)  # unique request transaction id
    srcnetid = Column(String)  # user who makes the request
    destnetid = Column(String)  # user who recieves the request
    timestamp = Column(String)  # timestamp when the request was made
    status = Column(Integer)  # status of the request
    schedule = Column(PickleType)  # 2016-character schedule sequence (same format as user.schedule)


class Schedule(BASE):
    """Schedule table. Maps each 5-minute time block throughout the week to users and statuses."""
    __tablename__ = "schedule"

    timeblock = Column(Integer, primary_key=True)  # a particular time block during the week
    netid = Column(String, primary_key=True)  # netid for a particular time block
    status = Column(Integer)  # status of netid for this time block


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


class ScheduleStatus(Flag):
    """Time block status enumeration. Indicates user status in a particular time block.
    ScheduleStatus can have 4 states:
        0 - UNAVAILABLE: user indicated that they are not available at this time
        1 - AVAILABLE:   user indicated available at this time, and no pending or finalized matches
        2 - PENDING:     user indicated available at this time, but is waiting on a request
        3 - MATCHED:     user indicated available at this time, but has already been matched
    """

    AVAILABLE = 4
    PENDING = 2
    MATCHED = 1

    def __repr__(self):  # Print self as an integer
        return str(int(self))


@dataclass
class TimeBlock:
    """Data class representing a particular time block in a schedule. Provides conversion functions
    to human readable times and vice versa."""
    index: int

    @classmethod
    def from_daytime(cls, day: int, time: int) -> "TimeBlock":
        """Converts a (day, time) tuple to a TimeBlock. 'day' is an integer from 0-6, corresponding
        to Monday, ..., Sunday. 'time' is an integer from 0-NUM_DAY_BLOCKS, corresponding to
        00:00-00:05, ..., 23:55-24:00."""
        return TimeBlock(day * NUM_DAY_BLOCKS + time)

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
        return self.index // NUM_DAY_BLOCKS, self.index % NUM_DAY_BLOCKS


def session_decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    """Initializes a connection with the DATABASE_URL and returns a session. To be use this
       decoration, a function must have a signature of the form
           func(a, b, ..., *args, *, session: Session, x, y, ..., **kwargs) -> Optional[T],
       where T is any type. The 'session' argument must be keyword only, and should be handled by
       this session_decorator. At the beginning of a decorated function, it should assert that
       'session' is not None. The wrapper will return the result of the function if successful;
       otherwise, it will return None."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if "session" in kwargs:
            print(
                f"{sys.argv[0]}: @session_decorator fuctions should not accept a 'session' kwarg.",
                file=sys.stderr)

        try:
            engine = create_engine(DATABASE_URL)
            with Session(engine) as session:
                result = func(*args, session=session, **kwargs)
            engine.dispose()
            return result

        except Exception as ex:
            print(f"{sys.argv[0]}: {ex}", file=sys.stderr)

        return None

    return wrapper
