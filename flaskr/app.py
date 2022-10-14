"""app.py: Flask application"""
from flask import Flask
from flask import render_template

app = Flask(__name__)


@app.route("/")
def index():
    """Hello world test"""
    return render_template("index.html")


@app.route("/post/<int:post_id>")
def var_test(post_id):
    """Index page"""
    return f"Post {post_id}"
