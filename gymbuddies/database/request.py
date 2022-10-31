"""Database API"""
from typing import List, Optional, Dict, Any
from typing import cast
from datetime import datetime

from sqlalchemy.orm import Session

from . import db


class RequestNotFound(Exception):
    """Exception raised in API call if user required but not found in database."""

    def __init__(self, message: str = "", requestid: Optional[int] = None):
        if message:
            pass
        elif requestid is not None:
            message = f"Request with requestid '{requestid}' not found in the database."
        else:
            message = "Request not found in the database."
        super().__init__(message)


# TODO: ERROR HANDLING FOR ALL OF THESE FUNCTIONS


@db.session_decorator(commit=False)
def get_active_outgoing(destnetid: str, *, session: Optional[Session] = None) -> List[int]:
    """Attempts to return a list of the active outgoing requests for a user with netid
    'destnetid'."""
    assert session is not None
    requests = session.query(db.Request.requestid).filter(
        db.Request.destnetid == destnetid, db.Request.status == db.RequestStatus.PENDING).all()
    return [r.requestid for r in cast(List[Any], requests)]


@db.session_decorator(commit=False)
def get_active_incoming(srcnetid: str, *, session: Optional[Session] = None) -> List[int]:
    """Attempts to return a list of the active incoming requests for a user with netid
    'srcnetid'."""
    assert session is not None
    requests = session.query(db.Request.requestid).filter(
        db.Request.srcnetid == srcnetid, db.Request.status == db.RequestStatus.PENDING).all()
    return [r.requestid for r in cast(List[Any], requests)]


@db.session_decorator(commit=False)
def get_active_id(srcnetid: str,
                  destnetid: str,
                  *,
                  session: Optional[Session] = None) -> Optional[int]:
    """Attempts to return the requestid of an active request from a user with netid 'srcnetid' to a
    user with netid 'destnetid'. If no such request exists, returns None."""
    assert session is not None
    request = session.query(db.Request.requestid).filter(
        db.Request.srcnetid == srcnetid, db.Request.destnetid == destnetid,
        db.Request.status.in_((db.RequestStatus.PENDING, db.RequestStatus.FINALIZED))).first()
    return cast(Any, request).requestid if request is not None else None


@db.session_decorator(commit=False)
def get_request(requestid: int, *, session: Optional[Session] = None) -> db.MappedRequest:
    """Attempts to return a request with a given requestid. If no such request exists, raises an
    exception."""
    assert session is not None
    request = session.query(db.Request).filter(db.Request.requestid == requestid).first()
    if request is None:
        raise RequestNotFound(requestid=requestid)
    return request


@db.session_decorator(commit=False)
def get_matches(netid: str, *, session: Optional[Session] = None) -> List[int]:
    """ get a list of matches associated with a user"""
    assert session is not None
    requestids = session.query(db.Request.requestid).filter(
        (db.Request.srcnetid == netid) | (db.Request.destnetid == netid),
        db.Request.status == db.RequestStatus.FINALIZED).all()

    return [r.requestid for r in cast(List[Any], requestids)]


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
    """ return request status"""
    assert session is not None
    row = session.query(db.Request).filter(db.Request.requestid == requestid).one()
    return row.status


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
def make_request(srcnetid: str,
                 destnetid: str,
                 schedule: List[db.ScheduleStatus],
                 *,
                 session: Optional[Session] = None) -> db.MappedRequest:
    """make a new outgoing request to another user with specific times"""
    assert session is not None
    assert len(schedule) == db.NUM_WEEK_BLOCKS
    # TODO: use get_active to check if there is already an active request
    request = db.MappedRequest(srcnetid=srcnetid,
                               destnetid=destnetid,
                               maketimestamp=datetime.now(),
                               status=db.RequestStatus.PENDING,
                               schedule=schedule)
    session.add(request)

    return request


@db.session_decorator(commit=True)
def accept_request(requestid: int, *, session: Optional[Session] = None):
    """send the accept for the request, selecting the final schedule times"""
    assert session is not None
    row = session.query(db.Request).filter(db.Request.requestid == requestid).one()
    row.accepttimestamp = datetime.now()
    row.status = db.RequestStatus.RETURN


@db.session_decorator(commit=True)
def finalize_request(requestid: int, *, session: Optional[Session] = None):
    """finalize the request by approving the accept request"""
    assert session is not None
    row = session.query(db.Request).filter(db.Request.requestid == requestid).one()
    row.finalizedtimestamp = datetime.now()
    row.status = db.RequestStatus.FINALIZED


@db.session_decorator(commit=True)
def delete_request(requestid: int, *, session: Optional[Session] = None) -> bool:
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
