"""Database API"""
from typing import List, Optional, Dict, Tuple, Any
from datetime import datetime, timezone
from sqlalchemy import Column
from sqlalchemy.orm import Session
from . import db
from . import user as usermod
from . import schedule as schedulemod

LIMIT = 5


class RequestWhileClosed(Exception):
    """Exception raise in an API call if a user attempts to make a request while not being open to
    matching."""

    def __init__(self):
        super().__init__(f"User is not open for matching. Unable to make request.")


class RequestToClosedUser(Exception):
    """Exception raise in an API call if a user attempts to make a request to a user who is not open
    to matching."""

    def __init__(self, closed: str):
        self.closed = closed
        super().__init__(f"User {closed} is not open for matching. Unable to make request.")


class RequestToBlockedUser(Exception):
    """Exception raise in an API call if a user attempts to make a request to a blocked user a user
    that has blocked them."""

    blocker: str
    blocked: str

    def __init__(self, blocker: str, blocked: str):
        self.blocker = blocker
        self.blocked = blocked
        super().__init__(f"User {blocked} blocked by user {blocker}. Unable to make request.")


class RequestAlreadyExists(Exception):
    """Exception raised in API call if attempting to create multiple active requests."""

    srcnetid: str
    destnetid: str

    def __init__(self, srcnetid: str, destnetid: str):
        self.srcnetid = srcnetid
        self.destnetid = destnetid
        super().__init__(f"Active request between '{srcnetid}' and '{destnetid}' already exists.")


class PreviousRequestInactive(Exception):
    """Exception raised in API call if attempting to modify a request that is no longer active."""

    def __init__(self):
        super().__init__("Previous request to be modified must be active.")


class RequestToSelf(Exception):
    """Exception raised in API call if request made to oneself."""

    def __init__(self):
        super().__init__("A user cannot make a request to themself.")


class NoChangeModification(Exception):
    """Exception raised in API call if modification request made with no change to schedule."""

    def __init__(self):
        super().__init__("Invalid modification schedule. Request must change one or more blocks.")


class EmptyRequestSchedule(Exception):
    """Exception raised in API call if request made with empty schedule."""

    def __init__(self):
        super().__init__("Invalid request schedule. Request must have one or more selected blocks.")

class OverlapRequests(Exception):
    """Exception raised in API call if request overlaps with others."""

    requestid: int

    def __init__(self, requestid: int):
        self.requestid = requestid
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
    """Returns a list of the active outgoing requests for a user with netid 'destnetid',
    sorted in order with respect to the request's make timestamp, newest first. If 'destnetid' does
    not exist in the database, returns an empty list."""
    assert session is not None
    return session.query(db.Request).filter(db.Request.srcnetid == srcnetid,
                                            db.Request.status != db.RequestStatus.PENDING).order_by(
                                                db.Request.maketimestamp.desc()).all()


@db.session_decorator(commit=False)
def get_active_outgoing(srcnetid: str, *, session: Optional[Session] = None) -> List[Any]:
    """Returns a list of the active outgoing requests for a user with netid 'destnetid',
    sorted in order with respect to the request's make timestamp, newest first. If 'destnetid' does
    not exist in the database, returns an empty list."""
    assert session is not None
    return session.query(db.Request).filter(db.Request.srcnetid == srcnetid,
                                            db.Request.status == db.RequestStatus.PENDING).order_by(
                                                db.Request.maketimestamp.desc()).all()


@db.session_decorator(commit=False)
def get_inactive_incoming(destnetid: str, *, session: Optional[Session] = None) -> List[Any]:
    """Returns a list of the active incoming requests for a user with netid 'srcnetid',
    sorted in order with respect to the request's make timestamp, newest first. If 'srcnetid' does
    not exist in the database, returns an empty list."""
    assert session is not None
    return session.query(db.Request).filter(db.Request.destnetid == destnetid,
                                            db.Request.status != db.RequestStatus.PENDING).order_by(
                                                db.Request.maketimestamp.desc()).all()


@db.session_decorator(commit=True)
def get_active_incoming(destnetid: str, *, session: Optional[Session] = None) -> List[Any]:
    """Returns a list of the active incoming requests for a user with netid 'srcnetid',
    sorted in order with respect to the request's make timestamp, newest first. If 'srcnetid' does
    not exist in the database, returns an empty list."""
    assert session is not None

    requests = session.query(db.Request).filter(
        db.Request.destnetid == destnetid, db.Request.status == db.RequestStatus.PENDING).order_by(
            db.Request.maketimestamp.desc()).all()

    unread = [r for r in requests if not r.read]
    print(f"these requests are still unread: {unread = }")
    for request in unread:
        request.read = True
        session.add(request)
    if unread:
        usermod.update(destnetid, session=session)

    return requests


