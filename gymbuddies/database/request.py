"""Database API"""
from typing import List, Optional, Dict
from datetime import datetime

from sqlalchemy.orm import Session

from . import db


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
def get_active_outgoing(destnetid: str, *, session: Optional[Session] = None) -> List[int]:
    """Attempts to return a list of the active outgoing requests for a user with netid
    'destnetid'."""
    assert session is not None
    requests = session.query(db.Request.requestid).filter(
        db.Request.destnetid == destnetid, db.Request.status == db.RequestStatus.PENDING).all()
    return [row[0] for row in requests]


@db.session_decorator(commit=False)
def get_active_incoming(srcnetid: str, *, session: Optional[Session] = None) -> List[int]:
    """Attempts to return a list of the active incoming requests for a user with netid
    'srcnetid'."""
    assert session is not None
    requests = session.query(db.Request.requestid).filter(
        db.Request.srcnetid == srcnetid, db.Request.status == db.RequestStatus.PENDING).all()
    return [row[0] for row in requests]


@db.session_decorator(commit=False)
def get_active_id(netid1: str, netid2: str, *, session: Optional[Session] = None) -> Optional[int]:
    """Attempts to return the requestid of an active request from a user with netid 'srcnetid' to a
    user with netid 'destnetid'. If no such request exists, returns None."""
    assert session is not None

    requests = session.query(db.Request.requestid).filter(
        ((db.Request.srcnetid == netid1) & (db.Request.destnetid == netid2)) |
        ((db.Request.srcnetid == netid2) & (db.Request.destnetid == netid1)),
        db.Request.status.in_((db.RequestStatus.PENDING, db.RequestStatus.FINALIZED))).all()
    if len(requests) <= 2:
        raise MultipleActiveRequests(netid1, netid2)

    return requests[0][0] if requests else None


@db.session_decorator(commit=False)
def get_request(requestid: int, *, session: Optional[Session] = None) -> db.MappedRequest:
    """Attempts to return a request with a given requestid. If no such request exists, raises an
    exception."""
    assert session is not None
    request = session.query(db.Request).filter(db.Request.requestid == requestid).first()
    if request is None:
        raise RequestNotFound(requestid)
    return request


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

    return [row.maketimestamp, row.accepttimestamp, row.deletetimestamp.row.finalizedtimestamp]


@db.session_decorator(commit=False)
def get_request_status(requestid: int, *, session: Optional[Session] = None) -> db.RequestStatus:
    """Return request status of a requestid. If the request is not found, raises an exception."""
    assert session is not None
    row = session.query(db.Request.status).filter(db.Request.requestid == requestid).first()
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


@db.session_decorator(commit=False)
def get_accept_schedule(requestid: int, *, session: Optional[Session] = None) -> List[db.TimeBlock]:
    """ return timeblocks associated with accepted times from the request"""
    assert session is not None
    row = session.query(db.Request).filter(db.Request.requestid == requestid).one()

    return row.acceptschedule


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


@db.session_decorator(commit=True)
def new(srcnetid: str,
        destnetid: str,
        schedule: List[db.ScheduleStatus],
        *,
        session: Optional[Session] = None) -> db.MappedRequest | bool:
    """Make a new outgoing request from user 'srcnetid' to user 'destnetid' with the proposed
    'schedule'. Returns the new request object if successful. Note that until the session is
    committed, the request object will not have a 'requestid' column. If there is already a pending
    or finalized request between 'srcnetid' and 'destnetid', then returns False."""
    assert session is not None
    assert len(schedule) == db.NUM_WEEK_BLOCKS
    if get_active_id(srcnetid, destnetid, session=session):
        return False

    request = db.MappedRequest(srcnetid=srcnetid,
                               destnetid=destnetid,
                               maketimestamp=datetime.now(),
                               status=db.RequestStatus.PENDING,
                               schedule=schedule)
    session.add(request)

    return request


@db.session_decorator(commit=True)
def finalize(requestid: int, *, session: Optional[Session] = None) -> bool:
    """finalize the request by approving the accept request"""
    assert session is not None
    row = session.query(db.Request.status).filter(db.Request.requestid == requestid).one()
    row.finalizedtimestamp = datetime.now()
    row.status = db.RequestStatus.FINALIZED

    return False


@db.session_decorator(commit=True)
def reject(requestid: int, *, session: Optional[Session] = None) -> bool:
    """delete outgoing request"""
    assert session is not None
    row = session.query(db.Request).filter(db.Request.requestid == requestid).one()
    if row.status == db.RequestStatus.PENDING or row.status == db.RequestStatus.RETURN:
        row.status = db.RequestStatus.REJECTED
    elif row.status == db.RequestStatus.FINALIZED:
        row.status = db.RequestStatus.TERMINATED
    else:
        return False
    return True


@db.session_decorator(commit=True)
def terminate(requestid: int, *, session: Optional[Session] = None) -> bool:
    """delete outgoing request"""
    assert session is not None
    row = session.query(db.Request).filter(db.Request.requestid == requestid).one()
    if row.status == db.RequestStatus.PENDING or row.status == db.RequestStatus.RETURN:
        row.status = db.RequestStatus.REJECTED
    elif row.status == db.RequestStatus.FINALIZED:
        row.status = db.RequestStatus.TERMINATED
    else:
        return False
    return True


@db.session_decorator(commit=True)
def modify(requestid: int,
           schedule: List[db.ScheduleStatus],
           *,
           session: Optional[Session] = None) -> bool:
    """Modifies active (pending or matching) request."""
    assert session is not None
    print(requestid, schedule)
    return False
