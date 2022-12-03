"""Database API"""
from typing import List, Optional, Dict, Tuple, Any
from datetime import datetime, timezone
from sqlalchemy import Column
from sqlalchemy.orm import Session
from . import db
from . import user as db_user
from . import schedule as db_schedule


class RequestAlreadyExists(Exception):
    """Exception raised in API call if attempting to create multiple active requests."""

    srcnetid: str
    destnetid: str

    def __init__(self, srcnetid: str, destnetid: str):
        self.srcnetid = srcnetid
        self.destnetid = destnetid
        super().__init__(f"Active request between '{srcnetid}' and '{destnetid}' already exists.")


class InvalidRequestSchedule(Exception):
    """Exception raised in API call if request made with empty schedule."""

    def __init__(self):
        super().__init__("Invalid request schedule. Request must have one or more selected blocks.")


class ConflictingRequestSchedule(Exception):
    """Exception raised in API call if request made with conflicting schedules."""

    def __init__(self):
        super().__init__("Conflicting request schedules.")


class RequestNotFound(Exception):
    """Exception raised in API call if request not found."""

    requestid: int

    def __init__(self, requestid: int):
        self.requestid = requestid
        super().__init__(f"Request with requestid '{requestid}' not found in the database.")


class RequestStatusMismatch(Exception):
    """Exception raised if the actual status of a request does not match the expected status of a
    database API call."""

    actual: db.RequestStatus
    expected: db.RequestStatus

    def __init__(self, actual: db.RequestStatus, expected: db.RequestStatus):
        self.actual = actual
        self.expected = expected
        super().__init__(f"Expected request status {expected}; instead got {actual}.")


@db.session_decorator(commit=False)
def get_inactive_outgoing(srcnetid: str, *, session: Optional[Session] = None) -> List[Any]:
    """Attempts to return a list of the active outgoing requests for a user with netid 'destnetid',
    sorted in order with respect to the request's make timestamp, newest first. If 'destnetid' does
    not exist in the database, returns an empty list."""
    assert session is not None
    return session.query(db.Request).filter(db.Request.srcnetid == srcnetid,
                                            db.Request.status != db.RequestStatus.PENDING).order_by(
                                                db.Request.maketimestamp.desc()).all()


@db.session_decorator(commit=False)
def get_active_outgoing(srcnetid: str, *, session: Optional[Session] = None) -> List[Any]:
    """Attempts to return a list of the active outgoing requests for a user with netid 'destnetid',
    sorted in order with respect to the request's make timestamp, newest first. If 'destnetid' does
    not exist in the database, returns an empty list."""
    assert session is not None
    return session.query(db.Request).filter(db.Request.srcnetid == srcnetid,
                                            db.Request.status == db.RequestStatus.PENDING).order_by(
                                                db.Request.maketimestamp.desc()).all()


@db.session_decorator(commit=False)
def get_inactive_incoming(destnetid: str, *, session: Optional[Session] = None) -> List[Any]:
    """Attempts to return a list of the active incoming requests for a user with netid 'srcnetid',
    sorted in order with respect to the request's make timestamp, newest first. If 'srcnetid' does
    not exist in the database, returns an empty list."""
    assert session is not None
    return session.query(db.Request).filter(db.Request.destnetid == destnetid,
                                            db.Request.status != db.RequestStatus.PENDING).order_by(
                                                db.Request.maketimestamp.desc()).all()


@db.session_decorator(commit=False)
def get_active_incoming(destnetid: str, *, session: Optional[Session] = None) -> List[Any]:
    """Attempts to return a list of the active incoming requests for a user with netid 'srcnetid',
    sorted in order with respect to the request's make timestamp, newest first. If 'srcnetid' does
    not exist in the database, returns an empty list."""
    assert session is not None
    return session.query(db.Request).filter(db.Request.destnetid == destnetid,
                                            db.Request.status == db.RequestStatus.PENDING).order_by(
                                                db.Request.maketimestamp.desc()).all()


