"""Database debug and diagnostics functions."""

import json

from typing import Any, Generator
from . import user


def sprint_users(*criterions) -> Generator[str, None, None]:
    """Yields a generator whose elements are strings representing a user in json format."""

    users = user.get_users(*criterions)
    if users is None:
        return

    for u in users:
        yield sprintv(u)


def print_users(*criterions) -> None:
    """Like sprint_users, but prints out each user instead."""
    for s in sprint_users(*criterions):
        print(s)


def sprintv(x: Any) -> str:
    """Prints the attributes of 'x' in json format."""
    return json.dumps({k: str(v) for k, v in vars(x).items() if "_" not in k},
                      sort_keys=True,
                      indent=4)


def printv(x: Any) -> None:
    """Like sprint_users, but prints out each user instead."""
    print(sprintv(x))
