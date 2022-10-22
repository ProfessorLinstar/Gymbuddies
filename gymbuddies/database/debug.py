"""Database debug and diagnostics functions."""

import json

from typing import Optional, List, Any
from sqlalchemy.orm import Session
import db

@db.session_decorator
def list_users(*criterions, session: Session) -> Optional[bool]:
    """Prints out all users in json dump format."""

    users: List[Any] = session.query(db.User).filter(*criterions).all()

    for user in users:
        printv(user)

def printv(x: Any) -> None:
    """Prints the attributes of 'x' in json format."""
    print(json.dumps({k: v for k,v in vars(x).items() if "_" not in k}, sort_keys=True, indent=4))
