"""Home page blueprint."""

from typing import Dict, Any, List, Optional
from flask import Blueprint
from flask import session, g
from flask import request
from flask import render_template, redirect, url_for
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

    g.user = database.user.get_user(netid)  # can access this in jinja template with {{ g.user }}
    interests = database.user.get_interests_string(netid)
    gender = db.Gender(g.user.gender).to_readable()
    level = db.Level(g.user.level).to_readable()
    return render_template("home.html", netid=netid, user=g.user, interests=interests, gender=gender, level=level)


@bp.route("/profile", methods=["GET", "POST"])
def profile():
    """Profile page for editing user information."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    g.user = database.user.get_user(netid)  # can access this in jinja template with {{ g.user }}

    if request.method == "GET":
        return render_template("profile.html", netid=netid, user = g.user)

    profile: Dict[str, Any] = form_to_profile()
    if "submit-user" in request.form:
        handle_user(profile)
    elif "submit-schedule" in request.form:
        handle_schedule(profile)
    g.user = database.user.get_user(netid)
    return render_template("profile.html", netid=netid, user=g.user)

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

def handle_user(profile: Dict[str, Any]) -> None:
    """Handles POST requests for 'user' functions"""
    netid: str = profile["netid"]
    submit: str = request.form.get("submit-user", "")

    if submit == "Update":
        database.user.update(**profile)


def handle_schedule(profile: Dict[str, Any]) -> None:
    """Handles POST requests for 'schedule' functions."""
    netid: str = profile["netid"]

    which_schedule: str = request.form.get("which_schedule", "available")
    submit: str = request.form.get("submit-schedule", "")

    if submit == "Update":
        status: db.ScheduleStatus = db.ScheduleStatus.from_str(which_schedule)
        database.schedule.update_schedule_status(netid, profile["schedule"], status)


