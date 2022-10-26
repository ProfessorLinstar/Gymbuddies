"""Database API"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from . import db
from . import user as db_user


@db.session_decorator
def get_schedule(netid: str, *, session: Optional[Session] = None) -> List[int]:
    """Returns a a list of 2016 blocks for a user showing the availability statuses for
    each of these times. Bitwise masking must be used to extract statuses"""
    assert session is not None
    return session.query(db.User).filter(db.User.netid == netid).one().schedule


def schedule_query(session: Session, netid: str, time: db.TimeBlock) -> Optional[db.Schedule]:
    """ Helper method for eliminating some repetitive code"""
    return session.query(db.Schedule).filter(db.Schedule.netid == netid,
                                             db.Schedule.timeblock == time.index).first()


@db.session_decorator
def add_time_status(netid: str,
                    time: db.TimeBlock,
                    which_status: int,
                    *,
                    session: Optional[Session] = None) -> bool:
    """Updates either Availability, Pending, or Matched to be set for a certain time block.
    In the case that the attribute was already set, False is returned. which_status should
    be a ScheduleStatus enum value"""
    assert session is not None

    # make change to the Schedule Table
    row = schedule_query(session, netid, time)
    if row is None:
        row = db.Schedule(timeblock=time.index, netid=netid)
        session.add(row)
    else:
        if row.status & which_status:
            return False
    row.matched = db.ScheduleStatus.MATCHED & which_status
    row.pending = db.ScheduleStatus.PENDING & which_status
    row.available = db.ScheduleStatus.AVAILABLE & which_status

    # make change to the User Table
    row = db_user.get_user(netid, session=session)
    row.schedule[time.index] |= which_status
    session.commit()

    return True



@db.session_decorator
def get_match_schedule(netid: str, *, session: Optional[Session] = None) -> List[int]:
    """ Return schedule specifially showing time of matches"""
    assert session is not None

    rows = session.query(db.Schedule).filter(db.Schedule.netid == netid).filter(
        or_(db.Schedule.status == 1, db.Schedule.status == 3, db.Schedule.status == 5,
            db.Schedule.status == 7)).order_by(db.Schedule.timeblock).all()
    return [row.timeblock for row in rows]


@db.session_decorator
def get_pending_schedule(netid: str, *, session: Optional[Session] = None) -> List[int]:
    """ Return schedule specifially showing time of pending matches"""
    assert session is not None

    rows = session.query(db.Schedule).filter(db.Schedule.netid == netid).filter(
        or_(db.Schedule.status == 2, db.Schedule.status == 3, db.Schedule.status == 6,
            db.Schedule.status == 7)).order_by(db.Schedule.timeblock).all()
    return [row.timeblock for row in rows]


@db.session_decorator
def get_available_schedule(netid: str, *, session: Optional[Session] = None) -> List[int]:
    """Return schedule specifically showing time of availabilities"""
    assert session is not None

    rows = session.query(db.Schedule).filter(db.Schedule.netid == netid).filter(
        db.Schedule.status >= 4, db.Schedule.status <= 7).order_by(db.Schedule.timeblock).all()
    return [row.timeblock for row in rows]


@db.session_decorator
def get_available_users(timeblock: int, *, session: Optional[Session] = None) -> List[str]:
    """Return list of users showing available users at a certain timeframe"""
    assert session is not None

    rows = session.query(db.Schedule).filter(db.Schedule.timeblock == timeblock).order_by(
        db.Schedule.netid).all()
    return [row.netid for row in rows]
