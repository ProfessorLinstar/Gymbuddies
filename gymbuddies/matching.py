"""Matching page blueprint. Provides routes for
  1. Finding matches
  2. Pending matches
  3. Matches
"""

from flask import Blueprint
from flask import render_template, redirect, url_for
from flask import session, g, request
from typing import List
from . import database
from .database import db

bp = Blueprint("matching", __name__, url_prefix="/matching")


@bp.route("/search")
def search():
    """Page for finding matches."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    g.user = database.user.get_user(netid)  # can access this in jinja template with {{ g.user }}
    # g.requests = database.request.get_active_incoming(netid)
    return render_template("search.html", netid=netid)


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
