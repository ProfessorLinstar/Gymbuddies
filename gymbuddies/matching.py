"""Matching page blueprint. Provides routes for
  1. Finding matches
  2. Pending matches
  3. Matches
"""

from flask import Blueprint
from flask import render_template


bp = Blueprint("matching", __name__, url_prefix="/matching")

@bp.route("/search")
def search():
    """Page for finding matches."""
    return render_template("search.html")

@bp.route("/pending")
def pending():
    """Page for finding matches."""
    return render_template("pending.html")

@bp.route("/matched")
def matched():
    """Page for finding matched."""
    return render_template("matched.html")
