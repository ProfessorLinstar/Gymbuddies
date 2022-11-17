"""Home page blueprint."""
from typing import Any, Dict
from flask import Blueprint
from flask import session
from flask import request
from flask import render_template, redirect, url_for
from . import common
from . import database
from .database import db

bp = Blueprint("home", __name__, url_prefix="")


@bp.route("/")
def index():
    """Default page for the Gymbuddies web application. Redirects to user home page if logged in."""
    if session.get("netid"):
        return redirect(url_for("home.home"))
    return render_template("index.html")



@bp.route("/home")
def home():
    """Homepage for logged-in user."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    user = database.user.get_user(netid)  # can access this in jinja template with {{ user }}
    assert user is not None
    interests = database.user.get_interests_string(netid)
    gender = db.Gender(user.gender).to_readable()
    level = db.Level(user.level).to_readable()

    context: Dict[str, Any] = {}
    common.fill_schedule(context, user.schedule)

    return render_template("home.html",
                           netid=netid,
                           user=user,
                           interests=interests,
                           gender=gender,
                           level=level,
                           **context)


@bp.route("/profile", methods=["GET", "POST"])
def profile():
    """Profile page for editing user information."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    user = database.user.get_user(netid)  # can access this in jinja template with {{ user }}

    if request.method == "POST" and "update" in request.form:
        prof: Dict[str, Any] = common.form_to_profile()
        submit: str = request.form.get("update", "")
        if submit == "information":
            prof.pop("schedule")
        elif submit == "schedule":
            prof = {"schedule": prof["schedule"]}
            # print("REQUEST", request.form)
            jsdata = request.form['javascript_data']
            print("JSDATA", jsdata)
        prof.update(netid=netid)
        assert database.user.update(**prof)

    user = database.user.get_user(netid)
    assert user is not None

    context: Dict[str, Any] = {}
    common.fill_schedule(context, user.schedule)

    return render_template("profile.html", netid=netid, user=user, **context)


