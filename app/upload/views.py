from flask import render_template

from app import app

@app.route("/", methods=["GET"])
def home():
    return "hello world"