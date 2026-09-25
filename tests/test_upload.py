import os
import shutil
from io import BytesIO
from pathlib import Path

import pytest

from app import app

UPLOAD_BASE = Path(__file__).resolve().parent.parent / "app" / "static" / "uploads"

@pytest.fixture(autouse=True)
def cleanup_uploads():
    yield
    if UPLOAD_BASE.exists():
        shutil.rmtree(UPLOAD_BASE)

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

def test_home_returns_200(client):
    resp = client.get("/")
    assert resp.status_code == 200

def test_upload_newfile_returns_url_and_saves_file(client):
    data = {"file": (BytesIO(b"hello"), "test.txt")}
    resp = client.put("/upload/newfile", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200

    import json
    body = json.loads(resp.data)
    assert "url" in body
    assert body["url"].endswith("/test.txt")

    saved_path = Path(UPLOAD_BASE) / list(Path(UPLOAD_BASE).iterdir())[0] / "test.txt"
    assert saved_path.exists()
    assert saved_path.read_bytes() == b"hello"

def test_upload_newfile_no_file_returns_400(client):
    resp = client.put("/upload/newfile", content_type="multipart/form-data")
    assert resp.status_code == 400

def test_upload_over_max_content_length_returns_413(client):
    with app.app_context():
        original = app.config["MAX_CONTENT_LENGTH"]
        app.config["MAX_CONTENT_LENGTH"] = 1
    try:
        data = {"file": (BytesIO(b"ab"), "small.txt")}
        resp = client.put("/upload/newfile", data=data, content_type="multipart/form-data")
    finally:
        with app.app_context():
            app.config["MAX_CONTENT_LENGTH"] = original
    assert resp.status_code == 413
