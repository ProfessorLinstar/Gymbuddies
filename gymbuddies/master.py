"""Master debugger page blueprint."""

import json
import textwrap

from typing import Dict, Any, List, Optional
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
    elif "submit-request" in request.form:
        handle_request(context, profile)
    elif "submit-matching" in request.form:
        handle_matching(context, profile)

    print("Made context of this form:")
    print(context["query"])

    context["netid"] = profile["netid"]
    return render_template("master.html", **context)


def form_to_profile() -> Dict[str, Any]:
    """Converts request.form to a user profile dictionary. Ignores extraneous keys."""
    profile: Dict[str,
                  Any] = {k: v for k, v in request.form.items() if k in db.User.__table__.columns}
    profile["interests"] = {v: True for v in request.form.getlist("interests")}
    for bool_key in ("open", "okmale", "okfemale", "okbinary"):
        profile[bool_key] = bool_key in profile

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


def fill_schedule(context: Dict[str, Any], schedule: List[int]) -> None:
    """Checks the master schedule boxes according to the provided 'schedule'."""
    for i, s in enumerate(schedule):
        day, time = db.TimeBlock(i).day_time()
        if s and time % db.NUM_HOUR_BLOCKS == 0:
            context[f"s{day}_{time // db.NUM_HOUR_BLOCKS}"] = "checked"


def handle_user(context: Dict[str, Any], profile: Dict[str, Any]) -> None:
    """Handles POST requests for 'user' functions"""
    netid: str = profile["netid"]
    submit: str = request.form.get("submit-user", "")

    if submit == "Create":
        if netid == "":
            context["query"] += "Cannot create user with empty netid. Creation aborted."
        else:
            context["query"] += f"Creation of user with netid '{netid}' successful.\n"
            context["query"] += wrap(database.debug.sprint_users(db.User.netid == netid))

    elif submit == "Update":
        database.user.update(**profile)
        context["query"] += f"Update of user with netid '{netid}' successful.\n"
        context["query"] += wrap(database.debug.sprint_users(db.User.netid == netid))

    elif submit == "Delete":
        database.user.delete(netid)
        context["query"] += f"Deletion of user with netid '{netid}' successful."

    elif submit == "Query":
        user: Optional[db.MappedUser] = None
        user_found: Optional[bool] = database.user.exists(netid)

        if user_found:
            user = database.user.get_user(netid)
        else:
            context["query"] += "netid not found. Database contains the following users.\n"
            users: Optional[List] = database.user.get_users()
            users = users if users else []
            context["query"] += json.dumps([u.netid for u in users], sort_keys=True, indent=4)

        if user_found and user is not None:
            # basic info
            context["netid"] = user.netid
            context["name"] = user.name
            context["contact"] = user.contact
            context["bio"] = user.bio
            context["addinfo"] = user.addinfo
            context[f"level{user.level}"] = "checked"
            context[f"gender{user.gender}"] = "checked"
            context["lastupdated"] = int(user.lastupdated.timestamp())

            context["open"] = "checked" if user.open else ""
            context["okmale"] = "checked" if user.okmale else ""
            context["okfemale"] = "checked" if user.okfemale else ""
            context["okbinary"] = "checked" if user.okbinary else ""

            print(user.okmale, user.okfemale, user.okbinary)

            # interests
            context["cardio"] = "checked" if user.interests.get("Cardiovascular Fitness") else ""
            context["upper"] = "checked" if user.interests.get("Upper Body") else ""
            context["lower"] = "checked" if user.interests.get("Lower Body") else ""
            context["losing"] = "checked" if user.interests.get("Losing Weight") else ""
            context["gaining"] = "checked" if user.interests.get("Gaining Mass") else ""

            fill_schedule(context, user.schedule)

            context["query"] += f"Query of user with netid '{netid}' successful."
            print(f"User '{netid}' query result:")
            database.debug.printv(user)
        elif user_found:
            context["query"] += f"User with netid '{netid}' found, but server encountered \n"
            context["query"] += "an error."

    elif submit == "Clear":
        pass

    else:
        context["query"] += f"Unknown submit request {submit}"


