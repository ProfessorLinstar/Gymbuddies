"""Master debugger page blueprint."""

import json
import textwrap

from typing import Dict, Any, List, cast
from flask import Blueprint
from flask import render_template
from flask import request
from .database import db, user, debug

TEXTWIDTH = 72
BLOCK_NUM = 12

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

    if request.method == "GET" or "submit-form" not in request.form:
        return render_template("master.html")

    print(f"Got a request of the form: {request.form}")

    form: str = request.form["submit-form"]

    match form:
        case "user":
            handle_user(context)


    return render_template("master.html", **context)

def handle_user(context) -> None:
    """Handles POST requests for 'user' functions"""


    profile: Dict[str, Any] = {
            "netid" : "",
            "name" : "",
            "contact" : "",
            "level" : "0",
            "addinfo" : "",
            "interests" : {},
            "schedule" : [],
            "open" : False,
            "settings" : {},
            }
    profile.update({k: v for k, v in request.form.items() if k != "submit-form"})
    profile["interests"] = {v: True for v in request.form.getlist("interests")}
    profile["open"] = "open" in profile

    schedule: List[int] = [db.ScheduleStatus.UNAVAILABLE] * db.NUM_WEEK_BLOCKS
    profile["schedule"] = schedule

    for k in tuple(profile):
        if ":" not in k:  # only timeblock entries will have colon in the key
            continue
        try:
            day, time = (int(i) for i in k.split(":"))
        except ValueError:
            continue

        start: db.TimeBlock = db.TimeBlock.from_daytime(day, time * BLOCK_NUM)
        print(f"{(day, time) = } to {start = }")
        for i in range(start.index, start.index + BLOCK_NUM):
            schedule[i] = db.ScheduleStatus.AVAILABLE
        profile.pop(k)


    print("Converted request to profile: " +
          f"{json.dumps({k: str(v) for k,v in profile.items()}, sort_keys=True, indent=4)}")

    match profile.pop("submit-user", ""):
        case "Create":
            user.create(**profile)
            context["query"] = wrap(debug.sprint_users(db.User.netid == profile["netid"]))

            print(f"Created a user with netid '{profile['netid']}'.")

        case "Update":
            user.update(**profile)
            context["query"] = wrap(debug.sprint_users(db.User.netid == profile["netid"]))

            print(f"Updated a user with netid '{profile['netid']}'.")

        case "Delete":
            user.delete(profile["netid"])

        case "Query":
            u = user.get_user(profile["netid"])
            if u is not None:
                # basic info
                context["netid"] = u.netid
                context["name"] = u.name
                context["contact"] = u.contact
                context["addinfo"] = u.addinfo
                context[f"level{u.level}"] = "checked"
                context["open"] = "on" if u.open else ""

                # interests
                context["buildingmass"] = "checked" if u.interests.get("buildingmass") else ""
                context["losingweight"] = "checked" if u.interests.get("losingweight") else ""
                context["pecs"] = "checked" if u.interests.get("pecs") else ""
                context["legs"] = "checked" if u.interests.get("legs") else ""

                # schedule
                for i, s in enumerate(u.schedule):
                    day, time = db.TimeBlock(i).day_time()
                    s = cast(db.ScheduleStatus, s)
                    if s == db.ScheduleStatus.AVAILABLE and time % BLOCK_NUM == 0:
                        context[f"s{day}_{time // BLOCK_NUM}"] = "checked"

        case "Clear":
            pass
