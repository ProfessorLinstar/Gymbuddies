"""Database API"""

#### User creation ####
# create_user(user info...)
# update_user(userid, user info...)
# delete_user(userid)

#### Matching ####
# query_matches(user)
# incoming_requests(destuser)
# outgoing_requests(srcuser)
# make_request(srcuser, destuser, times)
# accept_request(requestid)
# delete_request(srcuser, destuser, times)

#### Scheduling ####
# get_schedule(user)
# add_time(user)
# delete_time(user)
# parse_schedule(schedule: str)
