"""Home page blueprint."""
import json
from typing import Any, Dict
from flask import Blueprint
from flask import session
from flask import request
from flask import render_template, redirect, url_for
from . import common
from . import database
from .database import db
from . import sendsms

bp = Blueprint("home", __name__, url_prefix="")

@bp.route("/")
def index():
    """Default page for the Gymbuddies web application. Redirects to user home page if logged in."""
    if session.get("netid"):
        return redirect(url_for("home.dashboard"))
    return render_template("index.html")


@bp.route("/dashboard")
def dashboard():
    """Homepage for logged-in user."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    user = database.user.get_user(netid)  # can access this in jinja template with {{ user }}
    interests = database.user.get_interests_string(netid)
    gender = db.Gender(user.gender).to_readable()
    level = db.Level(user.level).to_readable()

    # context: Dict[str, Any] = {}
    # common.fill_schedule(context, user.schedule)
    # ADD BACK FOR MATCHES CALENDAR!!!!
    matches = database.request.get_matches(netid)  #should return a list of requests?
    matchSchedule = [0] * db.NUM_WEEK_BLOCKS
    requestName = ""
    matchNames = [""] * 2016
    for match in matches:
        # matchNames = match.schedule.copy()
        # requestName = database.user.get_name(match.destnetid)
        if (match.srcnetid == netid):
            requestName = database.user.get_name(match.destnetid)
        else: 
            requestName = database.user.get_name(match.srcnetid)
        for i in range(len(matchNames)):
            # print(matchNames[i].AVAILABLE)
            if (match.schedule[i] == 4):
                # print("triggered")
                matchNames[i] = requestName
        #print("row", len(match.schedule))
        #matchSchedules.append(match.schedule) # should be array of strings
        matchSchedule = [a + b for a, b in zip(matchSchedule, match.schedule)]

    # matches = database.schedule.get_matched_schedule(netid)
    # matchSchedules = common.schedule_to_json(matches)
    # print("schedule", matchSchedule)
    # print("names", matchNames)
    context: Dict[str, Any] = {}
    common.fill_match_schedule(context, matchSchedule, matchNames)
    # json.dumps(matchNames)
    return render_template(
        "dashboard.html",
        netid=netid,
        user=user,
        interests=interests,
        gender=gender,
        level=level,
        matchNames=matchNames,
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

    context: Dict[str, Any] = {}
    common.fill_schedule(context, user.schedule)

    return render_template("profile.html", netid=netid, user=user, **context)


@bp.route("/profileupdated", methods=["GET"])
def profileupdated():
    """Updated profile message."""
    time: str = request.args.get("lastupdated", "")
    return render_template("profileupdated.html", time=time)


@bp.route("/newuser", methods=["GET", "POST"])
def newuser():
    """Profile page for editing user information."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    user = database.user.get_user(netid)

    if request.method == "POST":
        prof: Dict[str, Any] = common.form_to_entireprofile()
        prof.update(netid=netid)
        assert database.user.update(**prof)

    user = database.user.get_user(netid)

    context: Dict[str, Any] = {}

    common.fill_schedule(context, user.schedule)

    return render_template("newuser.html", netid=netid, user=user, **context)