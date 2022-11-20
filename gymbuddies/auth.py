"""Login page blueprint."""
import flask
from flask import Blueprint
from flask import session, request, g
from flask import render_template, redirect, url_for
from . import database
from .database import user
import urllib.request
import urllib.parse
import re

_CAS_URL = 'https://fed.princeton.edu/cas/'

USE_CAS = True

bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.route("/signup", methods=("GET", "POST"))
def signup():
    """Shows signup page."""
    if not USE_CAS:
        if request.method == "GET":
            return render_template("signup.html")
        netid = request.form["netid"]

        if database.user.exists(netid):
            return redirect(url_for("auth.login"))

    else:
        netid = authenticate()
        assert netid is not None
        if database.user.exists(netid):
            session["netid"] = netid
            return redirect(url_for("home.home"))

    database.user.create(netid)
    session["netid"] = netid
    return redirect(url_for("home.profile"))


@bp.route("/login", methods=("GET", "POST"))
def login():
    """Shows login page."""
    netid: str = session.get("netid", "")
    if netid:
        return redirect(url_for("home.home"))

    if not USE_CAS:
        if request.method == "GET":
            return render_template("login.html")

        response: str = ""
        netid = request.form["netid"]

        if user.get_user(netid):
            session["netid"] = netid
            return redirect(url_for("home.home"))

        response = f"Netid '{request.form['netid']}' was not found in the database."
        return render_template("login.html", response=response)

    else:
        netid = authenticate()
        assert netid is not None
        if database.user.exists(netid):
            session["netid"] = netid
            return redirect(url_for("home.home"))
        return redirect(url_for("home.index"))


@bp.route("/logout")
def logout():
    # Log out of the CAS session, and then the application.
    if USE_CAS:
        logout_url = (_CAS_URL + "logout?service=" +
                      urllib.parse.quote(re.sub("logoutcas", "logoutapp", flask.request.url)))
        flask.abort(flask.redirect(logout_url))
    else:
        session.clear()
        return redirect(url_for("home.index"))


@bp.before_app_request
def load_logged_in_user():
    """If a user is logged in, load their data from the database."""
    netid: str = session.get("netid", "")

    g.user = user.get_user(netid) if netid else None


def logoutapp():
    """Logs out of the current user."""
    session.clear()
    return redirect(url_for("home.index"))


# Return url after stripping out the "ticket" parameter that was
# added by the CAS server
def strip_ticket(url):
    if url is None:
        return "something is badly wrong"
    url = re.sub(r"ticket=[^&]*&?", "", url)
    url = re.sub(r"\?&?$|&$", "", url)
    return url


# Validate a login ticket by contacting the CAS server. If
# valid, return the user’s username; otherwise, return None.


def validate(ticket):
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


# Authenticate the remote user, and return the user's username.
# Do not return unless the user is successfully authenticated
def authenticate():
    if 'netid' in flask.session:
        return flask.session.get('username')
    ticket = flask.request.args.get('ticket')
    if ticket is None:
        login_url = (_CAS_URL + "login?service=" + urllib.parse.quote(flask.request.url))
        flask.abort(flask.redirect(login_url))
    username = validate(ticket)
    if username is None:
        login_url = (_CAS_URL + "login?service=" +
                     urllib.parse.quote(strip_ticket(flask.request.url)))
        flask.abort(flask.redirect(login_url))
    username = username.strip()
    flask.session['netid'] = username
    return username
