"""Home page blueprint."""
from typing import Any, Dict
from flask import Blueprint
from flask import session
from flask import request
from flask import render_template, redirect, url_for
from . import common
from . import database
from .database import db

bp = Blueprint("home", __name__, url_prefix="")


@bp.route("/")
def index():
    """Default page for the Gymbuddies web application. Redirects to user home page if logged in."""
    # if session.get("netid"):
    #    return redirect(url_for("home.dashbaord"))
    return render_template("index.html")



@bp.route("/dashboard")
def dashboard():
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
    # ADD BACK FOR MATCHES CALENDAR!!!!
    matches = database.request.get_matches(netid) #should return a list of requests?
    matchSchedule = [0] * db.NUM_WEEK_BLOCKS
    if (matches is not None):
        for match in matches:
            #print("row", len(match.schedule))
            #matchSchedules.append(match.schedule) # should be array of strings
            matchSchedule = [a + b for a,b in zip(matchSchedule, match.schedule)]
    # matches = database.schedule.get_matched_schedule(netid)
    # matchSchedules = common.schedule_to_json(matches)
    print(matchSchedule)
    context: Dict[str, Any] = {}
    common.fill_schedule(context, matchSchedule)
    return render_template("dashboard.html",
                           netid=netid,
                           user=user,
                           interests=interests,
                           gender=gender,
                           level=level,
                           #matchSchedules=matchSchedules,
                           **context)


@bp.route("/profile", methods=["GET", "POST"])
def profile():
    """Profile page for editing user information."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    user = database.user.get_user(netid)

    if request.method == "POST":
        submit: str = request.form.get("update", "")
        prof: Dict[str, Any] = common.form_to_profile(submit)
        prof.update(netid=netid)
        assert database.user.update(**prof)

    user = database.user.get_user(netid)
    assert user is not None

    context: Dict[str, Any] = {}
    common.fill_schedule(context, user.schedule)

    return render_template("profile.html", netid=netid, user=user, **context)
