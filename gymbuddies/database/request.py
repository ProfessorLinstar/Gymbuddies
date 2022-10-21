"""Database API"""
from typing import List
import db

#### Matching ####
# get a list of matches associated with a user
def get_matches(srcUserId: int) -> dict[int, db.RequestStatus]:
    return {}
# get a list of incoming matches associated with a user
def incoming_requests(srcUserId: int) -> dict[int, db.RequestStatus]:
    return {}
# get a list of outgoing matches associated with a user
def outgoing_requests(srcUserId: int) -> dict[int, db.RequestStatus]:
    return {}
# make an outgoing request to another user with specific times
def make_request(srcUserId: int, destUserId: int, times: List[db.TimeBlock]):
    return
# accept incoming request
def accept_request(srcUserId: int, requestId: int):
    return
# delete outgoing request
def delete_request(srcUserId: int, requestId: int):
    return
