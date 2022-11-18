"""Common methods for routing modules."""
import json
from typing import Dict, Any, List
from flask import request
from . import database
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


def str_to_timeblock(day: str, time: str) -> db.TimeBlock:
    """Converts a day and time of the format 'HH:MM' to a TimeBlock."""
    hours, minutes = (int(t) for t in time.split(":"))
    return db.TimeBlock.from_daytime(
        int(day), hours * db.NUM_HOUR_BLOCKS + (minutes * db.NUM_HOUR_BLOCKS) // 60)


# TODO: error protect this
def json_to_schedule(calendar: str) -> List[db.ScheduleStatus]:
    """Converts a json calendar string of the form
    {
        '0': [['10:00', '11:00'], ['12:00', '17:00']],
        '1': [],
        '2': [],
        '3': [['12:00', '15:00']],
        '4': [],
        '5': [['5:00', '11:00'], ['12:00', '17:00']],
        '6': [],
    }
    to a schedule compatible with the database.
    """

    schedule = [db.ScheduleStatus.UNAVAILABLE] * db.NUM_WEEK_BLOCKS
    decoded: Dict[str, List[List[str]]] = json.loads(calendar)
    for day, events in decoded.items():
        for s, e in events:
            for i in range(str_to_timeblock(day, s), str_to_timeblock(day, e) - 1):
                schedule[i] = db.ScheduleStatus.AVAILABLE
    return schedule


def form_to_profile() -> Dict[str, Any]:
    """Converts request.form to a user profile dictionary. Ignores extraneous keys."""
    prof: Dict[str, Any] = {k: v for k, v in request.form.items() if k in db.User.__table__.columns}
    prof["interests"] = {v: True for v in request.form.getlist("interests")}

    for bool_key in ("open", "okmale", "okfemale", "okbinary"):
        prof[bool_key] = bool_key in prof

    prof["schedule"] = json_to_schedule(request.form.get("jsoncalendar", ""))

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


def needs_refresh(lastrefreshed: int, netid: str) -> bool:
    """Returns True if information regarding a user with netid 'netid' has changed since the
    timestamp 'lastrefreshed'. The timestamp 'lastrefreshed' should be provided in terms of the
    number of milliseconds since January 1st, 1970 00:00:00 UTC, as is done by javascript's
    Date.now() function. Otherwise, returns False."""

    lastupdated = database.user.get_lastupdated(netid)
    return lastupdated is not None and lastupdated.timestamp() * 1000 <= lastrefreshed
