"""Master debugger page blueprint."""

import json
import textwrap

from typing import Dict, Any, List, Optional
from typing import cast
from flask import Blueprint
from flask import render_template
from flask import request
from . import database
from .database import db

TEXTWIDTH = 72

bp = Blueprint("master", __name__, url_prefix="/master")


def wrap(strs) -> str:
    """Returns the wrapped version of a string."""
    paragraphs: List[str] = []
    for s in strs:
        p: List[str] = [
            "\n".join(textwrap.wrap(line, width=TEXTWIDTH, replace_whitespace=False))
            for line in s.splitlines()
        ]
        paragraphs.append("\n".join(p))
    return "\n\n".join(paragraphs)


@bp.route("/", methods=("GET", "POST"))
def show():
    """Shows master page."""
    context: Dict[str, Any] = {"query": ""}

    if request.method == "GET":
        return render_template("master.html")

    print(f"Got a request of the form: {request.form}")

    profile: Dict[str, Any] = form_to_profile()
    print("Converted request to profile: " +
          f"{json.dumps({k: str(v) for k,v in profile.items()}, sort_keys=True, indent=4)}")

    if "submit-user" in request.form:
        handle_user(context, profile)
    elif "submit-schedule" in request.form:
        handle_schedule(context, profile)

    return render_template("master.html", **context)

def form_to_profile() -> Dict[str, Any]:
    """Converts request.form to a user profile dictionary. Ignores extraneous keys."""
    profile: Dict[str, Any] = {
            "netid" : "",
            "name" : "",
            "contact" : "",
            "level" : "0",
            "bio" : "",
            "addinfo" : "",
            "interests" : {},
            "schedule" : [],
            "open" : False,
            "settings" : {},
            }
    profile.update({k: v for k, v in request.form.items() if k in profile})
    profile["interests"] = {v: True for v in request.form.getlist("interests")}
    profile["open"] = "open" in profile

    schedule: List[int] = [db.ScheduleStatus.UNAVAILABLE] * db.NUM_WEEK_BLOCKS
    profile["schedule"] = schedule

    for k in request.form:
        if ":" not in k:  # only timeblock entries will have colon in the key
            continue
        try:
            day, time = (int(i) for i in k.split(":"))
        except ValueError:
            continue

        start: db.TimeBlock = db.TimeBlock.from_daytime(day, time * db.NUM_HOUR_BLOCKS)
        print(f"{(day, time) = } to {start = }")
        for i in range(start, start + db.NUM_HOUR_BLOCKS):
            schedule[i] = db.ScheduleStatus.AVAILABLE

    return profile

def handle_user(context: Dict[str, Any], profile: Dict[str, Any]) -> None:
    """Handles POST requests for 'user' functions"""

    netid: str = profile["netid"]
    query: str = ""

    match request.form.get("submit-user", ""):
        case "Create":
            if netid == "":
                query = "Cannot create user with empty netid. Creation aborted."
            elif database.user.create(**profile):
                query = f"Creation of user with netid '{profile['netid']}' successful.\n"
                query += wrap(database.debug.sprint_users(db.User.netid == netid))
            else:
                query = f"User with netid '{profile['netid']}' already exists. Skipping creation."

        case "Update":
            if database.user.update(**profile):
                query = f"Update of user with netid '{profile['netid']}' successful.\n"
                query += wrap(database.debug.sprint_users(db.User.netid == netid))
            else:
                query = f"netid '{profile['netid']}' not found in the database."



        case "Delete":
            if database.user.delete(netid):
                query = f"Deletion of user with netid '{profile['netid']}' successful."
            else:
                query = f"netid '{profile['netid']}' not found in the database."

        case "Query":
            user: Optional[db.MappedUser] = None
            user_found: Optional[bool] = database.user.has_user(netid)

            if user_found:
                user = database.user.get_user(netid)
            else:
                query = "netid not found or not provided. Database contains the following users.\n"
                users: Optional[List] = database.user.get_users()
                users = users if users else []
                query += json.dumps(
                        [u.netid for u in users], sort_keys=True, indent=4)

            if user_found and user is not None:
                # basic info
                context["netid"] = user.netid
                context["name"] = user.name
                context["contact"] = user.contact
                context["bio"] = user.bio
                context["addinfo"] = user.addinfo
                context[f"level{user.level}"] = "checked"
                context["open"] = "on" if user.open else ""

                # interests
                context["buildingmass"] = "checked" if user.interests.get("Building Mass") else ""
                context["losingweight"] = "checked" if user.interests.get("Losing Weight") else ""
                context["pecs"] = "checked" if user.interests.get("Pecs") else ""
                context["legs"] = "checked" if user.interests.get("Legs") else ""

                # schedule
                for i, s in enumerate(user.schedule):
                    day, time = db.TimeBlock(i).day_time()
                    s = cast(db.ScheduleStatus, s)
                    if s == db.ScheduleStatus.AVAILABLE and time % db.NUM_HOUR_BLOCKS == 0:
                        context[f"s{day}_{time // db.NUM_HOUR_BLOCKS}"] = "checked"

                query = f"Query of user with netid '{profile['netid']}' successful."
                print(f"User '{profile['netid']}' query result:")
                database.debug.printv(user)
            elif user_found:
                query = f"User with netid '{profile['netid']}' found, but server encountered \n"
                query += "an error."

        case "Clear":
            query = ""

        case other:
            query = f"Unknown submit request {other}"

    context["query"] = query
    print(query)

def handle_schedule(context: Dict[str, Any], profile: Dict[str, Any]) -> None:
    """Handles POST requests for 'schedule' functions."""
    netid: str = profile["netid"]
    query: str = ""

    if not database.user.has_user(netid):
        context["query"] = f"User with netid '{profile['netid']}' not found in the database."
        return

    which_schedule: str = request.form.get("which_schedule", "available")

    match request.form.get("submit-schedule", ""):
        case "Get":
            timeblocks: Optional[List[int]] = []
            if which_schedule == "match":
                timeblocks = database.schedule.get_matched_schedule(netid)
            elif which_schedule == "pending":
                timeblocks = database.schedule.get_pending_schedule(netid)
            elif which_schedule == "available":
                timeblocks = database.schedule.get_available_schedule(netid)

            if timeblocks is not None:
                for t in timeblocks:
                    day, time = db.TimeBlock(t).day_time()
                    context[f"s{day}_{time // db.NUM_HOUR_BLOCKS}"] = "checked"

                query = f"Get {which_schedule} schedule for user '{profile['netid']}' successful.\n"
                query += f"Found these timeblocks: {timeblocks}"
            else:
                query = f"Get {which_schedule} schedule for user '{profile['netid']}' failed.\n"

        case "Update":
            status: db.ScheduleStatus = db.ScheduleStatus.from_str(which_schedule)
            if database.schedule.update_schedule_status(netid, profile["schedule"], status):
                query = f"Update {which_schedule} schedule for user '{profile['netid']}' successful"
                query += "."
            else:
                query = f"Update {which_schedule} schedule for user '{profile['netid']}' failed."

    context["query"] = query
    print(query)
