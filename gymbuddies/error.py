"""Error pages blueprint"""

import sys
import traceback

from flask import Blueprint
from flask import session
from flask import render_template
from sqlalchemy.exc import OperationalError
from werkzeug.exceptions import HTTPException
from . import database

bp = Blueprint("error", __name__, url_prefix="")


class NoLoginError(Exception):
    """Exception raised in a data request if no user is currently logged in."""

    def __init__(self):
        super().__init__("No user is logged in.")



@bp.app_errorhandler(database.request.RequestNotFound)
def request_not_found(_):
    """Application error handler for when attempting to access a request that does not exist."""
    return render_template("error.html"), 410


@bp.app_errorhandler(database.user.UserNotFound)
def user_not_found(ex):
    """Application error handler for when attempting to access a user that does not exist. If the
    accessed user is currently logged in, then returns an authentication error code (401).
    Otherwise, returns a deleted-content error code (410)."""

    code = 410
    if ex.netid == session.get("netid", ""):
        session.clear()
        code = 401

    return render_template("error.html"), code


@bp.app_errorhandler(OperationalError)
def sqlalchemy_operational_error(_):
    """Application error handler for when sqlalchemy throws an operational error. These errors can
    occur randomly, and are generally outside of the client and application's control. Response
    should be to just continue normal function."""

    return render_template("error.html"), 404

@bp.app_errorhandler(Exception)
def internal_server_error(ex: Exception):
    """Application error handler for when an unexpected error occurs."""

    traceback.print_exception(ex, file=sys.stderr)
    print("unexpected error occurred!")

    if isinstance(ex, HTTPException) and ex.code is not None:
        code = ex.code
        return ex.get_body(), code
    else:
        code = 500
        return render_template("error.html"), code
