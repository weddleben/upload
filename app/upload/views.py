from flask import render_template

from app import app

@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")

@app.route("/upload/newfile", methods=["PUT"])
def new_file():
    return "success"