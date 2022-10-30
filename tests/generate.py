"""Collection of functions for generating sample data for the database."""
import json
from typing import Dict, Any, Tuple, List
from gymbuddies.database import db
from gymbuddies import database


def schedule_from_dayhours(*day_hours: Tuple[int, int]):
    """Given arguments of the form (day, hour), returns a schedule with UNAVAILABLE in every block
    except for the specified times."""

    schedule: List[int] = [db.ScheduleStatus.UNAVAILABLE] * db.NUM_WEEK_BLOCKS
    for day, hour in day_hours:
        start: db.TimeBlock = db.TimeBlock.from_daytime(day, hour * db.NUM_HOUR_BLOCKS)
        for i in range(start, start + db.NUM_HOUR_BLOCKS):
            schedule[i] = db.ScheduleStatus.AVAILABLE

    return schedule


def users():
    """Initializes a group of users in the database."""
    data: Dict[str, Any] = {
        "andywang": {
            "netid": "andywang",
            "name": "Andy Wang",
            "contact": "919-265-8342",
            "level": "0",
            "bio": "I go to Princeton!",
            "addinfo": "):<",
            "interests": {
                "Pecs": True,
                "Legs": True,
            },
            # "schedule": schedule_from_dayhours((1, 7), (1, 8), (1, 9))
            "schedule": [db.ScheduleStatus.AVAILABLE] * db.NUM_WEEK_BLOCKS
        },
        "ejcho": {
            "netid": "ejcho",
            "name": "Joy Cho",
            "contact": "ejcho@princeton.edu",
            "level": "0",
            "bio": "I go to Princeton!",
            "addinfo": "):<",
            "interests": {},
            "schedule": schedule_from_dayhours((1, 7), (1, 8), (1, 9))
        },
        "jasono": {
            "netid": "jasono",
            "name": "Jason Oh",
            "contact": "jasono@princeton.edu",
            "level": "2",
            "addinfo": "):<",
            "bio": "I go to Princeton!",
            "interests": {},
            "schedule": schedule_from_dayhours((1, 7), (1, 8), (1, 9))
        },
        "eyc2": {
            "netid": "eyc2",
            "name": "Genie Choi",
            "contact": "eyc2@princeton.edu",
            "level": "0",
            "bio": "I go to Princeton!",
            "addinfo": "):<",
            "interests": {},
            "schedule": schedule_from_dayhours((1, 7), (1, 8), (1, 9))
        },
    }

    for user in data.values():
        print(json.dumps({k: str(v) for k, v in user.items()}, sort_keys=True, indent=4))

    for user in data.values():
        if database.user.has_user(user["netid"]):
            database.user.update(**user)
        else:
            database.user.create(**user)


def main():
    """Calls all database initialization functions."""
    users()


if __name__ == "__main__":
    main()
