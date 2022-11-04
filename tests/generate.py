"""Collection of functions for generating sample data for the database."""
import json
import random
from typing import Tuple, List
from gymbuddies.database import db
from gymbuddies import database

STR_LENGTH = 20
UNI_CHARS = "".join([chr(i) for i in range(1, 10000)])


def schedule_from_dayhours(*day_hours: Tuple[int, int]):
    """Given arguments of the form (day, hour), returns a schedule with UNAVAILABLE in every block
    except for the specified times."""

    data: List[int] = [db.ScheduleStatus.UNAVAILABLE] * db.NUM_WEEK_BLOCKS
    for day, hour in day_hours:
        start: db.TimeBlock = db.TimeBlock.from_daytime(day, hour * db.NUM_HOUR_BLOCKS)
        for i in range(start, start + db.NUM_HOUR_BLOCKS):
            data[i] = db.ScheduleStatus.AVAILABLE

    return data


def users():
    """Initializes a group of users in the database."""
    data = {
        "andywang": {
            "netid": "andywang",
            "name": "Andy Wang",
            "contact": "919-265-8342",
            "level": 0,
            "levelpreference": 1,
            "bio": "I go to Princeton!",
            "addinfo": "):<",
            "interests": {
                "Cardiovascular Fitness": True,
                "Building Mass": True,
            },
            # "schedule": schedule_from_dayhours((1, 7), (1, 8), (1, 9))
            "schedule": [db.ScheduleStatus.AVAILABLE] * db.NUM_WEEK_BLOCKS,
            "open": True,
            "gender": db.Gender.MALE,
            "okmale": True,
            "okfemale": False,
            "okbinary": True,
            "settings": {},
        },
        "ejcho": {
            "netid": "ejcho",
            "name": "Joy Cho",
            "contact": "ejcho@princeton.edu",
            "level": 0,
            "levelpreference": 0,
            "bio": "I go to Princeton!",
            "addinfo": "):<",
            "interests": {},
            "schedule": schedule_from_dayhours((1, 7), (1, 8), (1, 9)),
            "open": True,
            "gender": db.Gender.FEMALE,
            "okmale": True,
            "okfemale": False,
            "okbinary": True,
            "settings": {},
        },
        "jasono": {
            "netid": "jasono",
            "name": "Jason Oh",
            "contact": "jasono@princeton.edu",
            "level": "2",
            "levelpreference": 0,
            "addinfo": "):<",
            "bio": "I go to Princeton!",
            "interests": {},
            "schedule": schedule_from_dayhours((1, 7), (1, 8), (1, 9)),
            "open": True,
            "gender": db.Gender.MALE,
            "okmale": False,
            "okfemale": True,
            "okbinary": True,
            "settings": {},
        },
        "eyc2": {
            "netid": "eyc2",
            "name": "Genie Choi",
            "contact": "eyc2@princeton.edu",
            "level": 0,
            "levelpreference": 0,
            "bio": "I go to Princeton!",
            "addinfo": "):<",
            "interests": {},
            "schedule": schedule_from_dayhours((1, 7), (1, 8), (1, 9)),
            "open": True,
            "gender": db.Gender.FEMALE,
            "okmale": False,
            "okfemale": True,
            "okbinary": True,
            "settings": {},
        },
    }
    for datum in data.values():
        a = sorted(datum.keys())
        b = sorted(db.User.__table__.columns.keys())
        assert a == b, f"Missing columns: {a} vs {b}"

    for user in data.values():
        print(json.dumps({k: str(v) for k, v in user.items()}, sort_keys=True, indent=4))

    for user in data.values():
        if database.user.exists(user["netid"]):
            database.user.update(**user)
        else:
            database.user.create(**user)


def requests():
    """Generates sample requests."""
    data = [
        {
            "srcnetid": "andywang",
            "destnetid": "jasono",
            "schedule": schedule_from_dayhours((1, 7)),
        },
        {
            "srcnetid": "ejcho",
            "destnetid": "andywang",
            "schedule": schedule_from_dayhours((1, 8)),
        },
    ]
    for request in data:
        database.request.new(request["srcnetid"], request["destnetid"], request["schedule"])


def schedule():
    """Returns a randomly generate calendar."""
    return [
        db.ScheduleStatus.AVAILABLE if random.random() < .5 else db.ScheduleStatus.UNAVAILABLE
        for _ in range(db.NUM_WEEK_BLOCKS)
    ]


def profile(netid):
    """Returns a randomly generated profile with a given netid."""
    return {
        "netid": netid,
        "name": unistr(),
        "contact": unistr(),
        "level": db.Level(random.randint(0, 2)),
        "levelpreference": random.randint(0, 2),
        "bio": unistr(),
        "addinfo": unistr(),
        "interests": {},
        "open": bool(random.randint(0, 1)),
        "okmale": bool(random.randint(0, 1)),
        "okfemale": bool(random.randint(0, 1)),
        "okbinary": bool(random.randint(0, 1)),
        "schedule": schedule(),
        "settings": {}
    }


def unistr(str_length: int = 0, source: str = UNI_CHARS) -> str:
    """generates a random string with the given properties"""
    if str_length == 0:
        str_length = random.randint(1, STR_LENGTH)
    return ''.join((random.choice(source) for _ in range(str_length)))


def main():
    """Calls database initialization functions."""
    users()
    requests()


if __name__ == "__main__":
    main()
