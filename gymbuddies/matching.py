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
        schedule = common.json_to_schedule(request.form["jsoncalendar"])

        session["index"] += 1
        assert database.request.new(netid, destnetid, schedule)
        # return redirect(url_for("matching.outgoing"))
        print("inside search POST")
        return ""

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
    # TODO: when no more matches -- index out of bound error
    # generate "no more matches message"
    if len(matches) is 0:
        noMatches = True
        return render_template("search.html", netid=netid, noMatches = noMatches)
    else:
        g.user = database.user.get_user(
            matches[index])  # can access this in jinja template with {{ g.user }}
        assert g.user is not None
        # g.requests = database.request.get_active_incoming(netid)
        level = database.db.Level(g.user.level)
        level = level.to_readable()
        interests = database.user.get_interests_string(netid)
        # grab schedule
        context: Dict[str, Any] = {}
        noMatches = False
        common.fill_schedule(context, g.user.schedule)
        return render_template("search.html",
                            noMatches = noMatches,
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

    if len(matches) is 0:
        noMatches = True
        return render_template("buddies.html", netid=netid, noMatches = noMatches)
    else:
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
        noMatches = False
        return render_template("buddies.html",
                        noMatches = noMatches,
                           netid=netid,
                           level=level,
                           interests=interests,
                           user=g.user,
                           **context)


@bp.route("/pending", methods=("GET",))
def pending():
    """Page for pending matches."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    return render_template("pending.html", netid=netid)


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

    elif common.needs_refresh(int(request.args.get("lastrefreshed", 0)), netid):
        return ""

    # TODO: handle errors when database is not available
    requests = database.request.get_active_incoming(netid)
    assert requests is not None

    request_users: List[Any] = [database.user.get_user(req.srcnetid) for req in requests]

    levels = []
    interests = []
    for ruser in request_users:
        levels.append(db.Level(ruser.level).to_readable())
        interests.append(db.interests_to_readable(ruser.interests))

    return render_template("pendingtable.html",
                           netid=netid,
                           requests=requests,
                           requestUsers=request_users,
                           levels=levels,
                           interests=interests)

@bp.route("/pendingmodal", methods=["GET"])
def pendingmodal():
    """Page for pending matches."""
    # return "<div class='modal-content'>lmao</div>"

    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    print("processing a pendingmodal request!")

    # TODO: handle errors when database is not available
    # requests = database.request.get_active_incoming(netid)
    # assert requests is not None
    requestid = request.args.get("requestid", "0")
    req = database.request.get_request(int(requestid))
    assert req is not None

    user = database.user.get_user(req.srcnetid)
    assert user is not None
    jsoncalendar = common.schedule_to_json(req.schedule)
    level = db.Level(user.level).to_readable()
    interests = db.interests_to_readable(user.interests)

    print(f"returning card with info for request {requestid = }")

    return render_template("pendingmodal.html",
                           netid=netid,
                           req=req,
                           user = user,
                           jsoncalendar=jsoncalendar,
                           level=level,
                           interests=interests)


@bp.route("/outgoing", methods=["GET"])
def outgoing():
    """Page for viewing outgoing requests."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))
    return render_template("outgoing.html", netid=netid)


@bp.route("/outgoingtable", methods=["POST", "GET"])
def outgoingtable():
    """Page for viewing outgoing requests."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    # TODO: put reject handler into shared helper function
    requestid = int(request.form.get("requestid", "0"))
    action = request.form.get("action", "")

    if request.method == "POST":
        if action == "reject":
            database.request.reject(requestid)  # TODO: change to 'cancel'?
        else:
            print(f"Action not found! {action = }")
    elif common.needs_refresh(int(request.args.get("lastrefreshed", 0)), netid):
        return ""

    g.user = database.user.get_user(netid)  # can access this in jinja template with {{ g.user }}
    requests = database.request.get_active_outgoing(netid)
    assert requests is not None

    users = [m.destnetid for m in requests]
    users = [database.user.get_user(u) for u in users]
    length = len(requests)

    return render_template("outgoingtable.html", netid=netid, matchusers=zip(requests, users), length=length)


@bp.route("/matched", methods=("GET",))
def matched():
    """Page for finding matched."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    return render_template("matched.html", netid=netid)


@bp.route("/matchedtable", methods=("GET", "POST"))
def matchedtable():
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

    elif common.needs_refresh(int(request.args.get("lastrefreshed", 0)), netid):
        return ""

    print("matchedtable refreshed!")

    g.user = database.user.get_user(netid)  # can access this in jinja template with {{ g.user }}
    matches = database.request.get_matches(netid)
    assert matches is not None

    users = [m.srcnetid if netid != m.srcnetid else m.destnetid for m in matches]
    users = [database.user.get_user(u) for u in users]
    length = len(matches)

    return render_template("matchedtable.html", netid=netid, matchusers=zip(matches, users), length = length)