@db.session_decorator(commit=False)
def get_active_single(netid: str, *, session: Optional[Session] = None) -> List[db.MappedRequest]:
    """Attempts to return the requestid of an active request from a user with netid 'srcnetid' to a
    user with netid 'destnetid'. If no such request exists, returns None."""
    assert session is not None

    return session.query(db.Request).filter(
        (db.Request.srcnetid == netid) | (db.Request.srcnetid == netid),
        db.Request.status.in_((db.RequestStatus.PENDING, db.RequestStatus.FINALIZED))).all()


@db.session_decorator(commit=False)
def get_active_pair(netid1: str,
                    netid2: str,
                    *,
                    session: Optional[Session] = None) -> db.MappedRequest:
    """Attempts to return the requestid of an active request from a user with netid 'srcnetid' to a
    user with netid 'destnetid'. If no such request exists, returns None."""
    assert session is not None

    return session.query(db.Request).filter(
        ((db.Request.srcnetid == netid1) & (db.Request.destnetid == netid2)) |
        ((db.Request.srcnetid == netid2) & (db.Request.destnetid == netid1)),
        db.Request.status.in_((db.RequestStatus.PENDING, db.RequestStatus.FINALIZED))).scalar()


@db.session_decorator(commit=False)
def get_request(requestid: int, *, session: Optional[Session] = None) -> db.MappedRequest:
    """Attempts to return a request with a given requestid. If no such request exists, raises a
    RequestNotFound exception."""
    assert session is not None
    return _get(session, requestid)


@db.session_decorator(commit=False)
def get_srcnetid(requestid: int, *, session: Optional[Session] = None) -> str:
    """Attempts to return the srcnetid of a request with id 'requestid'. If no such request exists,
    raises a RequestNotFound exception."""
    assert session is not None
    return _get_column(session, requestid, db.Request.srcnetid)


@db.session_decorator(commit=False)
def get_destnetid(requestid: int, *, session: Optional[Session] = None) -> str:
    """Attempts to return the srcnetid of a request with id 'requestid'. If no such request exists,
    raises a RequestNotFound exception."""
    assert session is not None
    return _get_column(session, requestid, db.Request.destnetid)


@db.session_decorator(commit=False)
def get_matches(netid: str, *, session: Optional[Session] = None) -> List[db.MappedRequest]:
    """ get a list of matches associated with a user"""
    assert session is not None
    return session.query(db.Request).filter(
        (db.Request.srcnetid == netid) | (db.Request.destnetid == netid),
        db.Request.status == db.RequestStatus.FINALIZED).all()


@db.session_decorator(commit=False)
def get_terminated(netid: str, *, session: Optional[Session] = None) -> List[db.MappedRequest]:
    """ get a list of matches associated with a user"""
    assert session is not None
    return session.query(db.Request).filter(
        (db.Request.srcnetid == netid) | (db.Request.destnetid == netid),
        db.Request.status != db.RequestStatus.FINALIZED).all()


@db.session_decorator(commit=False)
def get_request_status(requestid: int, *, session: Optional[Session] = None) -> db.RequestStatus:
    """Return request status of a requestid. If the request is not found, raises an exception."""
    assert session is not None
    return _get_column(session, requestid, db.Request.status)


@db.session_decorator(commit=False)
def get_request_schedule(requestid: int, *, session: Optional[Session] = None) -> List[int]:
    """ return timeblocks associated with request"""
    assert session is not None
    return _get_column(session, requestid, db.Request.schedule)


# probably not necessary
@db.session_decorator(commit=False)
def incoming_requests(destnetid: str,
                      *,
                      session: Optional[Session] = None) -> Dict[int, db.RequestStatus]:
    """get a list of incoming matches associatec with a user"""
    assert session is not None

    rows = session.query(db.Request).filter(db.Request.destnetid == destnetid).order_by(
        db.Request.srcnetid).all()
    incoming_request_statuses: Dict[int, db.RequestStatus] = {}
    for row in rows:
        incoming_request_statuses[row.requestid] = db.RequestStatus(row.status)

    return incoming_request_statuses


