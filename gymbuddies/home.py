"""Home page blueprint."""
import flask
from typing import Any, Dict
from flask import Blueprint
from flask import session, g
from flask import request
from flask import render_template, redirect, url_for
from . import common, error, auth
from . import database
from .database import db
import re
import urllib.request
import urllib.parse

# import random
# from sqlalchemy.exc import OperationalError

bp = Blueprint("home", __name__, url_prefix="")


@bp.route("/")
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
        return redirect(url_for("home.index"))
    if not database.user.user_profile_valid(netid):
        return redirect(url_for("home.newuser"))

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
            if (match.schedule[i] == 4 and match.schedule[i - 1] != 4 and
                    match.schedule[i + 1] == 4):
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
    return render_template("dashboard.html",
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
        return redirect(url_for("home.index"))

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


@bp.route("/profilecard", methods=["GET", "POST"])
def profilecard():
    """Profile page for editing user information."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("home.index"))

    user = database.user.get_user(netid)

    if request.method == "POST":
        submit: str = request.form.get("update", "")
        print("update value: ", submit)
        prof: Dict[str, Any] = common.form_to_profile(submit)
        prof.update(netid=netid)
        database.user.update(**prof)
        # update the find a buddies page
        session["matches"] = database.matchmaker.find_matches(netid)
        session["index"] = 0

    user = database.user.get_user(netid)

    context: Dict[str, Any] = {}
    common.fill_schedule(context, user.schedule)

    return render_template("profilecard.html", netid=netid, user=user, **context)


# @bp.route("/profileupdated", methods=["GET"])
# @error.guard_decorator()
# def profileupdated():
#     """Updated profile message."""
#     time: str = request.args.get("lastupdated", "")
#     return render_template("profileupdated.html", time=time)


@bp.route("/newuser", methods=["GET", "POST"])
@error.guard_decorator()
def newuser():
    """Profile page for creating new user information."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("home.index"))

    user = database.user.get_user(netid)

    if request.method == "POST":
        prof: Dict[str, Any] = common.form_to_entireprofile()
        prof.update(netid=netid)
        database.user.update(**prof)
        return redirect(url_for("home.tutorial"))

    user = database.user.get_user(netid)

    context: Dict[str, Any] = {}

    common.fill_schedule(context, user.schedule)

    return render_template("newuser.html", netid=netid, user=user, **context)

@bp.route("/tutorial", methods=["GET", "POST"])
@error.guard_decorator()
def tutorial():
    """Profile page for creating new user information."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("home.index"))

    return render_template("tutorial.html", netid=netid)


@bp.route("/settings", methods=["GET", "POST"])
@error.guard_decorator()
def settings():
    """Settings page."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("home.index"))
    if not database.user.user_profile_valid(netid):
        return redirect(url_for("home.newuser"))

    # user = database.user.get_user(netid)

    # if request.method == "POST" and request.form.get("update", "") == "true":
    #     if request.form.get("notifications") == "on":
    #         database.user.recieve_notification_on(netid)
    #     else:
    #         database.user.recieve_notification_off(netid)

    #     print(request.form.get("blockinghere", 0) != "")

    # notification = database.user.get_notification_status(netid)
    
    # return render_template("settings.html", netid=netid, user=user, notification=notification)

    return render_template("settings.html", netid=netid)

@bp.route("/blocksearch", methods=["GET", "POST"])
def blocksearch():
    """Block search box."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("home.index"))
    if not database.user.user_profile_valid(netid):
        return redirect(url_for("home.newuser"))

    if request.method == "POST" and request.form.get("blockinghere", "") == "true":
        blocknetid = request.form.get("netid", "")
        # make sure that the block user operation is valid
        if not (database.user.exists(blocknetid) and database.user.exists(netid)):
            pass
        elif blocknetid == netid:
            pass
        else:
            database.user.block_user(netid, blocknetid)
            # perform refresh for the find a buddy page after having blocked a user
            session["matches"] = database.matchmaker.find_matches(netid)
            session["index"] = 0
        update_requests_matches(netid, blocknetid)
    
    return render_template("blocksearch.html")

@bp.route("/settingsnotifs", methods=["GET", "POST"])
def settingsnotifs():
    """Settings notification toggle."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("home.index"))
    if not database.user.user_profile_valid(netid):
        return redirect(url_for("home.newuser"))

    user = database.user.get_user(netid)

    if request.method == "POST" and request.form.get("update", "") == "true":
        if request.form.get("notifications") == "on":
            database.user.recieve_notification_on(netid)
        else:
            database.user.recieve_notification_off(netid)

    notification = database.user.get_notification_status(netid)
    
    return render_template("settingsnotifs.html", netid=netid, user=user, notification=notification)

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
def blockedtable():
    """Returns table of blocked people."""
    netid: str = session.get("netid", "")
    if not netid:
        raise error.NoLoginError

    if request.method == "POST":
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

    return render_template("blockedtable.html", netid=netid, blockedusers=users, length=length)

@bp.route("/delete", methods=["POST"])
def delete():
    """Deletes user"""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("home.index"))

    database.user.delete(netid)
    # session.clear()
    if auth.USE_CAS:
        return redirect(url_for("auth.logout"))
    else:
        return redirect(url_for("home.index"))


@bp.route("/notificationstable", methods=["GET", "POST"])
def notificationstable():
    """Returns table of blocked people."""
    netid: str = session.get("netid", "")
    if not netid:
        raise error.NoLoginError

    if common.needs_refresh(int(request.args.get("lastrefreshed", 0)), netid):
        return ""

    print("notifications refreshed!")

    return render_template("notificationstable.html", unread=database.request.get_unread(netid))

@bp.route("/notificationbadge", methods=["GET", "POST"])
def notificationbadge():
    """Returns table of blocked people."""
    netid: str = session.get("netid", "")
    if not netid:
        raise error.NoLoginError

    if common.needs_refresh(int(request.args.get("lastrefreshed", 0)), netid):
        return ""

    return render_template("notificationbadge.html", unread=database.request.get_unread(netid))

@bp.route("/aboutus", methods=["GET", "POST"])
@error.guard_decorator()
def aboutus():
    """Profile page for creating new user information."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("home.index"))

    return render_template("aboutus.html", netid=netid)
