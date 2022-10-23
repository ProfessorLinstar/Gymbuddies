"""Login page blueprint."""
from flask import Blueprint
from flask import session, request, g
from flask import render_template, redirect, url_for
from .database import user

bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.route("/login", methods=("GET", "POST"))
def login():
    """Shows login page."""
    netid: str = session.get("netid", "")
    if netid:
        return redirect(url_for("home.home"))

    if request.method == "GET":
        return render_template("login.html")

    response: str = ""
    netid = request.form["netid"]

    if user.get_user(netid):
        session["netid"] = netid
        return redirect(url_for("home.home"))

    response = f"Netid '{request.form['netid']}' was not found in the database."
    return render_template("login.html", response=response)

@bp.route("/logout")
def logout():
    """Logs out of the current user."""
    session.clear()
    return redirect(url_for("home.index"))

@bp.before_app_request
def load_logged_in_user():
    """If a user is logged in, load their data from the database."""
    netid: str = session.get("netid", "")

    g.user = user.get_user(netid) if netid else None
