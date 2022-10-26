"""
Core matchmaking algorithm. Provided a userid, the algorithm will find the top candidates
who have the greatest similarities for weighted user interests and schedule availability.
"""
from typing import List

import database.db

def find_matches(netid: str) -> List[str]:
    """run algorithm to find top matchces for user <netid>"""

    return []