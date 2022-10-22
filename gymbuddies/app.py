"""app.py: Flask application"""
from flask import Flask
from flask import render_template
# from flask import g
from .master import bp as master_bp
from .auth import bp as auth_bp

app = Flask(__name__)


@app.route("/")
def index():
    """Hello world test"""
    return render_template("index.html")


@app.route("/post/<int:post_id>")
def var_test(post_id):
    """Index page"""
    return f"Post {post_id}"

app.register_blueprint(master_bp)
app.register_blueprint(auth_bp)
