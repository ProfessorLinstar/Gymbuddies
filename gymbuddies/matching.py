"""Matching page blueprint. Provides routes for
  1. Finding matches
  2. Pending matches
  3. Matches
"""

from typing import Dict, Any, List
from flask import Blueprint
from flask import render_template, redirect, url_for, request
from flask import session, g, request
from typing import List
from . import common
from . import database
from .database import db

bp = Blueprint("matching", __name__, url_prefix="/matching")


@bp.route("/search", methods=("GET", "POST"))
def search():
    # get the current user in the session
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        destnetid = request.form["destnetid"]
        schedule = common.form_to_schedule()

        session["index"] += 1
        database.request.new(netid, destnetid, schedule)
        return redirect(url_for("matching.outgoing"))

    # implement the roundtable format of getting matches
    sess_index = request.args.get("index")
    if sess_index is not None:
        sess_index = int(sess_index)
        session["index"] += 1

    # get the users and index of current user that you have been matched with
    matches: List[str] = session.get("matches", None)
    index: int = session.get("index", None)
    if not matches or index >= len(matches):
        session["matches"] = database.matchmaker.find_matches(netid)
        session["index"] = 0
        matches = session.get("matches", None)
        index = session.get("index", None)

    # TODO: handle if g.user is None (e.g. if user is deleted but matches are preserved)
    g.user = database.user.get_user(
        matches[index])  # can access this in jinja template with {{ g.user }}
    assert g.user is not None
    # g.requests = database.request.get_active_incoming(netid)
    level = database.db.Level(g.user.level)
    level = level.to_readable()
    interests = database.user.get_interests_string(netid)
    # grab schedule
    context: Dict[str, Any] = {}
    common.fill_schedule(context, g.user.schedule)
    return render_template("search.html",
                           netid=netid,
                           level=level,
                           interests=interests,
                           user=g.user,
                           **context)

@bp.route("/buddies", methods=["GET"])
def buddies():
    # get the current user in the session
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    # implement the roundtable format of getting matches
    sess_index = request.args.get("index")
    if sess_index is not None:
        sess_index = int(sess_index)
        session["index"] += 1

    # get the users and index of current user that you have been matched with
    matches: List[str] = session.get("matches", None)
    index: int = session.get("index", None)
    if not matches or index >= len(matches):
        session["matches"] = database.matchmaker.find_matches(netid)
        session["index"] = 0
        matches = session.get("matches", None)
        index = session.get("index", None)

    # TODO: handle if g.user is None (e.g. if user is deleted but matches are preserved)
    g.user = database.user.get_user(
        matches[index])  # can access this in jinja template with {{ g.user }}
    assert g.user is not None
    # g.requests = database.request.get_active_incoming(netid)
    level = database.db.Level(g.user.level)
    level = level.to_readable()
    interests = database.user.get_interests_string(netid)
    # grab schedule
    context: Dict[str, Any] = {}
    common.fill_schedule(context, g.user.schedule)
    return render_template("buddies.html",
                           netid=netid,
                           level=level,
                           interests=interests,
                           user=g.user,
                           **context)


@bp.route("/pending", methods=("GET", "POST"))
def pending():
    """Page for pending matches."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        requestid = int(request.form.get("requestid", "0"))
        action = request.form.get("action")
        # if action == "reject":
        #     database.request.reject(requestid)
        if action == "accept":
            database.request.finalize(requestid)
        else:
            print(f"Action not found! {action = }")
        return redirect(url_for("matching.matched"))

    # # TODO: handle errors when database is not available
    # requests = database.request.get_active_incoming(netid)
    # assert requests is not None

    # request_users = []
    # calendars = []
    # for req in requests:
    #     request_users.append(database.user.get_user(req.srcnetid))
    #     calendars.append(common.schedule_to_calendar(req.schedule))

    # levels = []
    # interests = []
    # for ruser in request_users:
    #     levels.append(db.Level(ruser.level).to_readable())
    #     interests.append(db.interests_to_readable(ruser.interests))

    # print("interests", interests)
    # print("requestUsers", request_users)
    return render_template("pending.html",
                           netid=netid)
                        #    requests=requests,
                        #    calendars=calendars,
                        #    requestUsers=request_users,
                        #    levels=levels,
                        #    interests=interests)

@bp.route("/pendingtable", methods=("GET", "POST"))
def pendingtable():
    """Page for pending matches."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        requestid = int(request.form.get("requestid", "0"))
        action = request.form.get("action")

        if action == "reject":
            database.request.reject(requestid)
        elif action == "accept":
            database.request.finalize(requestid)
        else:
            print(f"Action not found! {action = }")

    # TODO: handle errors when database is not available
    requests = database.request.get_active_incoming(netid)
    assert requests is not None

    request_users = []
    calendars = []
    for req in requests:
        request_users.append(database.user.get_user(req.srcnetid))
        calendars.append(common.schedule_to_calendar(req.schedule))

    levels = []
    interests = []
    for ruser in request_users:
        levels.append(db.Level(ruser.level).to_readable())
        interests.append(db.interests_to_readable(ruser.interests))

    print("interests", interests)
    print("requestUsers", request_users)
    return render_template("pendingtable.html",
                           netid=netid,
                           requests=requests,
                           calendars=calendars,
                           requestUsers=request_users,
                           levels=levels,
                           interests=interests)


@bp.route("/outgoing", methods=["GET"])
def outgoing():
    """Page for viewing outgoing requests."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))
    return render_template("outgoing.html", netid=netid)

@bp.route("/outgoingtable", methods= ["POST"])
def outgoingtable():
    """Page for viewing outgoing requests."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    # TODO: put reject handler into shared helper function
    #if request.method == "POST":
    requestid = int(request.form.get("requestid", "0"))
    action = request.form.get("action")

    if action == "reject":
        database.request.reject(requestid)  # TODO: change to 'cancel'?
    else:
        print(f"Action not found! {action = }")

    g.user = database.user.get_user(netid)  # can access this in jinja template with {{ g.user }}
    matches = database.request.get_active_outgoing(netid)
    assert matches is not None

    users = [m.srcnetid if netid != m.srcnetid else m.destnetid for m in matches]
    users = [database.user.get_user(u) for u in users]

    return render_template("outgoingtable.html", netid=netid, matchusers=zip(matches, users))


@bp.route("/matched", methods=("GET", "POST"))
def matched():
    """Page for finding matched."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        requestid = int(request.form.get("requestid", "0"))
        action = request.form.get("action")

        if action == "terminate":
            database.request.terminate(requestid)
        else:
            print(f"Action not found! {action = }")


    g.user = database.user.get_user(netid)  # can access this in jinja template with {{ g.user }}
    matches = database.request.get_matches(netid)
    assert matches is not None

    users = [m.srcnetid if netid != m.srcnetid else m.destnetid for m in matches]
    users = [database.user.get_user(u) for u in users]

    return render_template("matched.html", netid=netid, matchusers=zip(matches, users))
