"""Home page blueprint."""

from flask import Blueprint
from flask import session
from flask import render_template, redirect, url_for


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

    return render_template("home.html", netid=netid)

@bp.route("/profile")
def profile():
    """Profile page for editing user information."""
    return ""
