"""Error pages blueprint"""

import functools
import random
import sys
import time
import traceback
from typing import Callable, ParamSpec, TypeVar

from flask import Blueprint
from flask import session, request
from flask import redirect, url_for
from sqlalchemy.exc import OperationalError
from werkzeug.exceptions import HTTPException, InternalServerError
from . import database
from .database import db

P = ParamSpec('P')
R = TypeVar('R')

RETRY_NUM = 10
TIMEOUT = .005 # seconds

bp = Blueprint("error", __name__, url_prefix="")


class NoLoginError(Exception):
    """Exception raised in a data request if no user is currently logged in."""

    def __init__(self):
        super().__init__("No user is logged in.")


def guard_decorator() -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator factory for protecting routes from database API errors. Resets the 'retries'
    session variable when a route is executed successfully."""

    def decorator(route: Callable[P, R]) -> Callable[P, R]:

        @functools.wraps(route)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            response = route(*args, **kwargs)
            session["retries"] = 0
            return response

        return wrapper

    return decorator


@bp.app_errorhandler(database.request.ConflictingRequestSchedule)
def conflicting_request_schedule(ex: database.request.ConflictingRequestSchedule):
    """Application handler for when attempting to create a request with no selected times."""
    traceback.print_exception(ex, file=sys.stderr)
    message = "Your match's or your schedules have changed. The times you have selected are no longer available. Please refresh."
    return {
        "error": type(ex).__name__,
        "message": message,
        "noRefresh": False,
    }, 400


@bp.app_errorhandler(database.request.RequestToBlockedUser)
def request_to_blocked_user(ex: database.request.RequestToBlockedUser):
    """Application handler for when attempting to create a request with no selected times."""
    traceback.print_exception(ex, file=sys.stderr)
    netid = session.get("netid", "")
    if ex.blocker != netid:
        blocker = ex.blocker 
        blocked = "You have"
    else:
        blocker = "you"
        blocked = ex.blocked + " has"
    return {
        "error": type(ex).__name__,
        "message": f"{blocked} been blocked by {blocker}.",
        "noRefresh": True
    }, 400


@bp.app_errorhandler(database.request.RequestAlreadyExists)
def request_already_exists(ex: database.request.RequestAlreadyExists):
    """Application handler for when attempting to create a request with no selected times."""
    traceback.print_exception(ex, file=sys.stderr)
    other = ex.srcnetid if ex.srcnetid != session.get("netid") else ex.destnetid
    return {
        "error": type(ex).__name__,
        "message": f"There is already an active request between {other} and you.",
        "noRefresh": True
    }, 400


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
    print(f"got operational error for the {session['retries']}th time.")
    if session["retries"] < RETRY_NUM:
        duration = TIMEOUT * (1 + random.random()) * 2**session["retries"] 
        print(f"sleeping for {duration = } before retry {session['retries'] = }")
        time.sleep(duration)
        return redirect(request.url, code=302 if request.method != "POST" else 307)
    else:
        session["retries"] = 0

    return {
        "error": type(ex).__name__,
        "message": "The database is under load. Please refresh.",
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
