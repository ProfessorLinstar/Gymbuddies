"""Error pages blueprint"""

import sys
import traceback

from flask import Blueprint
from flask import session
from flask import render_template
from . import database

bp = Blueprint("error", __name__, url_prefix="")


@bp.app_errorhandler(database.user.UserAlreadyExists)
def user_already_exists(_):
    """Application error handler for when attempting to create a user which already exists."""
    return render_template("404.html"), 404


@bp.app_errorhandler(database.request.RequestNotFound)
def request_not_found(_):
    """Application error handler for when attempting to access a request that does not exist."""
    return render_template("410.html"), 410


@bp.app_errorhandler(database.user.UserNotFound)
def user_not_found(ex: database.user.UserNotFound):
    """Application error handler for when attempting to access a user that does not exist. If the
    accessed user is currently logged in, then returns an authentication error code (401).
    Otherwise, returns a deleted-content error code (410)."""

    if ex.netid == session.get("netid", ""):
        session.clear()
        return render_template("401.html"), 401
    return render_template("410.html"), 410


@bp.app_errorhandler(Exception)
def internal_server_error(ex):
    """Application error handler for when an unexpected error occurs."""

    traceback.print_exception(ex, file=sys.stderr)
    print("unexpected error occurred!")
    return render_template("500.html"), 500
