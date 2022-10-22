"""Master debugger page blueprint."""

from typing import Dict, Any
from flask import Blueprint
from flask import render_template
from flask import request
from .database import user


bp = Blueprint("master", __name__, url_prefix="/master")

@bp.route("/", methods=("GET", "POST"))
def show():
    """Shows master page."""

    if request.method == "POST":
        profile: Dict[str, Any] = dict(request.form.items())
        profile["interests"] = {v: True for v in request.form.getlist("interests")}
        profile["open"] = "open" in profile

        user.create(**profile)

        print(f"Got a request of the form: {request.form}")
        print(f"Created a user with netid {profile['netid']}!")

    return render_template("master.html")
