"""Home page blueprint."""

from flask import Blueprint
from flask import session, g
from flask import render_template, redirect, url_for
from . import database

bp = Blueprint("home", __name__, url_prefix="")


@bp.route("/")
def index():
    """Default page for the Gymbuddies web application. Redirects to user home page if logged in."""
    return render_template("index.html")


@bp.route("/home")
def home():
    """Homepage for logged-in user."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    g.user = database.user.get_user(netid)  # can access this in jinja template with {{ g.user }}
    return render_template("home.html", netid=netid)


@bp.route("/profile")
def profile():
    """Profile page for editing user information."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    g.user = database.user.get_user(netid)  # can access this in jinja template with {{ g.user }}
    return render_template("profile.html", netid=netid)
