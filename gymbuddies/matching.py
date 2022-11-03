"""Matching page blueprint. Provides routes for
  1. Finding matches
  2. Pending matches
  3. Matches
"""

from flask import Blueprint
from flask import render_template, redirect, url_for
from flask import session, g
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

@bp.route("/pending")
def pending():
    """Page for pending matches."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    # g.user = database.user.get_user(netid)  # can access this in jinja template with {{ g.user }}
    g.requests = database.request.get_active_incoming(netid)
    # print("netid", netid)
    # print("request incoming", database.request.get_active_incoming(netid))
    # print("request outgoing", database.request.get_active_outgoing(netid))
    requestUsers = []
    for request in g.requests:
        print("request", request)
        requestUsers.append(database.user.get_user(request.destnetid))
    levels = []
    
    for ruser in requestUsers:
        user_level = db.Level(ruser.level)
        levels.append(user_level.to_readable())
        user_interests = database.user.get_interests(ruser.netid)
        s = ", ".join((k for k, v in user_interests.items() if v))
        
            

    print("requestUsers", requestUsers)
    return render_template("pending.html", netid=netid, requestUsers=requestUsers, levels = levels, interests=s )

@bp.route("/matched")
def matched():
    """Page for finding matched."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    g.user = database.user.get_user(netid)  # can access this in jinja template with {{ g.user }}
    return render_template("matched.html", netid=netid)
