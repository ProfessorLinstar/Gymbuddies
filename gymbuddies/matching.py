"""Matching page blueprint. Provides routes for
  1. Finding matches
  2. Pending matches
  3. Matches
"""

from flask import Blueprint
from flask import render_template, redirect, url_for, request
from flask import session, g, request
from typing import List
from . import database
from .database import db
from .database import matchmaker

bp = Blueprint("matching", __name__, url_prefix="/matching")


@bp.route("/search")
def search():
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

    g.user = database.user.get_user(matches[index])  # can access this in jinja template with {{ g.user }}
    assert g.user is not None
    # g.requests = database.request.get_active_incoming(netid)
    level = database.db.Level(g.user.level)
    level = level.to_readable()
    interests = database.user.get_interests_string(netid)
    return render_template("search.html", netid=netid, level=level, interests=interests)


@bp.route("/pending", methods=("GET", "POST"))
def pending():
    """Page for pending matches."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        requestid = int(request.form.get("requestid", "0"))
        action = request.form.get("action")

        if action == "reject":
            database.request.finalize(requestid)
        elif action == "accept":
            database.request.reject(requestid)
        else:
            print(f"Action not found! {action = }")

    # TODO: handle errors when database is not available
    requests = database.request.get_active_incoming(netid)
    assert requests is not None

    requestUsers: List[db.MappedUser] = []
    for req in requests:
        requestUsers.append(database.user.get_user(req.srcnetid))

    levels = []
    interests = []
    for ruser in requestUsers:
        levels.append(db.Level(ruser.level).to_readable())
        interests.append(db.interests_to_readable(ruser.interests))

    print("interests", interests)
    print("requestUsers", requestUsers)
    return render_template("pending.html",
                           netid=netid,
                           requests=requests,
                           requestUsers=requestUsers,
                           levels=levels,
                           interests=interests)


@bp.route("/matched")
def matched():
    """Page for finding matched."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    g.user = database.user.get_user(netid)  # can access this in jinja template with {{ g.user }}
    return render_template("matched.html", netid=netid)
