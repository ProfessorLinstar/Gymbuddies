"""Common methods for routing modules."""
from typing import Dict, Any, List
from flask import request
from .database import db


def fill_schedule(context: Dict[str, Any], schedule: List[int]) -> None:
    """Checks the master schedule boxes according to the provided 'schedule'."""
    for i, s in enumerate(schedule):
        day, time = db.TimeBlock(i).day_time()
        if s & db.ScheduleStatus.AVAILABLE and time % db.NUM_HOUR_BLOCKS == 0:
            context[f"s{day}_{time // db.NUM_HOUR_BLOCKS}"] = "checked"


def schedule_to_calendar(schedule: List[int]) -> List[List[str]]:
    """Makes a calendar list from a schedule, to be inserted into 'calendar.html'. boxes according
    to the provided 'schedule'."""
    calendar = [[""] * (db.NUM_DAY_BLOCKS // db.NUM_HOUR_BLOCKS) for _ in range(len(db.DAY_NAMES))]

    for i, s in enumerate(schedule):
        day, time = db.TimeBlock(i).day_time()
        if s & db.ScheduleStatus.AVAILABLE and time % db.NUM_HOUR_BLOCKS == 0:
            calendar[day][time // db.NUM_HOUR_BLOCKS] = "checked"

    return calendar


def form_to_profile() -> Dict[str, Any]:
    """Converts request.form to a user profile dictionary. Ignores extraneous keys."""
    prof: Dict[str, Any] = {k: v for k, v in request.form.items() if k in db.User.__table__.columns}
    prof["interests"] = {v: True for v in request.form.getlist("interests")}

    for bool_key in ("open", "okmale", "okfemale", "okbinary"):
        prof[bool_key] = bool_key in prof

    prof["schedule"] = form_to_schedule()

    return prof


def form_to_schedule() -> List[db.ScheduleStatus]:
    """Populates 'schedule' with the user provided information in request.form."""
    schedule = [db.ScheduleStatus.UNAVAILABLE] * db.NUM_WEEK_BLOCKS

    for k in request.form:
        if ":" not in k:  # only timeblock entries will have colon in the key
            continue
        try:
            day, time = (int(i) for i in k.split(":"))
        except ValueError:
            continue

        start: db.TimeBlock = db.TimeBlock.from_daytime(day, time * db.NUM_HOUR_BLOCKS)
        for i in range(start, start + db.NUM_HOUR_BLOCKS):
            schedule[i] = db.ScheduleStatus.AVAILABLE

    return schedule
