"""Database API"""
from typing import List, Optional, Dict, Tuple, Any
from datetime import datetime
from sqlalchemy import Column
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.orm import Session
from . import db
from . import user as db_user


class MultipleActiveRequests(Exception):
    """Exception raised in API call if user required but not found in database."""

    def __init__(self, netid1: str, netid2: str):
        super().__init__(f"Multiple active requests found between users '{netid1}' and '{netid2}'.")


class RequestNotFound(Exception):
    """Exception raised in API call if user required but not found in database."""

    def __init__(self, requestid: int):
        super().__init__(f"Request with requestid '{requestid}' not found in the database.")


# TODO: ERROR HANDLING FOR ALL OF THESE FUNCTIONS


@db.session_decorator(commit=False)
def get_active_outgoing(destnetid: str,
                        *,
                        session: Optional[Session] = None) -> List[db.MappedRequest]:
    """Attempts to return a list of the active outgoing requests for a user with netid 'destnetid',
    sorted in order with respect to the request's make timestamp, newest first. If 'destnetid' does
    not exist in the database, returns an empty list."""
    assert session is not None
    return session.query(db.Request).filter(db.Request.destnetid == destnetid,
                                            db.Request.status == db.RequestStatus.PENDING).order_by(
                                                db.Request.maketimestamp).all()


@db.session_decorator(commit=False)
def get_active_incoming(srcnetid: str,
                        *,
                        session: Optional[Session] = None) -> List[db.MappedRequest]:
    """Attempts to return a list of the active incoming requests for a user with netid 'srcnetid',
    sorted in order with respect to the request's make timestamp, newest first. If 'srcnetid' does
    not exist in the database, returns an empty list."""
    assert session is not None
    return session.query(db.Request).filter(db.Request.srcnetid == srcnetid,
                                            db.Request.status == db.RequestStatus.PENDING).order_by(
                                                db.Request.maketimestamp).all()


@db.session_decorator(commit=False)
def get_active(netid1: str,
               netid2: str,
               entities: Tuple[Column, ...] = (db.Request,),
               *,
               session: Optional[Session] = None) -> Any:
    """Attempts to return the requestid of an active request from a user with netid 'srcnetid' to a
    user with netid 'destnetid'. If no such request exists, returns None."""
    assert session is not None

    try:
        request = session.query(*entities).filter(
            ((db.Request.srcnetid == netid1) & (db.Request.destnetid == netid2)) |
            ((db.Request.srcnetid == netid2) & (db.Request.destnetid == netid1)),
            db.Request.status.in_((db.RequestStatus.PENDING, db.RequestStatus.FINALIZED))).scalar()
    except MultipleResultsFound as ex:
        raise MultipleActiveRequests(netid1, netid2) from ex

    return request


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
def get_matches(netid: str, *, session: Optional[Session] = None) -> List[int]:
    """ get a list of matches associated with a user"""
    assert session is not None
    requestids = session.query(db.Request.requestid).filter(
        (db.Request.srcnetid == netid) | (db.Request.destnetid == netid),
        db.Request.status == db.RequestStatus.FINALIZED).all()

    return [row[0] for row in requestids]


@db.session_decorator(commit=False)
def get_request_users(requestid: int, *, session: Optional[Session] = None) -> List[str]:
    """ return [srcnetid, desnetid] of the users involved in the request"""
    assert session is not None
    row = session.query(db.Request).filter(db.Request.requestid == requestid).one()

    return [row.srcnetid, row.destnetid]


@db.session_decorator(commit=False)
def get_request_stamps(requestid: int, *, session: Optional[Session] = None) -> List[datetime]:
    """ return [make, accept, delete] timestamps"""
    assert session is not None
    row = session.query(db.Request).filter(db.Request.requestid == requestid).one()

    return [row.maketimestamp, row.accepttimestamp, row.deletetimestamp, row.finalizedtimestamp]


