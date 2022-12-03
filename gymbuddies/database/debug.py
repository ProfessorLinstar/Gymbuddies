"""Database debug and diagnostics functions."""

import json

from typing import Any, Generator, Dict
from . import db
from . import user as db_user
from . import request as db_request


def sprint_users(*criterions) -> Generator[str, None, None]:
    """Yields a generator whose elements are strings representing a user in json format."""

    users = db_user.get_users(*criterions)
    if users is None:
        return

    for u in users:
        yield sprintv(u)


def print_users(*criterions) -> None:
    """Like sprint_users, but prints out each user instead."""
    for s in sprint_users(*criterions):
        print(s)


def sprintv(x: Any) -> str:
    """Prints the attributes of 'x' in json format."""
    return json.dumps({k: str(v) for k, v in vars(x).items() if "_" not in k},
                      sort_keys=True,
                      indent=4)


def printv(x: Any) -> None:
    """Like sprint_users, but prints out each user instead."""
    print(sprintv(x))


def sprint_requests(requests: Dict[int, db.RequestStatus]) -> str:
    """Returns a formatted string of a 'requests', dictionary of request_id's and the corresponding
    RequestStatus."""
    return json.dumps(
        {
            requestid: {
                "id": requestid,
                "srcnetid": db_request.get_srcnetid(requestid),
                "destnetid": db_request.get_destnetid(requestid),
                "status": status.to_readable(),
            } for requestid, status in requests.items()
        },
        sort_keys=True,
        indent=4)
