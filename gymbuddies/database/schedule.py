"""Database API"""
from typing import List, Optional
from sqlalchemy import Column
from sqlalchemy.orm import Session
from . import db
from . import user as db_user


@db.session_decorator(commit=False)
def get_schedule(netid: str, *, session: Optional[Session] = None) -> List[int]:
    """Returns a a list of 2016 blocks for a user showing the availability statuses for
    each of these times. Bitwise masking must be used to extract statuses"""
    assert session is not None
    return session.query(db.User).filter(db.User.netid == netid).one().schedule


@db.session_decorator(commit=True)
def update_schedule(netid: str,
                    schedule: List[int],
                    *,
                    session: Optional[Session] = None,
                    update_user: bool = True) -> bool:
    """Updates either Availability, Pending, or Matched to be set for a certain time block.
    In the case that the attribute was already set, False is returned. status should
    be a ScheduleStatus enum value"""
    assert session is not None
    assert len(schedule) == db.NUM_WEEK_BLOCKS

    # make change to the Schedule Table
    session.query(db.Schedule).filter(db.Schedule.netid == netid).delete()
    for i, status in enumerate(schedule):
        block = db.Schedule(
            timeblock=i,
            netid=netid,
            matched=bool(db.ScheduleStatus.MATCHED & status),
            pending=bool(db.ScheduleStatus.PENDING & status),
            available=bool(db.ScheduleStatus.AVAILABLE & status),
        )

        session.add(block)

    # make change to the User table if necessary
    print(f"update_schedule: trying to update user: {netid = }, {update_user = }")
    if update_user:
        db_user.update(netid, session=session, schedule=schedule, update_schedule=False)

    return True


@db.session_decorator(commit=True)
def add_schedule_status(
    netid: str,
    marked: List[int | bool],
    status: db.ScheduleStatus,
    *,
    session: Optional[Session] = None,
) -> bool:
    """Updates the pending schedule for a user with netid 'netid', according to the marked list. The
    indices of 'marked' correspond to a TimeBlock, and if an element is True, then the pending flag
    is marked for the corresponding TimeBlock. If False, then the element is ignored."""

    schedule: Optional[List[int]] = db_user.get_schedule(netid, session=session)
    if schedule is None:
        raise db_user.UserNotFound(netid=netid)

    for i, m in enumerate(marked):
        if m:
            schedule[i] |= status

    update_schedule(netid, schedule, session=session)
    return True

@db.session_decorator(commit=True)
def remove_schedule_status(
    netid: str,
    marked: List[int | bool],
    status: db.ScheduleStatus,
    *,
    session: Optional[Session] = None,
) -> bool:
    """Updates the pending schedule for a user with netid 'netid', according to the marked list. The
    indices of 'marked' correspond to a TimeBlock, and if an element is True, then the pending flag
    is unmarked for the corresponding TimeBlock. if False, then the element is ignored."""

    schedule: Optional[List[int]] = db_user.get_schedule(netid, session=session)
    if schedule is None:
        raise db_user.UserNotFound(netid=netid)

    for i, m in enumerate(marked):
        if m:
            schedule[i] &= ~status

    update_schedule(netid, schedule, session=session)
    return True


def _get_blocks(session: Session, netid: str, status_flag: Column) -> List[int]:
    rows = session.query(db.Schedule.timeblock).filter(
        db.Schedule.netid == netid, status_flag == True).order_by(db.Schedule.timeblock).all()
    return [row[0] for row in rows]


@db.session_decorator(commit=False)
def get_matched_schedule(netid: str, *, session: Optional[Session] = None) -> List[int]:
    """ Return schedule specifially showing time of matches"""
    assert session is not None
    return _get_blocks(session, netid, db.Schedule.matched)


@db.session_decorator(commit=False)
def get_pending_schedule(netid: str, *, session: Optional[Session] = None) -> List[int]:
    """ Return schedule specifially showing time of pending matches"""
    assert session is not None
    return _get_blocks(session, netid, db.Schedule.pending)


@db.session_decorator(commit=False)
def get_available_schedule(netid: str, *, session: Optional[Session] = None) -> List[int]:
    """Return schedule specifically showing time of availabilities"""
    assert session is not None
    return _get_blocks(session, netid, db.Schedule.available)


# TODO: get available users matching a given schedule
@db.session_decorator(commit=False)
def get_available_users(timeblock: int, *, session: Optional[Session] = None) -> List[str]:
    """Return list of users showing available users at a certain timeframe"""
    assert session is not None

    rows = session.query(db.Schedule.netid).filter(db.Schedule.timeblock == timeblock).order_by(
        db.Schedule.netid).all()
    return [row[0] for row in rows]

# def int_to_string_schedule(schedule: List[int]) -> List[str]:
#     schedule.