@db.session_decorator(commit=True)
def get_unread(netid: str, *, session: Optional[Session] = None) -> List[Tuple[str, int]]:
    """Returns a list of tuples of the form (netid, status) corresponding to the unread incoming
    requests and new matches of a user."""
    assert session is not None

    requests = session.query(db.Request.srcnetid, db.Request.destnetid, db.Request.status).filter(
        (db.Request.read == False) | (db.Request.read == None),
        ((db.Request.destnetid == netid) & (db.Request.status == db.RequestStatus.PENDING)) |
        ((db.Request.srcnetid == netid) & (db.Request.status == db.RequestStatus.FINALIZED)))

    return [(src if src != netid else dest, status) for src, dest, status in requests]


@db.session_decorator(commit=False)
def get_active_single(netid: str, *, session: Optional[Session] = None) -> List[db.MappedRequest]:
    """Returns the requestid of an active request from a user with netid 'srcnetid' to a
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
    """Returns the requestid of an active request from a user with netid 'srcnetid' to a
    user with netid 'destnetid'. If no such request exists, returns None."""
    assert session is not None

    return session.query(db.Request).filter(
        ((db.Request.srcnetid == netid1) & (db.Request.destnetid == netid2)) |
        ((db.Request.srcnetid == netid2) & (db.Request.destnetid == netid1)),
        db.Request.status.in_((db.RequestStatus.PENDING, db.RequestStatus.FINALIZED))).scalar()


@db.session_decorator(commit=False)
def get_request(requestid: int, *, session: Optional[Session] = None) -> db.MappedRequest:
    """Returns a request with a given requestid. If no such request exists, raises a
    RequestNotFound exception."""
    assert session is not None
    return _get(session, requestid)


@db.session_decorator(commit=False)
def get_srcnetid(requestid: int, *, session: Optional[Session] = None) -> str:
    """Returns the srcnetid of a request with id 'requestid'. If no such request exists,
    raises a RequestNotFound exception."""
    assert session is not None
    return _get_column(session, requestid, db.Request.srcnetid)


@db.session_decorator(commit=False)
def get_destnetid(requestid: int, *, session: Optional[Session] = None) -> str:
    """Returns the srcnetid of a request with id 'requestid'. If no such request exists,
    raises a RequestNotFound exception."""
    assert session is not None
    return _get_column(session, requestid, db.Request.destnetid)


@db.session_decorator(commit=True)
def get_matches(netid: str, *, session: Optional[Session] = None) -> List[db.MappedRequest]:
    """ get a list of matches associated with a user"""
    assert session is not None

    requests = session.query(db.Request).filter(
        (db.Request.srcnetid == netid) | (db.Request.destnetid == netid),
        db.Request.status == db.RequestStatus.FINALIZED).all()

    unread = [r for r in requests if not r.read and r.srcnetid == netid]
    print("get_matches unread:", unread)
    for request in unread:
        request.read = True
        session.add(request)
    if unread:
        usermod.update(netid, session=session)

    return requests


@db.session_decorator(commit=False)
def get_terminated(netid: str, *, session: Optional[Session] = None) -> List[db.MappedRequest]:
    """ get a list of matches associated with a user"""
    assert session is not None
    return session.query(db.Request).filter(
        (db.Request.srcnetid == netid) | (db.Request.destnetid == netid),
        db.Request.status == db.RequestStatus.TERMINATED).order_by(
            db.Request.deletetimestamp.desc()).limit(LIMIT).all()


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


@db.session_decorator(commit=True)
def new(srcnetid: str,
        destnetid: str,
        schedule: List[int] | List[db.ScheduleStatus],
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
    srcuser = usermod.get_user(srcnetid)
    destuser = usermod.get_user(destnetid)

    if srcnetid == destnetid:
        raise RequestToSelf

    if srcnetid in destuser.blocked:
        raise RequestToBlockedUser(destnetid, srcnetid)
    elif destnetid in srcuser.blocked:
        raise RequestToBlockedUser(srcnetid, destnetid)

    if all(not x for x in schedule):
        raise EmptyRequestSchedule

    prevrequestid: int = 0
    if prev is not None:
        prevrequestid = prev.requestid
        if all(bool(x) == bool(y) for x, y in zip(schedule, prev.schedule)):
            raise NoChangeModification
        if not _deactivate(session, prev):
            raise PreviousRequestInactive
    
    else:
        if not srcuser.open:
            raise RequestWhileClosed
        if not destuser.open:
            raise RequestToClosedUser(destnetid)


    if get_active_pair(srcnetid, destnetid, session=session):
        raise RequestAlreadyExists(srcnetid, destnetid)

    if any(x and (s & db.ScheduleStatus.MATCHED or d != db.ScheduleStatus.AVAILABLE)
           for x, s, d in zip(schedule, usermod.get_schedule(srcnetid, session=session),
                              usermod.get_schedule(destnetid, session=session))):
        raise ConflictingRequestSchedule

    request = db.Request(srcnetid=srcnetid,
                         destnetid=destnetid,
                         maketimestamp=datetime.now(timezone.utc),
                         status=db.RequestStatus.PENDING,
                         schedule=schedule,
                         prevrequestid=prevrequestid,
                         read=False)
    session.add(request)

    # Update user lastupdated timestamp by doing an empty update
    usermod.update(srcnetid, session=session)
    usermod.update(destnetid, session=session)

    print("Created a request with this schedule: ", db.schedule_to_readable(schedule))


@db.session_decorator(commit=False)
def get_conflicts(requestid: int, *, session: Optional[Session] = None) -> List[Tuple[str, str]]:
    """Returns requests with times conflicting with the request with the provided requestid."""
    assert session is not None
    request = _get(session, requestid)

    conflicts: List[Tuple[str, str]] = []
    for netid in (request.srcnetid, request.destnetid):
        for active in get_active_single(netid, session=session):
            if active.requestid == request.requestid:
                continue
            if any(x and y for x, y in zip(request.schedule, active.schedule)):
                conflicts.append((active.srcnetid, active.destnetid))

    return conflicts


@db.session_decorator(commit=True)
def finalize(requestid: int, *, session: Optional[Session] = None) -> None:
    """finalize the request by approving the accept request"""
    assert session is not None
    request = _get(session, requestid)

    for netid in (request.srcnetid, request.destnetid):
        # schedulemod.add_schedule_status(netid,
        #                                 request.schedule,
        #                                 db.ScheduleStatus.MATCHED,
        #                                 session=session)
        for active in get_active_single(netid, session=session):
            if active.requestid == request.requestid:
                continue
            if any(x and y for x, y in zip(request.schedule, active.schedule)):
                raise OverlapRequests(requestid)

    if request.status != db.RequestStatus.PENDING:
        raise RequestStatusMismatch(db.RequestStatus(request.status), db.RequestStatus.PENDING)

    request.finalizedtimestamp = datetime.now(timezone.utc)
    request.status = db.RequestStatus.FINALIZED
    request.read = False

    for netid in (request.srcnetid, request.destnetid):
        schedulemod.add_schedule_status(netid,
                                        request.schedule,
                                        db.ScheduleStatus.MATCHED,
                                        session=session)
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
    request.deletetimestamp = datetime.now(timezone.utc)

    # Update user lastupdated timestamp
    usermod.update(request.srcnetid, session=session)
    usermod.update(request.destnetid, session=session)


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

    print(f"request {request.requestid} will now be terminated!")
    for netid in (request.srcnetid, request.destnetid):
        schedulemod.remove_schedule_status(netid,
                                           request.schedule,
                                           db.ScheduleStatus.MATCHED,
                                           session=session)

    request.status = db.RequestStatus.TERMINATED
    request.deletetimestamp = datetime.now(timezone.utc)


def _deactivate(session: Session, request: db.MappedRequest) -> bool:
    """Deactivates a request if it is active. Returns True if a request was deactivated, and False
    otherwise."""
    if request.status == db.RequestStatus.PENDING:
        _reject(session, request)
    elif request.status == db.RequestStatus.FINALIZED:
        _terminate(session, request)
    else:
        return False
    return True


@db.session_decorator(commit=True)
def modify(requestid: int,
           schedule: List[db.ScheduleStatus] | List[int],
           *,
           session: Optional[Session] = None) -> None:
    """Modifies active (pending or matching) request. Switches direction of request."""
    assert session is not None

    print("trying to modify with this schedule: ", db.schedule_to_readable(schedule))

    request = _get(session, requestid)
    new(request.destnetid, request.srcnetid, schedule, session=session, prev=request)


@db.session_decorator(commit=True)
def modify_match(requestid: int,
                 netid: str,
                 schedule: List[db.ScheduleStatus] | List[int],
                 *,
                 session: Optional[Session] = None) -> None:
    """Modifies match times."""
    assert session is not None

    print("trying to modify with this schedule: ", db.schedule_to_readable(schedule))

    request = _get(session, requestid)

    srcuser = usermod.get_user(request.srcnetid)
    if srcuser != netid:
        destuser = srcuser
        srcuser = netid
    else:
        destuser = netid

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