# probably not necessary
@db.session_decorator(commit=False)
def outgoing_requests(srcnetid: str,
                      *,
                      session: Optional[Session] = None) -> Dict[int, db.RequestStatus]:
    """get a list of outgoing matches associated with a user"""
    assert session is not None
    rows: List[db.MappedRequest] = session.query(
        db.Request).filter(db.Request.srcnetid == srcnetid).order_by(db.Request.destnetid).all()
    outgoing_request_statuses: Dict[int, db.RequestStatus] = {}
    for row in rows:
        outgoing_request_statuses[row.requestid] = db.RequestStatus(row.status)
    return outgoing_request_statuses


def _get(session: Session, requestid: int, entities: Tuple[Column, ...] = (db.Request,)) -> Any:
    """Returns the 'entities' of a given 'requestid' using the sqlalchemy connection in 'session'.
    If there is no request with the given 'requestid' in the database, then raises the
    RequestNotFound exception."""
    query = session.query(*entities).filter(db.Request.requestid == requestid).scalar()
    if query is None:
        raise RequestNotFound(requestid)
    return query


def _get_column(session: Session, requestid: int, column: Column) -> Any:
    """Like '_get', but returns a single column only."""
    return _get(session, requestid, (column,))


# TODO: disallow making requests for times that are unavailable, or already matched, or empty
@db.session_decorator(commit=True)
def new(srcnetid: str,
        destnetid: str,
        schedule: List[int | db.ScheduleStatus],
        *,
        session: Optional[Session] = None,
        prev: Optional[db.MappedRequest] = None) -> None:
    """Make a new outgoing request from user 'srcnetid' to user 'destnetid' with the proposed
    'schedule'. If an active 'prevrequest' is specified, then rejects or terminates 'prevrequest',
    and sets prevrequestid in the newly created request. Returns the new request object if
    successful. If there is already a pending or finalized request between 'srcnetid' and
    'destnetid', or if the specified 'prevrequest' is not active, then returns False."""
    assert session is not None
    assert len(schedule) == db.NUM_WEEK_BLOCKS
    for netid in (srcnetid, destnetid):
        if not db_user.exists(netid):
            raise db_user.UserNotFound(netid)

    if all(not x for x in schedule):
        raise InvalidRequestSchedule

    if any(x and (s == db.ScheduleStatus.MATCHED or d != db.ScheduleStatus.AVAILABLE)
           for x, s, d in zip(schedule, db_user.get_schedule(srcnetid, session=session),
                              db_user.get_schedule(destnetid, session=session))):
        raise ConflictingRequestSchedule

    prevrequestid: int = 0
    if prev is not None:
        prevrequestid = prev.requestid
        _deactivate(session, prev)

    elif get_active_pair(srcnetid, destnetid, session=session):
        raise RequestAlreadyExists(srcnetid, destnetid)

    request = db.Request(srcnetid=srcnetid,
                         destnetid=destnetid,
                         maketimestamp=datetime.now(timezone.utc),
                         status=db.RequestStatus.PENDING,
                         schedule=schedule,
                         prevrequestid=prevrequestid)
    session.add(request)

    # Update user lastupdated timestamp by doing an empty update
    db_user.update(srcnetid, session=session)
    db_user.update(destnetid, session=session)

    print("Created a request with this schedule: ", db.schedule_to_readable(schedule))


