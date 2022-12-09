"""Error pages blueprint"""

import sys
import traceback

from flask import Blueprint
from flask import session, request
from flask import redirect, url_for
from sqlalchemy.exc import OperationalError
from werkzeug.exceptions import HTTPException, InternalServerError
from . import database
from .database import db

RETRY_NUM = 10

bp = Blueprint("error", __name__, url_prefix="")


class NoLoginError(Exception):
    """Exception raised in a data request if no user is currently logged in."""

    def __init__(self):
        super().__init__("No user is logged in.")


@bp.app_errorhandler(database.request.EmptyRequestSchedule)
def empty_request(ex):
    """Application handler for when attempting to create a request with no selected times."""
    traceback.print_exception(ex, file=sys.stderr)
    return {
        "error": type(ex).__name__,
        "message": "Please select at least one time.",
        "noRefresh": True
    }, 400

@bp.app_errorhandler(database.request.RequestStatusMismatch)
def request_mismatch(ex: database.request.RequestStatusMismatch):
    """Application handler for when attempting to perform an operation on a request with a
    mismatched request status."""
    traceback.print_exception(ex, file=sys.stderr)
    expected = db.RequestStatus(ex.expected).to_readable().lower()
    return {
        "error": type(ex).__name__,
        "message": f"The selected request has changed is no longer {expected}.",
        "noRefresh": True
    }, 410


    

@bp.app_errorhandler(database.request.RequestNotFound)
def request_not_found(ex):
    """Application error handler for when attempting to access a request that does not exist."""
    traceback.print_exception(ex, file=sys.stderr)
    return {
        "error": type(ex).__name__,
        "message": "The selected request no longer exists. Please refresh.",
        "noRefresh": False
    }, 410


@bp.app_errorhandler(database.user.UserNotFound)
def user_not_found(ex):
    """Application error handler for when attempting to access a user that does not exist. If the
    accessed user is currently logged in, then returns an authentication error code (401).
    Otherwise, returns a deleted-content error code (410)."""
    traceback.print_exception(ex, file=sys.stderr)

    if ex.netid == session.get("netid", ""):
        session.clear()
        return redirect(url_for("home.index"))

    return {
        "error": type(ex).__name__,
        "message": "The requested user no longer exists. Please refresh.",
        "noRefresh": False
    }, 410


@bp.app_errorhandler(OperationalError)
def sqlalchemy_operational_error(ex):
    """Application error handler for when sqlalchemy throws an operational error. These errors can
    occur randomly, and are generally outside of the client and application's control. Response
    should be to just continue normal function."""
    traceback.print_exception(ex, file=sys.stderr)

    session["retries"] = session.get("retries", 0) + 1
    if session["retries"] < RETRY_NUM:
        return redirect(request.url)
    else:
        session["retries"] = 0

    return {
        "error": type(ex).__name__,
        "message": "The database seems to be done. Please refresh.",
        "noRefresh": False
    }, 500


@bp.app_errorhandler(Exception)
def internal_server_error(ex: Exception):
    """Application error handler for when an unexpected error occurs."""

    traceback.print_exception(ex, file=sys.stderr)
    print("unexpected error occurred!")

    if isinstance(ex, HTTPException) and ex.code is not None:
        code = ex.code
        return ex.get_body(), code
    else:
        raise InternalServerError
