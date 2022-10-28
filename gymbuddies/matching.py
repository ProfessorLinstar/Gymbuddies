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
    return render_template("search.html", netid=netid)

@bp.route("/pending")
def pending():
    """Page for finding matches."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    g.user = database.user.get_user(netid)  # can access this in jinja template with {{ g.user }}
    return render_template("pending.html", netid=netid)

@bp.route("/matched")
def matched():
    """Page for finding matched."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    g.user = database.user.get_user(netid)  # can access this in jinja template with {{ g.user }}
    return render_template("matched.html", netid=netid)
