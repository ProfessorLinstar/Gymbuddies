"""
Core matchmaking algorithm. Provided a userid, the algorithm will find the top candidates
who have the greatest similarities for weighted user interests and schedule availability.
"""
from typing import List, Dict
from . import user as usermod
from . import schedule as schedulemod
from . import db
from . import request

# IMPORTANT! NUMBER_INTERESTS SHOULD NOT BE HARDCODED. CHANGE THIS ASAP!!!
NUMBER_INTERESTS: int = 10 # find a way for this value not to be hardcoded
RANDOM_NUMBER: int = 25 # number of users queried in random selection
RETURN_NUMBER: int = 10 # number of users returned by find_matches
LEVEL_WEIGHT: float = 0.5 # weight of level to compatability score
INTERESTS_WEIGHT: float = 1 / NUMBER_INTERESTS # weight of interests to compatability score
SCHEDULE_WEIGHT: float = 1 # weight of schedule intersection to compatability score
BLOCKS_IN_AN_HOUR: int = 12 # number of blocks in an hour. Used for total intersection checking

def find_matches(netid: str) -> List[str]:
    """run algorithm to find top matches for user <netid>"""
    # get the main user using their netid
    main_user = usermod.get_user(netid)
    assert main_user is not None

    # get a random sample of users to select from
    randusers = usermod.get_rand_users(RANDOM_NUMBER, netid)
    assert randusers is not None

    # do a hard filter on users that you are already matched with
    completed_matches = request.get_matches(netid)
    rand_netids = [user.netid for user in randusers]
    banned_netids = []
    assert completed_matches is not None
    for completed_match in completed_matches:
        src_user = completed_match.srcnetid
        dest_user = completed_match.destnetid
        if src_user in rand_netids:
            banned_netids.append(src_user)
        if dest_user in rand_netids:
            banned_netids.append(dest_user)

    # do a hard filter on users that you already sent a request to
    outgoing_requests = request.get_active_outgoing(netid)
    assert outgoing_requests is not None
    for outgoing_request in outgoing_requests:
        dest_user = outgoing_request.destnetid
        if dest_user in rand_netids:
            banned_netids.append(dest_user)

    # do a hard filter on users that you have incoming requests for
    incoming_requests = request.get_active_incoming(netid)
    assert incoming_requests is not None
    for incoming_request in incoming_requests:
        src_user = incoming_request.srcnetid
        if src_user in rand_netids:
            banned_netids.append(src_user)

    # do a hard filter on users that you have blocked
    blocked_users = usermod.get_blocked(netid)
    assert blocked_users is not None
    for blocked_user in blocked_users:
        if blocked_user in rand_netids:
            banned_netids.append(blocked_user)

    temprandusers = randusers.copy()
    for user in temprandusers:
        # do a hard filter on users that are not open
        if user.netid in banned_netids:
            randusers.remove(user)
            continue

        if not user.open:
            randusers.remove(user)
            continue
        # hard filter if user is not compatible with mainuser's preferences
        if user.gender == db.Gender.MALE:
            if not main_user.okmale:
                randusers.remove(user)
                continue
        elif user.gender == db.Gender.FEMALE:
            if not main_user.okfemale:
                randusers.remove(user)
                continue
        elif user.gender == db.Gender.NONBINARY:
            if not main_user.okbinary:
                randusers.remove(user)
                continue
        # hard filter if mainuser is not compatible with user's preferences
        if main_user.gender == db.Gender.MALE:
            if not user.okmale:
                randusers.remove(user)
                continue
        elif main_user.gender == db.Gender.FEMALE:
            if not user.okfemale:
                randusers.remove(user)
                continue
        elif main_user.gender == db.Gender.NONBINARY:
            if not user.okbinary:
                randusers.remove(user)
                continue

    # if there are not enough users left after the hard filters, return whoever is available
    # if len(randusers) <= RETURN_NUMBER:
    #    matches: List[str] = []
    #    for user in randusers:
    #         matches.append(user.netid)
    #   return matches

    # record user compatability scores based on user levels and level preferences
    user_compatabilities: Dict[str, float] = {}
    main_user_level = main_user.level
    assert main_user_level is not None
    main_user_level_preference = main_user.levelpreference
    assert main_user_level_preference is not None
    main_user_interests = main_user.interests
    assert main_user_interests is not None
    interests_score: float = 0

    for user in randusers:
        user_level = user.level
        assert user_level is not None

        user_compatabilities[user.netid] = 0
        # record whether user is compatable with the level preference of the main user
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
        user_level_preference = user.levelpreference
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
        user_interests = user.interests
        assert user_interests is not None
        for interest in user_interests:
            if interest in main_user_interests:
                if user_interests[interest] == main_user_interests[interest]:
                    interests_score += 1
        user_compatabilities[user.netid] += interests_score * INTERESTS_WEIGHT


    # update user compatability scores based on schedule intersection
    main_user_schedule: List[int] | None = schedulemod.get_schedule(netid)
    assert main_user_schedule is not None
    for user in randusers:
        schedule_score: int = 0
        user_schedule: List[int] | None = schedulemod.get_schedule(user.netid)
        assert user_schedule is not None
        i = 0
        while i + (BLOCKS_IN_AN_HOUR - 1) < len(user_schedule):
            flag = True
            for j in range(i, i + BLOCKS_IN_AN_HOUR):
                if not ((main_user_schedule[j] == db.ScheduleStatus.AVAILABLE) and (user_schedule[j] == db.ScheduleStatus.AVAILABLE)):
                    flag = False
            if flag:
                schedule_score += BLOCKS_IN_AN_HOUR
            i += BLOCKS_IN_AN_HOUR
        # do a hard filter where there are no schedule interactions
        # do a hard filter on users that have blocked you
        if schedule_score == 0 or (netid in user.blocked):
            del user_compatabilities[user.netid]
        else:
            # continue with matchmaking ranking algorithm
            user_compatabilities[user.netid] += (schedule_score / db.NUM_WEEK_BLOCKS) * SCHEDULE_WEIGHT


    # return users with the highest compatabilties to the main user
    compatabilities = sorted(user_compatabilities.items(), key = lambda x: x[1], reverse = True)
    matches: List[str] = []
    # if there are not enough users remaining, return everyone you can
    if len(compatabilities) <= RETURN_NUMBER:
        for i in range(len(compatabilities)):
            matches.append(compatabilities[i][0])
        return matches

    for i in range(RETURN_NUMBER):
        matches.append(compatabilities[i][0])
    return matches
