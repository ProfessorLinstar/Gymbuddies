"""Home page blueprint."""
from typing import Dict, Any, List
from flask import Blueprint
from flask import session
from flask import request
from flask import render_template, redirect, url_for
from . import common
from . import database
from .database import db

bp = Blueprint("home", __name__, url_prefix="")

def fill_schedule(context: Dict[str, Any], schedule: List[int]) -> None:
    """Checks the master schedule boxes according to the provided 'schedule'."""
    for i, s in enumerate(schedule):
        day, time = db.TimeBlock(i).day_time()
        if s & db.ScheduleStatus.AVAILABLE and time % db.NUM_HOUR_BLOCKS == 0:
            context[f"s{day}_{time // db.NUM_HOUR_BLOCKS}"] = "checked"


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
    fill_schedule(context, user.schedule)

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

    if request.method == "POST" and "update" in request.form:
        prof: Dict[str, Any] = form_to_profile()
        submit: str = request.form.get("update", "")
        if submit == "information":
            prof.pop("schedule")
        elif submit == "schedule":
            prof = {"schedule": prof["schedule"]}
        prof.update(netid=netid)
        database.user.update(**prof)

    user = database.user.get_user(netid)
    assert user is not None

    context: Dict[str, Any] = {}
    fill_schedule(context, user.schedule)

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
        for i in range(start, start + db.NUM_HOUR_BLOCKS):
            schedule[i] = db.ScheduleStatus.AVAILABLE

    return prof
