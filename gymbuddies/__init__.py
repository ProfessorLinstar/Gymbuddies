"""Gymbuddies Flask web application."""

from flask import Flask
from . import home, master, auth, matching
from . import database



def create_app():
    """Creates the Gymbuddies Flask application."""

    # TODO: make SECRET_KEY
    # SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY")

    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="dev"  # Should be changed to environment variable provided by render in
        # deployment
    )

    app.register_blueprint(home.bp)
    app.register_blueprint(master.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(matching.bp)

    app.jinja_env.globals.update(database=database)

    return app
