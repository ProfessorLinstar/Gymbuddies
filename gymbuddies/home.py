"""Home page blueprint."""
from typing import Any, Dict
from flask import Blueprint
from flask import session, g
from flask import request
from flask import render_template, redirect, url_for
from . import common, error
from . import database
from .database import db

# import random
# from sqlalchemy.exc import OperationalError

bp = Blueprint("home", __name__, url_prefix="")

@bp.route("/")
@error.guard_decorator()
def index():
    """Default page for the Gymbuddies web application. Redirects to user home page if logged in."""
    if session.get("netid"):
        return redirect(url_for("home.dashboard"))
    return render_template("index.html")


@bp.route("/dashboard")
@error.guard_decorator()
def dashboard():
    """Homepage for logged-in user."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    # if random.random() < .9:
    #     raise OperationalError(None, None, None)

    user = database.user.get_user(netid)  # can access this in jinja template with {{ user }}
    interests = database.user.get_interests_string(netid)
    gender = db.Gender(user.gender).to_readable()
    level = db.Level(user.level).to_readable()

    # context: Dict[str, Any] = {}
    # common.fill_schedule(context, user.schedule)
    matches = database.request.get_matches(netid)  #should return a list of requests?
    matchSchedule = [0] * db.NUM_WEEK_BLOCKS
    requestName = ""
    matchNames = [""] * db.NUM_WEEK_BLOCKS
    for match in matches:
        # matchNames = match.schedule.copy()
        # requestName = database.user.get_name(match.destnetid)
        if (match.srcnetid == netid):
            requestName = database.user.get_name(match.destnetid)
        else: 
            requestName = database.user.get_name(match.srcnetid)
        for i in range(len(matchNames)):
            # print(matchNames[i].AVAILABLE)
            if (match.schedule[i] == 4 and match.schedule[i-1] != 4 and match.schedule[i+1] == 4):
                # print("triggered")
                matchNames[i] = requestName
        #print("row", len(match.schedule))
        #matchSchedules.append(match.schedule) # should be array of strings
        matchSchedule = [a + b for a, b in zip(matchSchedule, match.schedule)]

    # matches = database.schedule.get_matched_schedule(netid)
    # matchSchedules = common.schedule_to_json(matches)
    print("schedule", matchSchedule)
    print("names", matchNames)
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
@error.guard_decorator()
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
        database.user.update(**prof)
        # update the find a buddies page
        session["matches"] = database.matchmaker.find_matches(netid)
        session["index"] = 0

    user = database.user.get_user(netid)

    context: Dict[str, Any] = {}
    common.fill_schedule(context, user.schedule)

    return render_template("profile.html", netid=netid, user=user, **context)


@bp.route("/profileupdated", methods=["GET"])
@error.guard_decorator()
def profileupdated():
    """Updated profile message."""
    time: str = request.args.get("lastupdated", "")
    return render_template("profileupdated.html", time=time)


@bp.route("/newuser", methods=["GET", "POST"])
@error.guard_decorator()
def newuser():
    """Profile page for creating new user information."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    user = database.user.get_user(netid)

    if request.method == "POST":
        prof: Dict[str, Any] = common.form_to_entireprofile()
        prof.update(netid=netid)
        database.user.update(**prof)
        return redirect(url_for("home.profile"))

    user = database.user.get_user(netid)

    context: Dict[str, Any] = {}

    common.fill_schedule(context, user.schedule)

    return render_template("newuser.html", netid=netid, user=user, **context)


@bp.route("/settings", methods=["GET", "POST"])
@error.guard_decorator()
def settings():
    """Settings page."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    user = database.user.get_user(netid)

    if request.method == "POST" and request.form.get("update", "") == "true":
        # submit: str = request.form.get("update", "")
        # prof: Dict[str, Any] = common.form_to_profile(submit)
        # prof.update(netid=netid)
        # database.user.update(**prof)
        if request.form.get("notifications") == "on":
            database.user.recieve_notification_on(netid)
        else:
            database.user.recieve_notification_off(netid)

        print(request.form.get("blockinghere", 0) != "")

    if request.method == "POST" and request.form.get("blockinghere", "") == "true":
        blocknetid = request.form.get("netid", "")
        database.user.block_user(netid, blocknetid)

        # perform refresh for the find a buddy page after having blocked a user
        session["matches"] = database.matchmaker.find_matches(netid)
        session["index"] = 0

        # update the database requests and matches based on the block
        update_requests_matches(netid, blocknetid)
        # p = Process(target=update_requests_matches, args=(netid, blocknetid))
        # p.start()

    context: Dict[str, Any] = {}
    common.fill_schedule(context, user.schedule)

    notification = database.user.get_notification_status(netid)

    return render_template("settings.html", netid=netid, user=user, notification=notification, **context)

def update_requests_matches(netid, blocknetid):
    active_outgoing = database.request.get_active_outgoing(netid)
    for arequest in active_outgoing:
        if arequest.destnetid == blocknetid:
            database.request.reject(arequest.requestid)
    active_incoming = database.request.get_active_incoming(netid)
    for arequest in active_incoming:
        if arequest.srcnetid == blocknetid:
            database.request.reject(arequest.requestid)
    matches = database.request.get_matches(netid)
    for match in matches:
        if match.srcnetid == blocknetid or match.destnetid == blocknetid:
            database.request.terminate(match.requestid)

@bp.route("/blockedtable", methods=["GET", "POST"])
@error.guard_decorator()
def blockedtable():
    """Returns table of blocked people."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        # requestid = int(request.form.get("requestid", "0"))
        # action = request.form.get("action")

        # if action == "terminate":
        #     # INSERT function to unblock
        #     database.request.terminate(requestid)
        # else:
        #     print(f"Action not found! {action = }")
        delnetid = request.form.get("delnetid", "")
        database.user.unblock_user(netid, delnetid)
        
        # perform refresh for the find a buddy page after having unblocked a user
        session["matches"] = database.matchmaker.find_matches(netid)
        session["index"] = 0


    elif common.needs_refresh(int(request.args.get("lastrefreshed", 0)), netid):
        return ""

    print("blockedtable refreshed!")

    g.user = database.user.get_user(netid)  # can access this in jinja template with {{ g.user }}
    # matches = database.request.get_matches(netid)

    # GET BLOCKED!!!! REIMPLEMENT
    blocked = database.user.get_blocked(netid)
    users = [database.user.get_user(block) for block in blocked]
    length = len(blocked)

    return render_template("blockedtable.html",
                           netid=netid,
                           blockedusers=users,
                           length=length)
