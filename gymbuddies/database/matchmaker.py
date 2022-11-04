"""
Core matchmaking algorithm. Provided a userid, the algorithm will find the top candidates
who have the greatest similarities for weighted user interests and schedule availability.
"""
from typing import List, Dict
from . import user as db_user
from . import schedule as db_schedule
from . import db
from . import request

# TODO: IMPORTANT! NUMBER_INTERESTS SHOULD NOT BE HARDCODED. CHANGE THIS ASAP!!!
NUMBER_INTERESTS: int = 10 # TODO: find a way for this value not to be hardcoded
NUMBER_SCHEDULE_BLOCKS: int = 2016 # number of timeblocks contained in a user's schedule
RANDOM_NUMBER: int = 10 # number of users queried in random selection
RETURN_NUMBER: int = 3 # number of users returned by find_matches
LEVEL_WEIGHT: float = 0.5 # weight of level to compatability score
INTERESTS_WEIGHT: float = 1 / NUMBER_INTERESTS # weight of interests to compatability score
SCHEDULE_WEIGHT: float = 1 # weight of schedule intersection to compatability score

def find_matches(netid: str) -> List[str]:
    """run algorithm to find top matches for user <netid>"""
    # get a random sample of users to select from
    randusers = db_user.get_rand_users(RANDOM_NUMBER, netid)
    assert randusers != None
    matches: List[str] = []
    # if there are not enough users in the database, return whoever is available
    if len(randusers) <= RETURN_NUMBER:
        for user in randusers:
            matches.append(user.netid)
        return matches

    # do a hard filter on users that you are already matched with
    completed_matches = request.get_matches(netid)
    assert completed_matches is not None
    for completed_match in completed_matches:
        src_user = completed_match.srcnetid
        dest_user = completed_match.destnetid
        if src_user in randusers:
            randusers.remove(src_user)
        elif dest_user in randusers:
            randusers.remove(dest_user)

    # do a hard filter on users that are not compatible with gender preferences
    main_gender = db_user.get_gender(netid)
    main_okmale = db_user.get_okmale(netid)
    main_okfemale = db_user.get_okfemale(netid)
    main_oknonbinary = db_user.get_okbinary(netid)
    for user in randusers:
        gender = db_user.get_gender(user.netid)
        okmale = db_user.get_okmale(user.netid)
        okfemale = db_user.get_okfemale(user.netid)
        oknonbinary = db_user.get_okbinary(user.netid)
        # check if user is compatible with mainuser's preferences
        if gender == db.Gender.MALE:
            if not main_okmale:
                randusers.remove(user)
                continue
        elif gender == db.Gender.FEMALE:
            if not main_okfemale:
                randusers.remove(user)
                continue
        elif gender == db.Gender.NONBINARY:
            if not main_oknonbinary:
                randusers.remove(user)
                continue;
        # check is mainuser is compatible with user's preferences
        if main_gender == db.Gender.MALE:
            if not okmale:
                randusers.remove(user)
                continue
        elif main_gender == db.Gender.FEMALE:
            if not okfemale:
                randusers.remove(user)
                continue
        elif main_gender == db.Gender.NONBINARY:
            if not oknonbinary:
                randusers.remove(user)
                continue


    # record user compatability scores based on user levels and level preferences
    user_compatabilities: Dict[str, float] = {}
    main_user_level = db_user.get_level(netid)
    assert main_user_level is not None
    main_user_level_preference = db_user.get_levelpreference(netid)
    for user in randusers:
        user_level = db_user.get_level(user.netid)
        assert user_level is not None

        # record whether user is compatable with the level preference of the main user
        user_compatabilities[user.netid] = 0
        if main_user_level_preference == db.LevelPreference.ALL:
            user_compatabilities[user.netid] += 1
        elif main_user_level_preference == db.LevelPreference.EQUAL:
            if main_user_level == user_level:
                user_compatabilities[user.netid] += 1
        elif main_user_level_preference == db.LevelPreference.LESSEQUAL:
            if main_user_level >= user_level:
                user_compatabilities[user.netid] += 1
        elif main_user_level_preference == db.LevelPreference.GREATEREQUAL:
            if main_user_level <= user_level:
                user_compatabilities[user.netid] += 1

        # record whether the main user is compatable with the level preference of user
        user_level_preference = db_user.get_levelpreference(netid)
        if user_level_preference == db.LevelPreference.ALL:
            user_compatabilities[user.netid] += 1
        if user_level_preference == db.LevelPreference.EQUAL:
            if user_level == main_user_level:
                user_compatabilities[user.netid] += 1
        elif user_level_preference == db.LevelPreference.LESSEQUAL:
            if user_level >= main_user_level:
                user_compatabilities[user.netid] += 1
        elif user_level_preference == db.LevelPreference.GREATEREQUAL:
            if user_level <= main_user_level:
                user_compatabilities[user.netid] += 1

        # adjust user compatability score with weight
        user_compatabilities[user.netid] *= LEVEL_WEIGHT


    # update user compatability scores based on user interests
    main_user_interests = db_user.get_interests(netid)
    assert main_user_interests is not None
    interests_score: float = 0
    for user in randusers:
        user_interests = db_user.get_interests(user.netid)
        assert user_interests is not None
        for interest in user_interests:
            if interest in main_user_interests:
                if user_interests[interest] == main_user_interests[interest]:
                    interests_score += 1
        user_compatabilities[user.netid] += interests_score * INTERESTS_WEIGHT


    # update user compatability scores based on schedule intersection
    main_user_schedule: List[int] | None = db_schedule.get_schedule(netid)
    assert main_user_schedule is not None
    schedule_score: float = 0
    for user in randusers:
        user_schedule: List[int] | None = db_schedule.get_schedule(user.netid)
        assert user_schedule is not None
        for i in range(len(user_schedule)):
            if main_user_schedule[i] & db.ScheduleStatus.AVAILABLE == 1\
            and user_schedule[i] & db.ScheduleStatus.AVAILABLE == 1:
                schedule_score += 1
            user_compatabilities[user.netid] += (
                schedule_score / NUMBER_SCHEDULE_BLOCKS) * SCHEDULE_WEIGHT


    # return users with the highest compatabilties to the main user
    compatabilities = sorted(user_compatabilities.items(), key = lambda x: x[1], reverse = True)
    for i in range(RETURN_NUMBER):
        matches.append(compatabilities[i][0])
    return matches