@db.session_decorator(commit=True)
def finalize(requestid: int, *, session: Optional[Session] = None) -> None:
    """finalize the request by approving the accept request"""
    assert session is not None
    request = _get(session, requestid)
    if request.status != db.RequestStatus.PENDING:
        raise RequestStatusMismatch(db.RequestStatus(request.status), db.RequestStatus.PENDING)

    request.finalizedtimestamp = datetime.now(timezone.utc)
    request.status = db.RequestStatus.FINALIZED

    for netid in (request.srcnetid, request.destnetid):
        db_schedule.add_schedule_status(netid, request.schedule, db.ScheduleStatus.MATCHED)
        for active in get_active_single(netid, session=session):
            if active.requestid == request.requestid:
                continue
            if any(x and y for x, y in zip(request.schedule, active.schedule)):
                _deactivate(session, active)


@db.session_decorator(commit=True)
def reject(requestid: int, *, session: Optional[Session] = None) -> None:
    """Reject request with id 'requestid'. If this request is not pending, raises an error."""
    assert session is not None
    _reject(session, _get(session, requestid))


def _reject(session: Session, request: db.MappedRequest) -> None:
    """Rejects request. If this request is not pending, raises an error."""
    if request.status != db.RequestStatus.PENDING:
        raise RequestStatusMismatch(db.RequestStatus(request.status), db.RequestStatus.PENDING)

    request.status = db.RequestStatus.REJECTED

    # Update user lastupdated timestamp
    db_user.update(request.srcnetid, session=session)
    db_user.update(request.destnetid, session=session)


@db.session_decorator(commit=True)
def terminate(requestid: int, *, session: Optional[Session] = None) -> None:
    """Terminates a request with id 'requestid'. If this request is not finalized, raises an
    error."""
    assert session is not None
    _terminate(session, _get(session, requestid))


def _terminate(session: Session, request: db.MappedRequest) -> None:
    """Terminates a request. If this request is not finalized, raises an error."""
    if request.status != db.RequestStatus.FINALIZED:
        raise RequestStatusMismatch(db.RequestStatus(request.status), db.RequestStatus.FINALIZED)

    for netid in (request.srcnetid, request.destnetid):
        db_schedule.remove_schedule_status(netid,
                                           request.schedule,
                                           db.ScheduleStatus.MATCHED,
                                           session=session)

    request.status = db.RequestStatus.TERMINATED


def _deactivate(session: Session, request: db.MappedRequest) -> None:
    """Deactivates a request if it is active."""
    if request.status == db.RequestStatus.PENDING:
        _reject(session, request)
    elif request.status == db.RequestStatus.FINALIZED:
        _terminate(session, request)


@db.session_decorator(commit=True)
def modify(requestid: int,
           schedule: List[db.ScheduleStatus | int],
           *,
           session: Optional[Session] = None) -> None:
    """Modifies active (pending or matching) request. Switches direction of request."""
    assert session is not None

    print("trying to modify with this schedule: ", db.schedule_to_readable(schedule))

    request = _get(session, requestid)
    new(request.destnetid, request.srcnetid, schedule, session=session, prev=request)

@db.session_decorator(commit=True)
def modifymatch(requestid: int, netid: str,
           schedule: List[db.ScheduleStatus | int],
           *,
           session: Optional[Session] = None) -> None:
    """Modifies match times."""
    assert session is not None

    print("trying to modify with this schedule: ", db.schedule_to_readable(schedule))

    request = _get(session, requestid)
    
    destuser
    srcuser = db.user.get_user(request.srcnetid)
    if srcuser != netid:
        destuser = srcuser
        srcuser = netid
    else:
        destuser =netid
    
    new(srcuser, destuser, schedule, session=session, prev=request)


@db.session_decorator(commit=True)
def delete_all(netid: str, *, session: Optional[Session] = None) -> None:
    """Deletes all requests involving the user with netid 'netid'."""
    assert session is not None
    requests: List[db.MappedRequest] = session.query(
        db.Request).filter((db.Request.srcnetid == netid) | (db.Request.destnetid == netid)).all()

    for request in requests:
        _deactivate(session, request)
        session.delete(request)
