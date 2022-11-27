"""Gymbuddies Flask web application."""
import os
from flask import Flask
from . import home, master, auth, matching, error
from . import database
from .database import db


def create_app():
    """Creates the Gymbuddies Flask application."""

    app = Flask(__name__)
    app.config.from_mapping(SECRET_KEY=os.getenv("FLASK_SECRET_KEY", "dev"))

    app.register_blueprint(home.bp)
    app.register_blueprint(master.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(matching.bp)
    app.register_blueprint(error.bp)

    app.jinja_env.globals.update(database=database, db=db)

    print("Started a flask application!")

    return app
