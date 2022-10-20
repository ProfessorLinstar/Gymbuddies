"""Tests database initialization."""
from sqlalchemy import Column, String, Integer, Boolean, PickleType
from sqlalchemy.ext.declarative import declarative_base

DB_STRING = "postgresql://gymbuddies_database_user:jkOWdkfbNDIDlTkT9PXRnEdAp6Z6fRMQ@dpg-cd8lg7mn6mpnkgibbc2g-a.ohio-postgres.render.com/gymbuddies_database"  # pylint: disable=line-too-long
BASE = declarative_base()
NUM_TIME_BLOCKS = 2016


class User(BASE):
    """Users database"""
    __tablename__ = "users"

    userid = Column(Integer, primary_key=True)  # unique user id
    name = Column(String)  # alias displayed in system, e.g. mrpieguy
    level = Column(Integer)  # level of experience (e.g. beginner, intermediate, expert)
    addinfo = Column(String)  # additional info in user profile

    interests = Column(PickleType)  # Integer indicating interest (will have a column for each kind of interest)

    schedule = Column(String)  # a sequence of 2016 characters indicating status for each time block
    open = Column(Boolean)  # open for matching


class Request(BASE):
    """Requests table"""
    __tablename__ = "requests"

    requestid = Column(Integer, primary_key=True)  # unique request transaction id
    srcuserid = Column(Integer)  # user who makes the request
    destuserid = Column(Integer)  # user who recieves the request
    timestamp = Column(String)  # timestamp when the request was made
    status = Column(String)  # status of the request (e.g. 0 = successful, 1 = in progress, 2 = rejected)
    schedule = Column(String)  # 2016-character schedule sequence (same format as user.schedule)


class Matches(BASE):
    """Matches table"""
    __tablename__ = "matches"

    # same structure as requests database
    # when a request is finalized, it is moved from the requests database into the matches database

    matchid = Column(Integer, primary_key=True)
    srcuserid = Column(Integer)
    destuserid = Column(Integer)
    status = Column(String)
    schedule = Column(String)


class Schedule(BASE):
    """Schedule table"""
    __tablename__ = "schedule"

    time = Column(Integer, primary_key=True)  # a particular time block (5-minute granularity => 2016 blocks)
    userid = Column(Integer, primary_key=True)  # userid for a particular time block
    status = Column(String)  # status of userid for this time block (e.g. 0 = available, 1 = already matched)
