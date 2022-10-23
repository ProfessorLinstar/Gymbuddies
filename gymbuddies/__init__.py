"""Gymbuddies Flask web application."""

from flask import Flask
from flask import render_template

from . import master
from . import auth


def create_app():
    """Creates the Gymbuddies Flask application."""

    app = Flask(__name__)

    @app.route("/")
    def index():
        """Hello world test"""
        return render_template("index.html")

    app.register_blueprint(master.bp)
    app.register_blueprint(auth.bp)

    return app