@db.session_decorator(commit=False)
def get_request_status(requestid: int, *, session: Optional[Session] = None) -> db.RequestStatus:
    """Return request status of a requestid. If the request is not found, raises an exception."""
    assert session is not None
    row = session.query(db.Request.status).filter(db.Request.requestid == requestid).scalar()
    if row is None:
        raise RequestNotFound(requestid)
    return row[0]


@db.session_decorator(commit=False)
def get_request_schedule(requestid: int,
                         *,
                         session: Optional[Session] = None) -> List[db.TimeBlock]:
    """ return timeblocks associated with request"""
    assert session is not None
    row = session.query(db.Request).filter(db.Request.requestid == requestid).one()
    return row.schedule


# probably not necessary
@db.session_decorator(commit=False)
def incoming_requests(destnetid: str,
                      *,
                      session: Optional[Session] = None) -> Dict[int, db.RequestStatus]:
    """get a list of incoming matches associatec with a user"""
    assert session is not None
    rows: List[db.MappedRequest] = session.query(
        db.Request).filter(db.Request.destnetid == destnetid).order_by(db.Request.srcnetid).all()
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
    return _get(session, requestid, (column,))[0]


# TODO: add timestamps
@db.session_decorator(commit=True)
def new(srcnetid: str,
        destnetid: str,
        schedule: List[db.ScheduleStatus],
        *,
        session: Optional[Session] = None,
        prev: Optional[db.MappedRequest] = None) -> bool:
    """Make a new outgoing request from user 'srcnetid' to user 'destnetid' with the proposed
    'schedule'. If an active 'prevrequest' is specified, then rejects or terminates 'prevrequest',
    and sets prevrequestid in the newly created request. Returns the new request object if
    successful. If there is already a pending or finalized request between 'srcnetid' and
    'destnetid', or if the specified 'prevrequest' is not active, then returns False."""
    assert session is not None
    assert len(schedule) == db.NUM_WEEK_BLOCKS
    for netid in (srcnetid, destnetid):
        if not db_user.has_user(netid):
            raise db_user.UserNotFound(netid)

    if get_active(srcnetid, destnetid, session=session) and prev is None:
        return False

    prevrequestid: int = 0
    if prev:
        if prev.status == db.RequestStatus.PENDING:
            prev.status = db.RequestStatus.REJECTED
        elif prev.status == db.RequestStatus.FINALIZED:
            prev.status = db.RequestStatus.TERMINATED
        else:
            return False

    request = db.Request(srcnetid=srcnetid,
                         destnetid=destnetid,
                         maketimestamp=datetime.now(),
                         status=db.RequestStatus.PENDING,
                         schedule=schedule,
                         prevrequestid=prevrequestid)
    session.add(request)

    return True


@db.session_decorator(commit=True)
def finalize(requestid: int, *, session: Optional[Session] = None) -> bool:
    """finalize the request by approving the accept request"""
    assert session is not None
    request = _get(session, requestid)
    if request.status != db.RequestStatus.PENDING:
        return False

    request.finalizedtimestamp = datetime.now()  # TODO: specify timezone
    request.status = db.RequestStatus.FINALIZED

    return True


@db.session_decorator(commit=True)
def reject(requestid: int, *, session: Optional[Session] = None) -> bool:
    """delete outgoing request"""
    assert session is not None
    request = _get(session, requestid)
    if request.status != db.RequestStatus.PENDING:
        return False

    request.status = db.RequestStatus.REJECTED
    return True


@db.session_decorator(commit=True)
def terminate(requestid: int, *, session: Optional[Session] = None) -> bool:
    """delete outgoing request"""
    assert session is not None
    request = _get(session, requestid)
    if request.status != db.RequestStatus.FINALIZED:
        return False

    request.status = db.RequestStatus.TERMINATED
    return True


@db.session_decorator(commit=True)
def modify(requestid: int,
           schedule: List[db.ScheduleStatus],
           *,
           session: Optional[Session] = None) -> bool:
    """Modifies active (pending or matching) request."""
    assert session is not None
    request = _get(session, requestid)
    return bool(new(request.srcnetid, request.destnetid, schedule, session=session, prev=request))
