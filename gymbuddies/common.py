"""Common methods for routing modules."""
import json
import sys
import traceback
from typing import Dict, Any, List

from flask import request
from . import database
from .database import db


class VerificationError(Exception):
    """Exception raised in API call if attempting to create a user with a netid already in the
    database."""

    netid: str

    def __init__(self, netid: str):
        self.netid = netid
        super().__init__(f"User with netid '{netid}' does not exist. Verification failed.")


def fill_schedule(context: Dict[str, Any], schedule: List[int]) -> None:
    """Checks the master schedule boxes according to the provided 'schedule'."""
    context["jsoncalendar"] = schedule_to_json(schedule)

def fill_match_schedule(context: Dict[str, Any], schedule: List[int], matchNames: List[str]) -> None:
    """Checks the master schedule boxes according to the provided 'schedule'."""
    context["jsoncalendar"] = schedule_to_jsonmatches(schedule, matchNames)

def fill_modify_schedule(context: Dict[str, Any], schedule: List[int], requests: List[int]) -> None:
    """Checks the master schedule boxes according to the provided 'schedule'."""
    context["jsoncalendar"] = schedule_to_jsonmodify(schedule, requests)

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
    print(decoded)
    for day, events in decoded.items():
        for s, e in events:
            for i in range(str_to_timeblock(day, s), str_to_timeblock(day, e)):
                schedule[i] = db.ScheduleStatus.AVAILABLE

    return schedule

# schedule should be available
def schedule_to_json(schedule: List[int]) -> str:
    """Converts a schedule into stringified json representation appropriate for the artsy
    calendar."""
    jsoncalendar: Dict[int, List[List[str]]] = {i: [] for i in range(len(db.DAY_NAMES))}

    for event in db.schedule_to_events(schedule):
        day, _ = event[0].day_time()
        start, end = [t.time_str() for t in event]
        jsoncalendar[day].append([start, end if end != "00:00" else "24:00"])

    return json.dumps(jsoncalendar)

#schedule should be available
def schedule_to_jsonmatches(schedule: List[int], matchNames: List[str]) -> str:
    """Converts a schedule into stringified json representation appropriate for the artsy
    calendar."""
    jsoncalendar: Dict[int, List[List[str]]] = {i: [] for i in range(len(db.DAY_NAMES))}

    # blocks: List[List[TimeBlock]] = [[]]
    # for t, status in enumerate(schedule):
    #     if (status != ScheduleStatus.AVAILABLE or t % NUM_DAY_BLOCKS == 0) and blocks[-1]:
    #         blocks[-1].append(TimeBlock(t))
    #         blocks.append([])
    #     if status == ScheduleStatus.AVAILABLE and not blocks[-1]:
    #         blocks[-1].append(TimeBlock(t))

    # if blocks[-1]:
    #     blocks[-1].append(TimeBlock(len(schedule)))
    # else:
    #     blocks.pop()

    # return blocks

    for event in db.schedule_to_matchevents(schedule, matchNames):
        day, _ = event[0][0].day_time()
        start, end = [t[0].time_str() for t in event]
        jsoncalendar[day].append([start, end if end != "00:00" else "24:00", event[0][1]])

    return json.dumps(jsoncalendar)


#schedule should be available
def schedule_to_jsonmodify(schedule: List[int], requests: List[int]) -> str:
    """Converts a schedule into stringified json representation appropriate for the artsy
    calendar."""
    jsoncalendar: Dict[int, List[List[str]]] = {i: [] for i in range(len(db.DAY_NAMES))}

    # blocks: List[List[TimeBlock]] = [[]]
    # for t, status in enumerate(schedule):
    #     if (status != ScheduleStatus.AVAILABLE or t % NUM_DAY_BLOCKS == 0) and blocks[-1]:
    #         blocks[-1].append(TimeBlock(t))
    #         blocks.append([])
    #     if status == ScheduleStatus.AVAILABLE and not blocks[-1]:
    #         blocks[-1].append(TimeBlock(t))

    # if blocks[-1]:
    #     blocks[-1].append(TimeBlock(len(schedule)))
    # else:
    #     blocks.pop()

    # return blocks

    for event in db.schedule_to_modifyevents(schedule, requests):
        day, _ = event[0][0].day_time()
        start, end = [t[0].time_str() for t in event]
        jsoncalendar[day].append([start, end if end != "00:00" else "24:00", event[0][1]])

    return json.dumps(jsoncalendar)


def form_to_profile(category: str) -> Dict[str, Any]:
    """Converts request.form to a user profile dictionary. Ignores extraneous keys. If
    update_schedule is True, then updates the schedule. Otherwise, updates other information."""

    prof: Dict[str, Any] = {}

    if category == "information":
        prof.update({k: v for k, v in request.form.items() if k in db.User.__table__.columns})
        prof["interests"] = {v: True for v in request.form.getlist("interests")}
        prof.pop("schedule", None)

        for bool_key in ("open", "okmale", "okfemale", "okbinary"):
            prof[bool_key] = bool_key in prof

    elif category == "schedule":
        prof["schedule"] = json_to_schedule(request.form.get("jsoncalendar", ""))

    return prof

def form_to_entireprofile() -> Dict[str, Any]:
    """Converts request.form to a user profile dictionary. Ignores extraneous keys. updates b
    oth schedule and information at the same time"""

    prof: Dict[str, Any] = {}

    # if category == "information":
    prof.update({k: v for k, v in request.form.items() if k in db.User.__table__.columns})
    prof["interests"] = {v: True for v in request.form.getlist("interests")}
    prof.pop("schedule", None)

    for bool_key in ("open", "okmale", "okfemale", "okbinary"):
            prof[bool_key] = bool_key in prof

    # elif category == "schedule":
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

    return database.user.get_lastupdated(netid).timestamp() * 1000 <= lastrefreshed
