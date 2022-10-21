"""Database API"""
from typing import List
import db

#### Scheduling ####
# return schedule informing occupied times of user
# list will be of size 2016 (7 * 24 * 12)
def get_schedule(userId: int) -> List[str]:
    return []
# update a time to be occupied on userend
def add_time(userId: int, time: db.TimeBlock, eventtype: str) -> bool:
    return False
# update a time to be available on userend
def delete_time(user) -> bool:
    return False
# return schedule from str to an object form
def parse_schedule(schedule: str) -> List[str]:
    return []
# return schedule specifically showing time of matches
def get_match_schedule(userId: int) -> List[str]:
    return []
