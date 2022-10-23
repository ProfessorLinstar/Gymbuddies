"""Master debugger page blueprint."""

import json
import textwrap

from typing import Dict, Any, List
from flask import Blueprint
from flask import render_template
from flask import request
from .database import db, user, debug

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
    query: str = ""

    if request.method == "GET":
        return render_template("master.html", query=query)

    print(f"Got a request of the form: {request.form}")

    profile: Dict[str, Any] = dict(request.form.items())
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

        timeblock: db.TimeBlock = db.TimeBlock.from_daytime(day, time)
        schedule[timeblock.index] = db.ScheduleStatus.AVAILABLE
        profile.pop(k)


    print(f"Converted request to profile: {json.dumps(profile, sort_keys=True, indent=4)}")

    if profile.pop("submit-create", None) is not None:
        user.create(**profile)
        query = wrap(debug.sprint_users(db.User.netid == profile["netid"]))

        print(f"Created a user with netid {profile['netid']}.")

    elif profile.pop("submit-update", None) is not None:
        user.update(**profile)
        query = wrap(debug.sprint_users(db.User.netid == profile["netid"]))

    elif profile.pop("submit-delete", None) is not None:
        user.delete(profile["netid"])

    elif profile.pop("submit-query", None) is not None:
        pass

    elif profile.pop("submit-clear", None) is not None:
        pass

    return render_template("master.html", query=query)