def handle_schedule(context: Dict[str, Any], profile: Dict[str, Any]) -> None:
    """Handles POST requests for 'schedule' functions."""
    netid: str = profile["netid"]

    if not database.user.exists(netid):
        context["query"] = f"User with netid '{netid}' not found in the database."
        return

    which_schedule: str = request.form.get("which_schedule", "available")
    submit: str = request.form.get("submit-schedule", "")

    if submit == "Get":
        schedule: List[int] = []
        if which_schedule == "match":
            schedule = database.schedule.get_matched_schedule(netid)
        elif which_schedule == "pending":
            schedule = database.schedule.get_pending_schedule(netid)
        elif which_schedule == "available":
            schedule = database.schedule.get_available_schedule(netid)

        fill_schedule(context, schedule)

        context["query"] += f"Get {which_schedule} schedule for user '{netid}' successful."
        context["query"] += f"\nFound these timeblocks: {schedule}"

    elif submit == "Update":
        status: db.ScheduleStatus = db.ScheduleStatus.from_str(which_schedule)
        database.schedule.add_schedule_status(netid, profile["schedule"], status)
        context["query"] += f"Update {which_schedule} schedule for user '{netid}' "
        context["query"] += "successful."


def handle_request(context: Dict[str, Any], profile: Dict[str, Any]) -> None:
    """Handles POST requests for 'request' functions."""
    srcnetid: str = profile["netid"]
    destnetid: str = request.form.get("destnetid", "")

    if not database.user.exists(srcnetid):
        context["query"] += f"User with netid '{srcnetid}' not found in the database."
        return

    submit: str = request.form.get("submit-request", "")
    requestid = request.form.get("requestid", "")
    requestid = int(requestid) if requestid.isdigit() else 0

    if submit == "Get":
        response = database.request.get_request(requestid)

        if response is None:
            context["query"] += f"Query for request {requestid} failed."
        else:
            fill_schedule(context, response.schedule)
            context["srcnetid"] = response.srcnetid
            context["destnetid"] = response.destnetid
            context["query"] += f"Query for request {requestid} successful.\n" + \
                f"Request {requestid} is: {db.RequestStatus(response.status).to_readable()}"

    elif submit == "New":
        response = database.request.new(srcnetid, destnetid, profile["schedule"])
        context["query"] += f"Request made from '{srcnetid}' to '{destnetid}'."

    elif submit == "Finalize":
        response = database.request.finalize(requestid)
        context["query"] += f"Request {requestid} successfully finalized."

    elif submit == "Modify":
        response = database.request.modify(requestid, profile["schedule"])
        context["query"] += f"Request {requestid} successfully modified."

    elif submit == "Reject":
        response = database.request.reject(requestid)
        context["query"] += f"Request {requestid} successfully rejected."

    elif submit == "Terminate":
        response = database.request.terminate(requestid)
        context["query"] += f"Request {requestid} successfully terminated."

    elif submit == "Query":
        in_requests = database.request.incoming_requests(srcnetid)
        context["query"] += f"Incoming requests for user with netid '{srcnetid}':\n"
        context["query"] += database.debug.sprint_requests(in_requests) + "\n"

        out_requests = database.request.outgoing_requests(srcnetid)
        context["query"] += f"Outgoing requests for user with netid '{srcnetid}':\n"
        context["query"] += database.debug.sprint_requests(out_requests) + "\n"


def handle_matching(context: Dict[str, Any], profile: Dict[str, Any]) -> None:
    """Handles matching functions."""
    netid: str = profile["netid"]

    if not database.user.exists(netid):
        context["query"] = f"User with netid '{netid}' not found in the database."
        return

    submit: str = request.form.get("submit-matching", "")
    if submit == "Get":
        matches = database.matchmaker.find_matches(netid)
        context["query"] += "Found these matches:"
        context["query"] += json.dumps(matches, indent=4, sort_keys=True)
