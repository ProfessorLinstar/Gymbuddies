"""Gymbuddies Flask web application."""

from flask import Flask
from . import home, master, auth, matching


def create_app():
    """Creates the Gymbuddies Flask application."""

    app = Flask(__name__)

    app.register_blueprint(home.bp)
    app.register_blueprint(master.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(matching.bp)

    return app
