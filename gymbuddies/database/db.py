"""Database schema and data class enumerations."""
import calendar
import functools
import sys

from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Tuple, Callable, Any

from sqlalchemy import Column, String, Integer, Boolean, PickleType
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "postgresql://gymbuddies_database_user:jkOWdkfbNDIDlTkT9PXRnEdAp6Z6fRMQ@dpg-cd8lg7mn6mpnkgibbc2g-a.ohio-postgres.render.com/gymbuddies_database"  # pylint: disable=line-too-long
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

    schedule = Column(String)  # a sequence of 2016 characters indicating status for each time block
    open = Column(Boolean)  # open for matching

    settings = Column(PickleType)  # Notification and account settings


class Request(BASE):
    """Requests table. Includes requests that are pending, rejected, or finalized (i.e. completed matches)."""
    __tablename__ = "requests"

    requestid = Column(Integer, primary_key=True)  # unique request transaction id
    srcnetid = Column(String)  # user who makes the request
    destnetid = Column(String)  # user who recieves the request
    timestamp = Column(String)  # timestamp when the request was made
    status = Column(Integer)  # status of the request (e.g. 0 = successful, 1 = in progress, 2 = rejected)
    schedule = Column(String)  # 2016-character schedule sequence (same format as user.schedule)


class Schedule(BASE):
    """Schedule table. Maps each 5-minute time block throughout the week to users and statuses."""
    __tablename__ = "schedule"

    timeblock = Column(Integer, primary_key=True)  # a particular time block (5-minute granularity => 2016 blocks)
    netid = Column(String, primary_key=True)  # netid for a particular time block
    status = Column(String)  # status of netid for this time block (e.g. 0 = available, 1 = already matched)


class RequestStatus(int, Enum):
    """Request status enumeration. Includes pending, rejected, and finalized requests. Requests that become matches have a value of at least
    RequestStatus.FINALIZED. When reading the a request status from the Requests database, it should be cast to a RequestStatus enumeration.
    RequestStatus can have 5 states:
        0 - REJECTED:   request was rejected before finalization
        1 - PENDING:    request is currently pending
        2 - RETURN:     request was modified by destination user, and is being returned for confirmation
        3 - FINALIZED:  request has been finalized (match completed)
        4 - TERMINATED: request was finalized, but has been terminated.
    """

    REJECTED = 0
    PENDING = 1
    RETURN = 2
    FINALIZED = 3
    TERMINATED = 4

class ScheduleStatus(str, Enum):
    """Time block status enumeration. Indicates user status in a particular time block. ScheduleStatus can have 4 states:
        0 - UNAVAILABLE: user indicated that they are not available at this time
        1 - AVAILABLE:   user indicated that they are available at this time, and they have no pending or finalized matches here
        2 - PENDING:     user indicated that they are available at this time, but they are waiting on a request for this time
        3 - MATCHED:     user indicated that they are available at this time, but they have already been matched for this time
    """

    UNAVAILABLE = 0
    AVAILABLE = 1
    PENDING = 2
    MATCHED = 3

@dataclass
class TimeBlock:
    """Data class representing a particular time block in a schedule. Provides conversion functions to human readable times and vice versa."""
    index: int

    def to_readable(self) ->  str:
        """Converts index to human readable format: 'Day, HH:MM'"""

        day, time = self.day_time()
        d = datetime.strptime(f"{time // NUM_HOUR_BLOCKS}:{BLOCK_LENGTH * (time % NUM_HOUR_BLOCKS)}", "%H:%M")

        return f"{calendar.day_name[day]}, {d.strftime('%I:%M %p')}"

    def day_time(self) -> Tuple[int, int]:
        """Converts index to (day, timeIndex) tuple."""
        return self.index // NUM_DAY_BLOCKS, self.index % NUM_DAY_BLOCKS

def session_decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    """Initializes a connection with the DATABASE_URL and returns a session. To be use this decoration, a function must have a signature of the form
           func(a, b, ..., *args, /, *, session: Session, x, y, ..., **kwargs) -> Optional[T],
       where T is any type. The 'session' argument must be keyword only, and should be handled by this session_decorator. The wrapper will return the
       result of the function if successful; otherwise, it will return None."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if "session" in kwargs:
            print(f"{sys.argv[0]}: functions decorated with @session_decorator should not accept a 'session' keyword argument.", file=sys.stderr)

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
