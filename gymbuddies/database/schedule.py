"""Database API"""
from typing import List
from . import db

#### Scheduling ####
# return schedule informing occupied times of user
# list will be of size 2016 (7 * 24 * 12)
@db.session_decorator
def get_schedule(userId: int) -> List[int]:
    """Returns a a list of 2016 blocks for a user showing the availability statuses for
    each of these times. Bitwise masking must be used to extract statuses"""
    assert session is not None
    return session.query(db.User).filter(netid == userId).one().schedule


def schedule_query(session, userId: int, time: db.TimeBlock, user_table: bool) -> Query:
    """ Helper method for eliminating some repetitive code"""
    if user_table:
        return session.query(db.User).filter(db.User.netid == userId)
    else:
        return session.query(db.Schedule).filer(db.Schedule.netid == userId)
            .filter(db.Schedule.timeblock == time.index)


@db.session_decorator
def add_time_status(userId: int, time: db.TimeBlock, int: which_status) -> bool:
    """Updates either Availability, Pending, or Matched to be set for a certain time block.
    In the case that the attribute was already set, False is returned. which_status should
    be a ScheduleStatus enum value"""
    assert session is not None

    # make change to the Schedule Table
    row = schedule_query(session, userId, time, user_table=False).one()
    if row.status & which_status:
        return False
    row.status |= which_status
    # make change to the Request Table
    row = schedule_query(session, userId, NULL, user_table=True).one()
    row.schedule[time.index] |= schedule_status
    session.commit()

    return True


@db.session_decorator
def remove_time_status(userId: int, time: db.TimeBlock, int: which_status) -> bool:
    """Updates either Availability, Pending, or Matched to be unset for a certain time block.
    In the case that the attribute was already unset, False is returned. which_status should
    be a ScheduleStatus enum value"""
    assert session is not None

    # make change to the Schedule Table
    row = schedule_query(session, userId, time, user_table=False).one()
    if not (row.status & which_status):
        return False
    row.status &= ~which_status
    # make change to the Request Table
    row = schedule_query(session, userId, NULL, user_table=True).one()
    row.schedule[time.index] &= ~which_status
    session.commit()

    return True


@db.session_decorator
def get_match_schedule(userId: int) -> List[db.TimeBlock]:
    """ Return schedule specifially showing time of matches"""
    available_times: List[int] = []
    rows = session.query(db.Schedule).filter(db.Schedule.netid == userId)
        .filter(or_(db.Schedule.status == 1, db.Schedule.status == 3,
        db.Schedule.status == 5, db.Schedule.status == 7))
        .order_by(db.Schedule.timeblock).all()
    for row in rows:
        available_times.append(rows.timeblock)
    return available_times


@db.session_decorator
def get_pending_schedule(userId: int) -> List[db.TimeBlock]:
    """ Return schedule specifially showing time of pending matches"""
    available_times: List[int] = []
    rows = session.query(db.Schedule).filter(db.Schedule.netid == userId)
        .filter(or_(db.Schedule.status == 2, db.Schedule.status == 3,
        db.Schedule.status == 6, db.Schedule.status == 7))
        .order_by(db.Schedule.timeblock).all()
    for row in rows:
        available_times.append(rows.timeblock)
    return available_times


@db.session_decorator
def get_available_schedule(userId: int) -> List[db.TimeBlock]:
    """Return schedule specifically showing time of availabilities"""
    available_times: List[int] = []
    rows = session.query(db.Schedule).filter(db.Schedule.netid == userId)
        .filter(or_(db.Schedule.status >= 4 and db.Schedule.status <= 7))
        .order_by(db.Schedule.timeblock).all()
    for row in rows:
        available_times.append(rows.timeblock)
    return available_times


@db.session_decorator
def get_available_users() -> List[str]:
    return {}
