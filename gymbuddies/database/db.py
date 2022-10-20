"""Tests database initialization."""
from enum import Enum
from sqlalchemy import Column, String, Integer, Boolean, PickleType
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "postgresql://gymbuddies_database_user:jkOWdkfbNDIDlTkT9PXRnEdAp6Z6fRMQ@dpg-cd8lg7mn6mpnkgibbc2g-a.ohio-postgres.render.com/gymbuddies_database"  # pylint: disable=line-too-long
BASE = declarative_base()
NUM_TIME_BLOCKS = 2016


class User(BASE):
    """Users database. Maps each userid to their Gymbuddies profile information."""
    __tablename__ = "users"

    userid = Column(Integer, primary_key=True)  # unique user id
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
    srcuserid = Column(Integer)  # user who makes the request
    destuserid = Column(Integer)  # user who recieves the request
    timestamp = Column(String)  # timestamp when the request was made
    status = Column(Integer)  # status of the request (e.g. 0 = successful, 1 = in progress, 2 = rejected)
    schedule = Column(String)  # 2016-character schedule sequence (same format as user.schedule)


class Schedule(BASE):
    """Schedule table. Maps each 5-minute time block throughout the week to users and statuses."""
    __tablename__ = "schedule"

    timeblock = Column(Integer, primary_key=True)  # a particular time block (5-minute granularity => 2016 blocks)
    userid = Column(Integer, primary_key=True)  # userid for a particular time block
    status = Column(String)  # status of userid for this time block (e.g. 0 = available, 1 = already matched)


class RequestStatus(Enum, int):
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

class ScheduleStatus(Enum, str):
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
