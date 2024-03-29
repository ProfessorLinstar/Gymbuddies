"""Login page blueprint."""
import re
import urllib.request
import urllib.parse

import flask
from flask import Blueprint
from flask import session, request, g
from flask import render_template, redirect, url_for
from . import database
from .database import user

_CAS_URL = 'https://fed.princeton.edu/cas/'

USE_CAS = True

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/signup", methods=("GET", "POST"))
def signup():
    """Shows signup page."""
    if not USE_CAS:
        if request.method == "GET":
            return render_template("signup.html")
        netid = request.form.get("netid", "")

    else:
        netid = authenticate()

    session["netid"] = netid
    try:
        database.user.create(netid)
        return redirect(url_for("home.newuser"))
    except user.UserAlreadyExists:
        return redirect(url_for("home.dashboard"))


@bp.route("/login", methods=("GET", "POST"))
def login():
    """Shows login page."""
    netid = session.get("netid", "")
    if netid:
        return redirect(url_for("home.dashboard"))

    if not USE_CAS:
        if request.method == "GET":
            return render_template("login.html")

        response: str = ""
        netid = request.form["netid"]

    else:
        netid = authenticate()

    if database.user.exists(netid):
        session["netid"] = netid
        return redirect(url_for("home.dashboard"))

    if not USE_CAS:
        response = f"Netid '{request.form['netid']}' was not found in the database."
        return render_template("login.html", response=response)
    else:
        return redirect(url_for("auth.signup"))


@bp.route("/logout")
def logout():
    """Log out of the CAS session, and then the application."""
    if USE_CAS:
        logout_url = (_CAS_URL + "logout?service=" +
                      urllib.parse.quote(re.sub("logout", "logoutapp", flask.request.url)))
        flask.abort(flask.redirect(logout_url))
    else:
        session.clear()
        return redirect(url_for("home.index"))


# TODO: check if necessary
@bp.before_app_request
def load_logged_in_user():
    """If a user is logged in, load their data from the database."""
    netid: str = session.get("netid", "")

    try:
        g.user = user.get_user(netid) if netid else None
    except database.user.UserNotFound:
        session.clear()


@bp.route("/logoutapp")
def logoutapp():
    """Logs out of the current user."""
    session.clear()
    return redirect(url_for("home.index"))


def strip_ticket(url):
    """Returns url after strippling out the ticket parameter added by the CAS server."""
    if url is None:
        return "something is badly wrong"

    url = re.sub(r"ticket=[^&]*&?", "", url)
    url = re.sub(r"\?&?$|&$", "", url)
    return url


def validate(ticket):
    """Validates a login ticket by contacting the CAS server. If valid, returns the user's netid;
    otehrwise, returns None."""
    val_url = (_CAS_URL + "validate" + "?service=" +
               urllib.parse.quote(strip_ticket(flask.request.url)) + "&ticket=" +
               urllib.parse.quote(ticket))
    lines = []

    with urllib.request.urlopen(val_url) as flo:
        lines = flo.readlines()  # Should return 2 lines.
    if len(lines) != 2:
        return None

    first_line = lines[0].decode("utf-8")
    second_line = lines[1].decode("utf-8")
    if not first_line.startswith("yes"):
        return None

    return second_line


def authenticate():
    """Authenticates the remote user, and returns the user's netid. Does not return unless the user
    is successfully authenticated."""
    if "netid" in flask.session:
        return flask.session.get("netid", "")

    ticket = flask.request.args.get("ticket")
    if ticket is None:
        login_url = (_CAS_URL + "login?service=" + urllib.parse.quote(flask.request.url))
        flask.abort(flask.redirect(login_url))

    netid = validate(ticket)
    if netid is None:
        login_url = (_CAS_URL + "login?service=" +
                     urllib.parse.quote(strip_ticket(flask.request.url)))
        flask.abort(flask.redirect(login_url))

    netid = netid.strip()
    flask.session["netid"] = netid
    return netid
