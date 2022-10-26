"""Database API"""
from typing import List, Optional, Dict
from datetime import datetime

from sqlalchemy.orm import Session

from . import db

#### Matching ####
def get_matches(srcuserid: int) -> dict[int, db.RequestStatus]:
    """ get a list of matches associated with a user"""
    return {}


@db.session_decorator
def get_request_users(requestid: int, *, session: Optional[Session] = None) -> List[string]:
    assert session is not None
    row = session.query()

    return []


@db.session_decorator
def get_request_stamps(requestid: int, *, session: Optional[Session] = None) -> List[datetime]:
    return []


@db.session_decorator
def get_request_status(requestid: int, *, session: Optional[Session] = None) -> db.RequestStatus:
    return


@db.session_decorator
def get_request_schedule(requestid: int, *, session: Optional[Session] = None) -> List[db.TimeBlock]:
    return []


@db.session_decorator
def incoming_requests(destnetid: int, *, session: Optional[Session] = None) -> dict[
    int, db.RequestStatus]:
    """get a list of incoming matches associatec with a user"""
    assert session is not None
    rows = session.query(db.Request).filter(db.Request.destnetid == destnetid).order_by(
        db.Request.srcnetid).all()
    incoming_request_statuses: Dict[int, db.RequestStatus] = {}
    for row in rows:
        incoming_request_statuses[row.requestid] = row.status
    return incoming_request_statuses


@db.session_decorator
def outgoing_requests(srcnetid: int, *, session: Optional[Session] = None) -> dict[
    int, db.RequestStatus]:
    """get a list of outgoing matches associated with a user"""
    assert session is not None
    rows = session.query(db.Request).filter(db.Request.srcnetid == srcnetid).order_by(
        db.Request.destnetid).all()
    outgoing_request_statuses: Dict[int, db.RequestStatus] = {}
    for row in rows:
        outgoing_request_statuses[row.requestid] = row.status
    return outgoing_request_statuses


@db.session_decorator
def make_request(srcnetid: int, destnetid: int, times: List[
    db.TimeBlock], *, session: Optional[Session] = None) -> int:
    """make a new outgoing request to another user with specific times"""
    assert session is not None
    request = db.Request(
        srcnetid = srcnetid,
        destnetid = destnetid,
        maketimestamp = datetime.now(),
        status = db.RequestStatus.PENDING,
        schedule = times
        )
    session.add(request)
    session.commit()
    session.refresh(request)
    return request.requestid


@db.session_decorator
def accept_request(request_id: int, *, session: Optional[Session] = None):
    """ accept incoming request"""
    assert session is not None

    return


@db.session_decorator
def delete_request(request_id: int, *, session: Optional[Session] = None):
    """delete outgoing request"""
    assert session is not None

    return
