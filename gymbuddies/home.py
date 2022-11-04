"""Home page blueprint."""

from typing import Dict, Any, List
from flask import Blueprint
from flask import session, g
from flask import request
from flask import render_template, redirect, url_for
from . import common
from . import database
from .database import db

bp = Blueprint("home", __name__, url_prefix="")


@bp.route("/")
def index():
    """Default page for the Gymbuddies web application. Redirects to user home page if logged in."""
    return render_template("index.html")


@bp.route("/home")
def home():
    """Homepage for logged-in user."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    user = database.user.get_user(netid)  # can access this in jinja template with {{ user }}
    assert user is not None
    interests = database.user.get_interests_string(netid)
    gender = db.Gender(user.gender).to_readable()
    level = db.Level(user.level).to_readable()

    context: Dict[str, Any] = {}
    common.fill_schedule(context, user.schedule)

    return render_template("home.html",
                           netid=netid,
                           user=user,
                           interests=interests,
                           gender=gender,
                           level=level,
                           **context)


@bp.route("/profile", methods=["GET", "POST"])
def profile():
    """Profile page for editing user information."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    ints = database.user.get_interests(netid)
    assert ints is not None
    print(ints.get("upper"))

    user = database.user.get_user(netid)  # can access this in jinja template with {{ user }}

    if request.method == "GET":
        return render_template("profile.html", netid=netid, user=user)

    prof: Dict[str, Any] = form_to_profile()
    if "submit-user" in request.form:
        handle_user(prof)

    user = database.user.get_user(netid)
    assert user is not None

    context: Dict[str, Any] = {}
    common.fill_schedule(context, user.schedule)

    return render_template("profile.html", netid=netid, user=user, **context)


def form_to_profile() -> Dict[str, Any]:
    """Converts request.form to a user profile dictionary. Ignores extraneous keys."""
    prof: Dict[str, Any] = {k: v for k, v in request.form.items() if k in db.User.__table__.columns}
    prof["interests"] = {v: True for v in request.form.getlist("interests")}
    for bool_key in ("open", "okmale", "okfemale", "okbinary"):
        prof[bool_key] = bool_key in prof

    schedule: List[int] = [db.ScheduleStatus.UNAVAILABLE] * db.NUM_WEEK_BLOCKS
    prof["schedule"] = schedule

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

    return prof


def handle_user(prof: Dict[str, Any]) -> None:
    """Handles POST requests for 'user' functions"""
    submit: str = request.form.get("submit-user", "")
    #print("requests", request.post("submit-user", ""))
    if submit == "Update":
        database.user.update(**prof)


