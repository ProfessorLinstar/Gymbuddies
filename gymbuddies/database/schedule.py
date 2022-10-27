"""Database API"""
from typing import List, Optional
from typing import cast
from sqlalchemy import Column
from sqlalchemy import or_
from sqlalchemy.orm import Session
from . import db
from . import user as db_user


@db.session_decorator(commit=False)
def get_schedule(netid: str, *, session: Optional[Session] = None) -> List[int]:
    """Returns a a list of 2016 blocks for a user showing the availability statuses for
    each of these times. Bitwise masking must be used to extract statuses"""
    assert session is not None
    return session.query(db.User).filter(db.User.netid == netid).one().schedule


def _get_block(session: Session, netid: str, time: db.TimeBlock) -> Optional[db.Schedule]:
    """ Helper method for eliminating some repetitive code"""
    return session.query(db.Schedule).filter(db.Schedule.netid == netid,
                                             db.Schedule.timeblock == time).first()


@db.session_decorator(commit=True)
def add_time_status(netid: str,
                    time: db.TimeBlock,
                    status: db.ScheduleStatus,
                    *,
                    session: Optional[Session] = None,
                    user: Optional[db.MappedUser] = None) -> bool:
    """Updates either Availability, Pending, or Matched to be set for a certain time block.
    In the case that the attribute was already set, False is returned. status should
    be a ScheduleStatus enum value"""
    assert session is not None

    # make change to the Schedule Table
    block = _get_block(session, netid, time)
    if block is None:
        block = db.Schedule(timeblock=time, netid=netid)
        session.add(block)
    else:
        if block.status & status:
            return False

    block.matched = cast(Column, db.ScheduleStatus.MATCHED & status)
    block.pending = cast(Column, db.ScheduleStatus.PENDING & status)
    block.available = cast(Column, db.ScheduleStatus.AVAILABLE & status)

    # make change to the User Table
    if user is None:
        user = db_user.get_user(netid, session=session)
    if user is None:
        raise db_user.UserNotFound(netid=netid)

    user.schedule[time] |= status

    return True


@db.session_decorator(commit=False)
def get_match_schedule(netid: str, *, session: Optional[Session] = None) -> List[int]:
    """ Return schedule specifially showing time of matches"""
    assert session is not None

    rows = session.query(db.Schedule).filter(db.Schedule.netid == netid).filter(
        or_(db.Schedule.status == 1, db.Schedule.status == 3, db.Schedule.status == 5,
            db.Schedule.status == 7)).order_by(db.Schedule.timeblock).all()
    return [row.timeblock for row in rows]


@db.session_decorator(commit=False)
def get_pending_schedule(netid: str, *, session: Optional[Session] = None) -> List[int]:
    """ Return schedule specifially showing time of pending matches"""
    assert session is not None

    rows = session.query(db.Schedule).filter(db.Schedule.netid == netid).filter(
        or_(db.Schedule.status == 2, db.Schedule.status == 3, db.Schedule.status == 6,
            db.Schedule.status == 7)).order_by(db.Schedule.timeblock).all()
    return [row.timeblock for row in rows]


@db.session_decorator(commit=False)
def get_available_schedule(netid: str, *, session: Optional[Session] = None) -> List[int]:
    """Return schedule specifically showing time of availabilities"""
    assert session is not None

    rows = session.query(db.Schedule).filter(db.Schedule.netid == netid).filter(
        db.Schedule.status >= 4, db.Schedule.status <= 7).order_by(db.Schedule.timeblock).all()
    return [row.timeblock for row in rows]


@db.session_decorator(commit=False)
def get_available_users(timeblock: int, *, session: Optional[Session] = None) -> List[str]:
    """Return list of users showing available users at a certain timeframe"""
    assert session is not None

    rows = session.query(db.Schedule).filter(db.Schedule.timeblock == timeblock).order_by(
        db.Schedule.netid).all()
    return [row.netid for row in rows]
