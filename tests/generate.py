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
            "contact": "3333333333",
            "level": db.Level.BEGINNER,
            "levelpreference": db.LevelPreference.ALL,
            "bio": "I enjoy playing Soccer!",
            "addinfo": "):<",
            "interests": {
                "Cardiovascular Fitness": True,
                "Building Mass": True,
            },
            "schedule": schedule_from_dayhours((0, 6), (1, 7), (2, 8)),
            "open": True,
            "gender": db.Gender.MALE,
            "okmale": True,
            "okfemale": True,
            "okbinary": True,
            "settings": {},
            "blocked": [],
        },
        "ejcho": {
            "netid": "ejcho",
            "name": "Joy Cho",
            "contact": "3333333333",
            "level": db.Level.INTERMEDIATE,
            "levelpreference": db.LevelPreference.ALL,
            "bio": "I enjoy playing Basketball!",
            "addinfo": "):<",
            "interests": {
                "Cardiovascular Fitness": True,
                "Lower Body": True,
            },
            "schedule": schedule_from_dayhours((1, 7), (2, 8), (3, 9)),
            "open": True,
            "gender": db.Gender.FEMALE,
            "okmale": True,
            "okfemale": True,
            "okbinary": True,
            "settings": {},
            "blocked": [],
        },
        "jasono": {
            "netid": "jasono",
            "name": "Jason Oh",
            "contact": "3333333333",
            "level": db.Level.INTERMEDIATE,
            "levelpreference": db.LevelPreference.ALL,
            "addinfo": "):<",
            "bio": "I enjoy playing Tennis!",
            "interests": {
                "Lower Body": True,
                "Upper Body": True,
            },
            "schedule": schedule_from_dayhours((2, 8), (3, 9), (4, 10)),
            "open": True,
            "gender": db.Gender.MALE,
            "okmale": True,
            "okfemale": True,
            "okbinary": True,
            "settings": {},
            "blocked": [],
        },
        "eyc2": {
            "netid": "eyc2",
            "name": "Genie Choi",
            "contact": "3333333333",
            "level": db.Level.BEGINNER,
            "levelpreference": db.LevelPreference.ALL,
            "bio": "I enjoy playing Baseball!",
            "addinfo": "):<",
            "interests": {
                "Cardiovascular Fitness": True,
                "Upper Body": True,
            },
            "schedule": schedule_from_dayhours((3, 9), (4, 10), (5, 11)),
            "open": True,
            "gender": db.Gender.FEMALE,
            "okmale": True,
            "okfemale": True,
            "okbinary": True,
            "settings": {},
            "blocked": [],
        },
        "jsnow": {
            "netid": "jsnow",
            "name": "Jon Snow",
            "contact": "3333333333",
            "level": db.Level.ADVANCED,
            "levelpreference": db.LevelPreference.ALL,
            "bio": "I enjoy playing Golf!",
            "addinfo": "):<",
            "interests": {
                "Gaining Mass": True,
                "Upper Body": True,
            },
            "schedule": schedule_from_dayhours((6, 10), (0, 11), (1, 12)),
            "open": True,
            "gender": db.Gender.MALE,
            "okmale": True,
            "okfemale": False,
            "okbinary": True,
            "settings": {},
            "blocked": [],
        },
        "dtargaryen": {
            "netid": "dtargaryen",
            "name": "Daenerys Targaryen",
            "contact": "3333333333",
            "level": db.Level.INTERMEDIATE,
            "levelpreference": db.LevelPreference.ALL,
            "bio": "I enjoy Running!",
            "addinfo": "):<",
            "interests": {
                "Losing Weight": True,
                "Cardiovascular Fitness": True,
            },
            "schedule": schedule_from_dayhours((0, 11), (1, 12), (2, 13)),
            "open": True,
            "gender": db.Gender.FEMALE,
            "okmale": False,
            "okfemale": True,
            "okbinary": True,
            "settings": {},
            "blocked": [],
        },
        "tlannister": {
            "netid": "tlannister",
            "name": "Tyrion Lannister",
            "contact": "3333333333",
            "level": db.Level.BEGINNER,
            "levelpreference": db.LevelPreference.ALL,
            "bio": "I enjoy Boxing!",
            "addinfo": "):<",
            "interests": {
                "Upper Body": True,
                "Lower Body": True,
            },
            "schedule": schedule_from_dayhours((0, 6), (1, 7), (2, 8)),
            "open": True,
            "gender": db.Gender.MALE,
            "okmale": True,
            "okfemale": True,
            "okbinary": True,
            "settings": {},
            "blocked": [],
        },
        "tgreyjoy": {
            "netid": "tgreyjoy",
            "name": "Theon Greyjoy",
            "contact": "3333333333",
            "level": db.Level.INTERMEDIATE,
            "levelpreference": db.LevelPreference.ALL,
            "bio": "I enjoy Swimming!",
            "addinfo": "):<",
            "interests": {
                "Gaining Mass": True,
                "Losing Weight": True,
            },
            "schedule": schedule_from_dayhours((1, 6), (2, 7), (3, 8)),
            "open": True,
            "gender": db.Gender.MALE,
            "okmale": True,
            "okfemale": False,
            "okbinary": True,
            "settings": {},
            "blocked": [],
        },
        "astark": {
            "netid": "astark",
            "name": "Arya Stark",
            "contact": "3333333333",
            "level": db.Level.ADVANCED,
            "levelpreference": db.LevelPreference.ALL,
            "bio": "I enjoy Fencing!",
            "addinfo": "):<",
            "interests": {
                "Cardiovascular Fitness": True,
                "Upper Body": True,
            },
            "schedule": schedule_from_dayhours((2, 6), (3, 7), (4, 9)),
            "open": True,
            "gender": db.Gender.FEMALE,
            "okmale": True,
            "okfemale": False,
            "okbinary": True,
            "settings": {},
            "blocked": [],
        },
        "mtyrell": {
            "netid": "mtyrell",
            "name": "Margaery Tyrell",
            "contact": "3333333333",
            "level": db.Level.BEGINNER,
            "levelpreference": db.LevelPreference.ALL,
            "bio": "I enjoy playing Pool!",
            "addinfo": "):<",
            "interests": {
                "Losing Weight": True,
                "Lower Body": True,
            },
            "schedule": schedule_from_dayhours((3, 6), (4, 7), (5, 9)),
            "open": True,
            "gender": db.Gender.FEMALE,
            "okmale": False,
            "okfemale": True,
            "okbinary": True,
            "settings": {},
            "blocked": [],
        },
        "jbaratheon": {
            "netid": "jbaratheon",
            "name": "Joffrey Baratheon",
            "contact": "3333333333",
            "level": db.Level.ADVANCED,
            "levelpreference": db.LevelPreference.ALL,
            "bio": "I enjoy Surfing!",
            "addinfo": "):<",
            "interests": {
                "Gaining Mass": True,
                "Upper Body": True,
            },
            "schedule": schedule_from_dayhours((4, 12), (5, 13), (6, 14)),
            "open": True,
            "gender": db.Gender.MALE,
            "okmale": True,
            "okfemale": False,
            "okbinary": False,
            "settings": {},
            "blocked": [],
        },
        "rstark": {
            "netid": "rstark",
            "name": "Rob Stark",
            "contact": "3333333333",
            "level": db.Level.INTERMEDIATE,
            "levelpreference": db.LevelPreference.ALL,
            "bio": "I enjoy Archery!",
            "addinfo": "):<",
            "interests": {
                "Cardiovascular Fitness": True,
                "Gaining Mass": True,
            },
            "schedule": schedule_from_dayhours((3, 6), (4, 7), (5, 9)),
            "open": True,
            "gender": db.Gender.MALE,
            "okmale": True,
            "okfemale": True,
            "okbinary": True,
            "settings": {},
            "blocked": [],
        },
        "pbaelish": {
            "netid": "pbaelish",
            "name": "Petyr Baelish",
            "contact": "3333333333",
            "level": db.Level.BEGINNER,
            "levelpreference": db.LevelPreference.ALL,
            "bio": "I enjoy Fishing!",
            "addinfo": "):<",
            "interests": {
                "Upper Body": True,
                "Lower Body": True,
            },
            "schedule": schedule_from_dayhours((4, 14), (5, 15), (6, 16)),
            "open": True,
            "gender": db.Gender.MALE,
            "okmale": True,
            "okfemale": True,
            "okbinary": True,
            "settings": {},
            "blocked": [],
        },
        "sstark": {
            "netid": "sstark",
            "name": "Sansa Stark",
            "contact": "3333333333",
            "level": db.Level.BEGINNER,
            "levelpreference": db.LevelPreference.ALL,
            "bio": "I enjoy Weightlifting!",
            "addinfo": "):<",
            "interests": {
                "Losing Weight": True,
                "Lower Body": True,
            },
            "schedule": schedule_from_dayhours((6, 14), (0, 15), (1, 16)),
            "open": True,
            "gender": db.Gender.FEMALE,
            "okmale": False,
            "okfemale": True,
            "okbinary": True,
            "settings": {},
            "blocked": [],
        },
        "clannister": {
            "netid": "clannister",
            "name": "Cercei Lannister",
            "contact": "3333333333",
            "level": db.Level.INTERMEDIATE,
            "levelpreference": db.LevelPreference.ALL,
            "bio": "I enjoy Rock Climbing!",
            "addinfo": "):<",
            "interests": {
                "Cardiovascular Fitness": True,
                "Lower Body": True,
            },
            "schedule": schedule_from_dayhours((4, 6), (5, 7), (6, 8)),
            "open": True,
            "gender": db.Gender.FEMALE,
            "okmale": True,
            "okfemale": True,
            "okbinary": True,
            "settings": {},
            "blocked": [],
        },
        "ltyrell": {
            "netid": "ltyrell",
            "name": "Loras Tyrell",
            "contact": "3333333333",
            "level": db.Level.INTERMEDIATE,
            "levelpreference": db.LevelPreference.ALL,
            "bio": "I enjoy Figure Skating!",
            "addinfo": "):<",
            "interests": {
                "Cardiovascular Fitness": True,
                "Upper Body": True,
            },
            "schedule": schedule_from_dayhours((4, 6), (5, 7), (6, 8)),
            "open": True,
            "gender": db.Gender.MALE,
            "okmale": True,
            "okfemale": False,
            "okbinary": True,
            "settings": {},
            "blocked": [],
        },
        "sbaratheon": {
            "netid": "sbaratheon",
            "name": "Stannis Baratheon",
            "contact": "3333333333",
            "level": db.Level.ADVANCED,
            "levelpreference": db.LevelPreference.ALL,
            "bio": "I enjoy Scuba Diving!",
            "addinfo": "):<",
            "interests": {
                "Upper Body": True,
                "Lower Body": True,
            },
            "schedule": schedule_from_dayhours((5, 6), (6, 7), (0, 8)),
            "open": True,
            "gender": db.Gender.MALE,
            "okmale": True,
            "okfemale": False,
            "okbinary": False,
            "settings": {},
            "blocked": [],
        },
    }
    for datum in data.values():
        a = sorted(datum.keys())
        b = sorted(db.User.__table__.columns.keys())
        b.remove("lastupdated")
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
        # {
        #     "srcnetid": "andywang",
        #     "destnetid": "jasono",
        #     "schedule": schedule_from_dayhours((1, 7)),
        # },
        # {
        #     "srcnetid": "ejcho",
        #     "destnetid": "andywang",
        #     "schedule": schedule_from_dayhours((1, 8)),
        # },
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
