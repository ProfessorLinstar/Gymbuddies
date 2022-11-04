"""Common methods for routing modules."""
from typing import Dict, Any, List
from .database import db


def fill_schedule(context: Dict[str, Any], schedule: List[int]) -> None:
    """Checks the master schedule boxes according to the provided 'schedule'."""
    for i, s in enumerate(schedule):
        day, time = db.TimeBlock(i).day_time()
        if s & db.ScheduleStatus.AVAILABLE and time % db.NUM_HOUR_BLOCKS == 0:
            context[f"s{day}_{time // db.NUM_HOUR_BLOCKS}"] = "checked"
