import secrets
from datetime import datetime, timezone
from pathlib import Path

from flask import json, request, render_template, url_for, make_response, send_from_directory, abort
from werkzeug.utils import secure_filename

from app import app
from app.auth.views import check_upload_password

def upload_directory():
    return Path(app.config["UPLOAD_DIRECTORY"]).resolve()


@app.after_request
def secure_uploaded_downloads(response):
    filename = (request.view_args or {}).get("filename", "")
    if request.endpoint == "download_file" or (request.endpoint == "static" and filename.startswith("uploads/")):
        disposition = response.headers.get("Content-Disposition", "")
        _, separator, parameters = disposition.partition(";")
        response.headers["Content-Disposition"] = "attachment" + (separator + parameters if separator else "")
        response.headers["Content-Type"] = "application/octet-stream"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "sandbox; default-src 'none'"
    return response


@app.get("/static/uploads/<path:filename>")
def download_file(filename):
    root = upload_directory()
    if not (root / filename).resolve().is_relative_to(root):
        abort(404)
    return send_from_directory(root, filename, as_attachment=True, mimetype="application/octet-stream")


@app.route("/upload/check-password", methods=["POST"])
def check_password():
    if not check_upload_password(request.form.get("password") or ""):
        return {"error": "wrong password"}, 401, {"Cache-Control": "no-store"}
    return {"ok": True}, 200, {"Cache-Control": "no-store"}


@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    files = None
    error = None
    status = 200
    if request.method == "POST":
        if not check_upload_password(request.form.get("password") or ""):
            error = "Incorrect password."
            status = 401
        else:
            files = []
            root = upload_directory()
            if root.exists():
                for path in root.rglob("*"):
                    if not path.is_file() or not path.resolve().is_relative_to(root):
                        continue
                    stat = path.stat()
                    files.append({
                        "name": path.name,
                        "path": path.relative_to(root).as_posix(),
                        "url": url_for("download_file", filename=path.relative_to(root).as_posix()),
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                        "date": datetime.fromtimestamp(stat.st_mtime, timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                    })
            files.sort(key=lambda file: (-file["modified"], file["path"]))
    response = make_response(render_template("admin.html", files=files, error=error), status)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response


@app.route("/admin/file", methods=["DELETE"])
def delete_file():
    if not check_upload_password(request.form.get("password") or ""):
        return {"error": "Incorrect password."}, 401, {"Cache-Control": "no-store"}

    relative = Path(request.form.get("path") or "")
    root = upload_directory()
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        return {"error": "Invalid file path."}, 400
    target = root / relative
    if not target.resolve().is_relative_to(root) or target.is_symlink():
        return {"error": "Invalid file path."}, 400
    # Reject symlinked parent directories as well as symlinked files.
    if any(parent.is_symlink() for parent in target.parents if parent != root and root in parent.parents):
        return {"error": "Invalid file path."}, 400
    if not target.is_file():
        return {"error": "File no longer exists."}, 404
    try:
        target.unlink()
    except OSError:
        return {"error": "Could not delete the file. Please try again."}, 500
    # Remove the now-empty upload folder, keeping shared folders intact.
    if target.parent != root:
        try:
            target.parent.rmdir()
        except OSError:
            pass
    return {"deleted": relative.as_posix()}, 200, {"Cache-Control": "no-store"}


@app.route("/upload/newfile", methods=["PUT"])
def new_file():
    if not check_upload_password(request.form.get("password") or ""):
        return json.dumps({"error": "wrong password"}), 401

    file = request.files.get("file")
    if not file:
        return json.dumps({"error": "no file provided"}), 400

    filename = secure_filename(file.filename)
    if not filename:
        return json.dumps({"error": "invalid filename"}), 400

    folder_name = secrets.token_hex(16)
    upload_root = upload_directory()
    dest_dir = upload_root / folder_name
    dest_dir.mkdir(parents=True)

    destination = (dest_dir / filename).resolve()
    if not destination.is_relative_to(upload_root):
        return json.dumps({"error": "invalid filename"}), 400
    file.save(destination)

    url = url_for("download_file", filename=f"{folder_name}/{filename}", _external=True)

    return json.dumps({"url": url}), 200, {"Content-Type": "application/json"}
