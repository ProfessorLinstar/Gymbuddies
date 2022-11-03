"""Tests users table API functions."""
import unittest
from gymbuddies import database
from gymbuddies.database import db
from . import generate


class TestSchedule(unittest.TestCase):
    """Tests API functions for the schedule database"""

    def test_basic(self):
        """Tests basic user functions."""
        netid = generate.unistr()

        if database.user.exists(netid):
            database.user.delete(netid)

        self.assertTrue(database.user.create(netid))
        self.assertTrue(database.user.exists(netid))
        user = database.user.get_user(netid)
        self.assertTrue(user is not None)

        for col in db.User.__table__.columns.keys():
            a = getattr(user, col)
            self.assertTrue(getattr(user, col) is not None, f"user.{col} is None!")
            if col == "netid":
                continue
            b = getattr(database.user, "get_" + col)(netid)
            self.assertTrue(a == b, f"user.{col} = {a} vs database.user.get_{col}() = {b}")

        profile = generate.profile(netid)
        for col, a in profile.items():
            if col != "netid":
                continue
            database.user.update(netid, **{col: a})
            b = getattr(database.user, "get_" + col)(netid)
            self.assertTrue(a == b, f"profile['{col}'] = {a} vs database.user.get_{col}() = {b}")

        self.assertTrue(database.user.delete(netid))
        self.assertTrue(not database.user.exists(netid))

    def test_stress(self):
        """Generates large amount of random user operations for testing."""

    def test_errors(self):
        """Tests inputs that will cause exceptions to be raised in API calls."""
        netid = generate.unistr()

        database.user.delete(netid)
        self.assertTrue(not database.user.exists(netid))

        for col in db.User.__table__.columns.keys():
            if col == "netid":
                continue
            b = getattr(database.user, "get_" + col)(netid)
    # TODO: schedule consistency
    # TODO: error checking

if __name__ == "__main__":
    unittest.main()
