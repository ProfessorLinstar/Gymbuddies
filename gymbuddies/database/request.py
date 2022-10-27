"""Database API"""
from typing import List, Optional, Dict
from typing import cast
from datetime import datetime

from sqlalchemy.orm import Session

from . import db


# TODO: ERROR HANDLING FOR ALL OF THESE FUNCTIONS
#### Matching ####
@db.session_decorator(commit=False)
def get_matches(srcuserid: int, *, session: Optional[Session] = None) -> List[int]:
    """ get a list of matches associated with a user"""
    assert session is not None
    matches: List[int] = []
    rows = session.query(db.Request).filter(db.Request.srcuserid == srcuserid,
                                            db.Request.status == db.RequestStatus.FINALIZED).all()
    for row in rows:
        matches.append(row.requestid)
    rows = session.query(db.Request).filter(db.Request.destuserid == srcuserid,
                                            db.Request.status == db.RequestStatus.FINALIZED).all()
    for row in rows:
        matches.append(row.requestid)

    return matches


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
def incoming_requests(destnetid: int,
                      *,
                      session: Optional[Session] = None) -> dict[int, db.RequestStatus]:
    """get a list of incoming matches associatec with a user"""
    assert session is not None
    rows = session.query(db.Request).filter(db.Request.destnetid == destnetid).order_by(
        db.Request.srcnetid).all()
    incoming_request_statuses: Dict[int, db.RequestStatus] = {}
    for row in rows:
        incoming_request_statuses[row.requestid] = row.status

    return incoming_request_statuses


@db.session_decorator(commit=False)
def outgoing_requests(srcnetid: int,
                      *,
                      session: Optional[Session] = None) -> dict[int, db.RequestStatus]:
    """get a list of outgoing matches associated with a user"""
    assert session is not None
    rows = session.query(db.Request).filter(db.Request.srcnetid == srcnetid).order_by(
        db.Request.destnetid).all()
    outgoing_request_statuses: Dict[int, db.RequestStatus] = {}
    for row in rows:
        outgoing_request_statuses[row.requestid] = row.status
    return outgoing_request_statuses


@db.session_decorator(commit=True)
def make_request(srcnetid: int,
                 destnetid: int,
                 times: List[db.TimeBlock],
                 *,
                 session: Optional[Session] = None) -> int:
    """make a new outgoing request to another user with specific times"""
    assert session is not None
    request = db.Request(srcnetid=srcnetid,
                         destnetid=destnetid,
                         maketimestamp=datetime.now(),
                         status=db.RequestStatus.PENDING,
                         schedule=times)
    session.add(request)
    session.commit()
    # session.refresh(request) # insert line if session.commit() does not refresh request

    return cast(int, request.requestid)


@db.session_decorator(commit=True)
def accept_request(requestid: int, times: List[db.TimeBlock], *, session: Optional[Session] = None):
    """send the accept for the request, selecting the final schedule times"""
    assert session is not None
    row = session.query(db.Request).filter(db.Request.requestid == requestid).one()
    row.accepttimestamp = datetime.now()
    row.status = db.RequestStatus.RETURN
    session.commit()


def finalize_request(requestid: int, *, session: Optional[Session] = None):
    """finalize the request by approving the accept request"""
    assert session is not None
    row = session.query(db.Request).filter(db.Request.requestid == requestid).one()
    row.finalizedtimestamp = datetime.now()
    row.status = db.RequestStatus.FINALIZED
    session.commit()


@db.session_decorator(commit=True)
def delete_request(requestid: int, *, session: Optional[Session] = None):
    """delete outgoing request"""
    assert session is not None
    row = session.query(db.Request).filter(db.Request.requestid == requestid).one()
    if row.status == db.RequestStatus.PENDING or row.status == db.RequestStatus.RETURN:
        row.status = db.RequestStatus.REJECTED
    elif row.status == db.RequestStatus.FINALIZED:
        row.status = db.RequestStatus.TERMINATED
    else:
        pass
    row.commit()
