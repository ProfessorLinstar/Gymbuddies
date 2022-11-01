"""Tests users table API functions."""
import unittest
from gymbuddies import database
from gymbuddies.database import db
from . import generate


class TestUser(unittest.TestCase):
    def basic(self):
        """Tests basic user functions."""
        netid: str = "lmao"

        if database.user.exists(netid):
            database.user.delete(netid)

        self.assertTrue(database.user.create(netid))
        user = database.user.get_user(netid)
        self.assertTrue(user)
        for column in db.User.__table__.columns:
            self.assertTrue(getattr(database.user, "get_" + column))
