"""Master debugger page blueprint."""

import json
from typing import Dict, Any
from flask import Blueprint
from flask import render_template
from flask import request
from .database import db, user, debug

bp = Blueprint("master", __name__, url_prefix="/master")


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

    profile["schedule"] = "n" * db.NUM_WEEK_BLOCKS
    for k,v in profile.items():
        if ":" not in k:
            continue
        try:
            day, time = (int(i) for i in k.split(":"))
        except ValueError:
            continue

        timeblock: db.TimeBlock = db.TimeBlock.from_daytime(day, time)

    print(f"Converted request to profile: {json.dumps(profile, sort_keys=True, indent=4)}")

    if profile.pop("submit-create", None) is not None:
        user.create(**profile)
        query = "\n".join(debug.sprint_users(db.User.netid == profile["netid"]))

        print(f"Created a user with netid {profile['netid']}.")

    elif profile.pop("submit-update", None) is not None:
        user.update(**profile)
        query = "\n".join(debug.sprint_users(db.User.netid == profile["netid"]))

    elif profile.pop("submit-delete", None) is not None:
        user.delete(profile["netid"])

    elif profile.pop("submit-query", None) is not None:
        pass

    return render_template("master.html", query=query)
