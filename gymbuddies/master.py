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
    elif "submit-request" in request.form:
        handle_request(context, profile)

    print("Made context of this form:")
    print(context["query"])
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

    match request.form.get("submit-user", ""):
        case "Create":
            if netid == "":
                context["query"] += "Cannot create user with empty netid. Creation aborted."
            elif database.user.create(**profile):
                context["query"] += f"Creation of user with netid '{netid}' successful.\n"
                context["query"] += wrap(database.debug.sprint_users(db.User.netid == netid))
            else:
                context["query"] += f"User with netid '{netid}' already exists. Skipping creation."

        case "Update":
            if database.user.update(**profile):
                context["query"] += f"Update of user with netid '{netid}' successful.\n"
                context["query"] += wrap(database.debug.sprint_users(db.User.netid == netid))
            else:
                context["query"] += f"netid '{netid}' not found in the database."



        case "Delete":
            if database.user.delete(netid):
                context["query"] += f"Deletion of user with netid '{netid}' successful."
            else:
                context["query"] += f"netid '{netid}' not found in the database."

        case "Query":
            user: Optional[db.MappedUser] = None
            user_found: Optional[bool] = database.user.has_user(netid)

            if user_found:
                user = database.user.get_user(netid)
            else:
                context["query"] += "netid not found. Database contains the following users.\n"
                users: Optional[List] = database.user.get_users()
                users = users if users else []
                context["query"] += json.dumps(
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
                    if s & db.ScheduleStatus.AVAILABLE and time % db.NUM_HOUR_BLOCKS == 0:
                        context[f"s{day}_{time // db.NUM_HOUR_BLOCKS}"] = "checked"

                context["query"] += f"Query of user with netid '{netid}' successful."
                print(f"User '{netid}' query result:")
                database.debug.printv(user)
            elif user_found:
                context["query"] += f"User with netid '{netid}' found, but server encountered \n"
                context["query"] += "an error."

        case "Clear":
            pass

        case other:
            context["query"] += f"Unknown submit request {other}"

def handle_schedule(context: Dict[str, Any], profile: Dict[str, Any]) -> None:
    """Handles POST requests for 'schedule' functions."""
    netid: str = profile["netid"]

    if not database.user.has_user(netid):
        context["query"] = f"User with netid '{netid}' not found in the database."
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

                context["query"] += f"Get {which_schedule} schedule for user '{netid}' successful."
                context["query"] += f"\nFound these timeblocks: {timeblocks}"
            else:
                context["query"] += f"Get {which_schedule} schedule for user '{netid}' failed."

        case "Update":
            status: db.ScheduleStatus = db.ScheduleStatus.from_str(which_schedule)
            if database.schedule.update_schedule_status(netid, profile["schedule"], status):
                context["query"] += f"Update {which_schedule} schedule for user '{netid}' "
                context["query"] += "successful."
            else:
                context["query"] += f"Update {which_schedule} schedule for user '{netid}' failed."

def handle_request(context: Dict[str, Any], profile: Dict[str, Any]) -> None:
    """Handles POST requests for 'request' functions."""
    netid: str = profile["netid"]
    destnetid: str = request.form.get("destnetid", "")
    srcnetid: str = request.form.get("srcnetid", "")

    if not database.user.has_user(netid):
        context["query"] += f"User with netid '{netid}' not found in the database."
        return

    if destnetid and srcnetid:
        context["query"] += "Use only one of srcnetid and destnetid."
        return

    if not database.user.has_user(srcnetid) and not database.user.has_user(destnetid):
        context["query"] += f"Request users '{srcnetid}' and '{destnetid}' not found.\n"
        in_requests: Optional[Dict[int, db.RequestStatus]] = database.request.incoming_requests(
                netid)
        if in_requests is None:
            context["query"] += f"Incoming requests query for user with netid '{netid}' failed."
            return

        context["query"] += f"Incoming requests for user with netid '{netid}':\n"
        context["query"] += json.dumps(
            {requestid: {
                "id": requestid,
                "users": database.request.get_request_users(requestid),
                "status": status.to_readable()
            } for requestid, status in in_requests.items()},
            sort_keys=True,
            indent=4)
        context["query"] += "\n"

        out_requests: Optional[Dict[int, db.RequestStatus]] = database.request.outgoing_requests(
                netid)
        if out_requests is None:
            context["query"] += f"Outgoing requests query for user with netid '{netid}' failed."
            return

        context["query"] += f"Outgoing requests for user with netid '{netid}':\n"
        context["query"] += json.dumps(
            {requestid: {
                "id": requestid,
                "users": database.request.get_request_users(requestid),
                "status": status.to_readable()
            } for requestid, status in out_requests.items()},
            sort_keys=True,
            indent=4)
        context["query"] += "\n"
        return

    if destnetid:
        srcnetid = netid
    else:
        destnetid = netid

    match request.form.get("submit-request", ""):
        case "Get":
            requestid: Optional[int] = database.request.get_active_id(srcnetid, destnetid)
            if requestid is None:
                context["query"] += f"Active request not found between '{srcnetid}' and "
                context["query"] += f"'{destnetid}'."
                return
            req: db.MappedRequest = database.request.get_request(requestid)
            print(req)
        case "Update":
            if database.request.get_active_id(srcnetid, destnetid):
                context["query"] += f"Pending request between {srcnetid} and {destnetid} "
                context["query"] += "already exists."
            elif database.request.make_request(srcnetid, destnetid, profile["schedule"]):
                context["query"] += f"Request made between {srcnetid} and {destnetid}."
            else:
                context["query"] += f"Request between {srcnetid} and {destnetid} failed."
        case "Reject":
            requestid: Optional[int] = database.request.get_active_id(srcnetid, destnetid)
            if requestid is None:
                context["query"] += f"Reject request between {srcnetid} and {destnetid} failed. "
                context["query"] += "No such active request exists."
            elif database.request.delete_request(requestid):
                context["query"] += f"Reject request between {srcnetid} and {destnetid} successful."
            else:
                context["query"] += f"Reject request between {srcnetid} and {destnetid} failed."
        case "Terminate":
            pass
