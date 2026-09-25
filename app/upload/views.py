import os
import secrets
from pathlib import Path

from flask import json, request, render_template

from app import app

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "static" / "uploads"

@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")

@app.route("/upload/newfile", methods=["PUT"])
def new_file():
    file = request.files.get("file")
    if not file:
        return json.dumps({"error": "no file provided"}), 400

    random_suffix = secrets.token_hex(6)
    folder_name = f"{file.filename}-{random_suffix}"
    dest_dir = UPLOAD_DIR / folder_name
    dest_dir.mkdir(parents=True)

    file.save(dest_dir / file.filename)

    url = request.host_url.rstrip("/") + f"/static/uploads/{folder_name}/{file.filename}"

    return json.dumps({"url": url}), 200, {"Content-Type": "application/json"}