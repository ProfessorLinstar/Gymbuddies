"""Database API"""
import db

#### User creation ####
# create user using relevant information
def create_user(userid, userinfo) -> bool:
    return False
# update user info (listed in the Users table)
def update_user(userid, userinfo) -> bool:
    return False
# remove user from database
def delete_user(userid) -> bool:
    return False

### User information ###
# return name associated with userid
def get_name(userId: int) -> str:
    return ""
# return bio associated with userid
def get_bio(userId: int) -> str:
    return ""
# return level assciate with userid
def get_level(userId: int) -> str:
    return ""
# return additional into associated with userid
def get_additionalInfo(userId: int) -> str:
    return ""
