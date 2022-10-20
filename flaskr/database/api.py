"""Database API"""

#### User creation ####
# create user using relevant information
def create_user(userid, userinfo...) -> ok
# update user info (listed in the Users table)
def update_user(userid, userinfo...) -> ok
# remove user from database
def delete_user(userid) -> ok

### User information ###
# return name associated with userid
def get_name(userId: int) -> str
# return bio associated with userid
def get_bio(userId: int) -> str
# return level assciate with userid
def get_level(userId: int) -> str
# return additional into associated with userid
def get_additionalInfo(userId: int) -> str

#### Matching ####
# get a list of matches associated with a user
def get_matches(srcUserId: int) -> dict[destUserId: int, status: int]
# get a list of incoming matches associated with a user
def incoming_requets(srcUserId: int) -> dict[destUserId: int, status: int]
# get a list of outgoing matches associated with a user
def outgoing_requets(srcUserId: int) -> dict[destUserId: int, status: int]
# make an outgoing request to another user with specific times
def make_request(srcUserId: int, destUserId: int, times: list[Time])
# accept incoming request
def accept_request(srcUserId: int, requestId: int)
# delete outgoing request
def delete_request(srcUserId: int, requestId: int)

#### Scheduling ####
# return schedule informing occupied times of user
# list will be of size 2016 (7 * 24 * 12)
def get_schedule(userId: int) -> list[str]
# update a time to be occupied on userend
def add_time(userId: int, time: Time, eventtype: str) -> ok
# update a time to be available on userend
def delete_time(user) -> ok
# return schedule from str to an object form
def parse_schedule(schedule: str) -> list[str]
# return schedule specifically showing time of matches
def get_match_schedule(userId: int) -> list[str]
