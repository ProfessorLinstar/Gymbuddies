"""Login page blueprint."""
from flask import Blueprint, render_template

bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.route("/login")
def login():
    """Shows login page."""
    return render_template("login.html")
