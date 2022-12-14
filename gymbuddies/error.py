"""Error pages blueprint"""

import functools
import sys
import traceback
from typing import Callable, ParamSpec, TypeVar

from flask import Blueprint
from flask import session
from sqlalchemy.exc import OperationalError
from werkzeug.exceptions import HTTPException, InternalServerError
from . import database
from .database import db

P = ParamSpec('P')
R = TypeVar('R')

RETRY_NUM = 10
TIMEOUT = .005  # seconds

bp = Blueprint("error", __name__, url_prefix="")


class NoLoginError(Exception):
    """Exception raised in a data request if no user is currently logged in."""

    def __init__(self):
        super().__init__("No user is logged in.")


# TODO: implement guard checking if necessary
def guard_decorator() -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator factory for protecting routes from database API errors."""

    def decorator(route: Callable[P, R]) -> Callable[P, R]:

        @functools.wraps(route)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            response = route(*args, **kwargs)
            return response

        return wrapper

    return decorator


@bp.app_errorhandler(NoLoginError)
def no_login_error(ex):
    """Application handler for when a data request is made but no user is logged in."""
    traceback.print_exception(ex, file=sys.stderr)
    return {
        "error": type(ex).__name__,
        "message": "You've been logged out. Please refresh.",
        "noRefresh": False,
    }, 401


@bp.app_errorhandler(database.request.PreviousRequestInactive)
def previous_request_inactive(ex):
    """Application handler for when attempting to modify a request that is no longer active."""
    traceback.print_exception(ex, file=sys.stderr)
    return {
        "error": type(ex).__name__,
        "message": "The selected request is no longer active.",
        "noRefresh": True,
    }, 400


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


@bp.app_errorhandler(database.request.RequestWhileClosed)
def request_while_closed(ex):
    """Application handler for when attempting to create a request while not open for matching."""
    traceback.print_exception(ex, file=sys.stderr)
    return {
        "error": type(ex).__name__,
        "message": "You are not open for matching. Please edit your profile to make requests.",
        "noRefresh": True
    }, 400


@bp.app_errorhandler(database.request.RequestToClosedUser)
def request_to_closed_user(ex):
    """Application handler for when attempting to create a request to a closed user."""
    traceback.print_exception(ex, file=sys.stderr)
    return {
        "error": type(ex).__name__,
        "message": "The requested user is no longer available for matching.",
        "noRefresh": True
    }, 400


@bp.app_errorhandler(database.request.RequestToBlockedUser)
def request_to_blocked_user(ex):
    """Application handler for when attempting to create a request to a blocked user."""
    traceback.print_exception(ex, file=sys.stderr)
    return {
        "error": type(ex).__name__,
        "message": "The requested user is no longer available for matching.",
        "noRefresh": True
    }, 400


@bp.app_errorhandler(database.request.RequestAlreadyExists)
def request_already_exists(ex: database.request.RequestAlreadyExists):
    """Application handler for when attempting to create a request to a user when a request already
    exists."""
    traceback.print_exception(ex, file=sys.stderr)
    other = ex.srcnetid if ex.srcnetid != session.get("netid") else ex.destnetid
    return {
        "error": type(ex).__name__,
        "message": f"There is already an active request between {other} and you.",
        "noRefresh": True
    }, 400


@bp.app_errorhandler(database.request.NoChangeModification)
def no_change_modification(ex):
    """Application handler for when attempting to modify a request with no changes."""
    traceback.print_exception(ex, file=sys.stderr)
    return {
        "error": type(ex).__name__,
        "message": "Please change at least one time.",
        "noRefresh": True
    }, 400


@bp.app_errorhandler(database.request.EmptyRequestSchedule)
def empty_request_schedule(ex):
    """Application handler for when attempting to create a request with no selected times."""
    traceback.print_exception(ex, file=sys.stderr)
    return {
        "error": type(ex).__name__,
        "message": "Please select at least one time.",
        "noRefresh": True
    }, 400

@bp.app_errorhandler(database.request.OverlapRequests)
def overlapRequests(ex: database.request.OverlapRequests):
    """Application handler for when attempting to create a request with no selected times."""
    traceback.print_exception(ex, file=sys.stderr)
    conflicts = database.request.get_conflicts(ex.requestid)
    names = []
    for conflict in conflicts:
        if conflict[0] == ex.requestid:
            names.append(database.user.get_name(conflict[0]))
        else:
            names.append(database.user.get_name(conflict[1]))
    namesString = ', '.join(names)
    return {
        "error": type(ex).__name__,
        "message": "The following requests are in conflict:\n" + namesString,
        "noRefresh": False
    }, 400

@bp.app_errorhandler(database.request.RequestStatusMismatch)
def request_status_mismatch(ex: database.request.RequestStatusMismatch):
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
