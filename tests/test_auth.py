import json
from io import BytesIO
from urllib.parse import urlparse

import pytest

from app import app

PASSWORD = "test-password"  # set by the autouse fixture in conftest.py


def upload_file(client, password=None):
    data = {"file": (BytesIO(b"hello"), "test.txt")}
    if password is not None:
        data["password"] = password
    return client.put("/upload/newfile", data=data, content_type="multipart/form-data")


@pytest.fixture
def no_password():
    """runs a test with no password configured (misconfigured server)."""
    with app.app_context():
        original = app.config.get("UPLOAD_MASTER_PASSWORD")
        app.config["UPLOAD_MASTER_PASSWORD"] = ""
    yield
    with app.app_context():
        app.config["UPLOAD_MASTER_PASSWORD"] = original


# --- uploads: wrong or missing password is rejected ---

def test_upload_without_password_field_returns_401(client, upload_base):
    resp = upload_file(client)
    assert resp.status_code == 401
    assert not upload_base.exists()  # nothing was saved

def test_upload_with_wrong_password_returns_401(client, upload_base):
    resp = upload_file(client, password="wrong-password")
    assert resp.status_code == 401
    assert not upload_base.exists()  # nothing was saved

def test_upload_with_correct_password_returns_200(client):
    resp = upload_file(client, password=PASSWORD)
    assert resp.status_code == 200
    body = json.loads(resp.data)
    assert body["url"].endswith("/test.txt")

# --- file downloads stay public ---

def test_file_download_does_not_require_password(client):
    resp = upload_file(client, password=PASSWORD)
    body = json.loads(resp.data)
    download_path = urlparse(body["url"]).path

    assert client.get(download_path).status_code == 200
    assert client.get(download_path).data == b"hello"

# --- home page stays public ---

def test_home_page_does_not_require_password(client):
    assert client.get("/").status_code == 200

# --- no password configured: fail closed with 500 ---

def test_no_password_home_returns_500(client, no_password):
    resp = client.get("/")
    assert resp.status_code == 500
    assert b"misconfigured" in resp.data

def test_no_password_upload_returns_500(client, no_password):
    resp = upload_file(client, password=PASSWORD)
    assert resp.status_code == 500
    assert b"misconfigured" in resp.data

def test_no_password_download_returns_500(client, no_password, upload_base):
    upload_base.mkdir(parents=True, exist_ok=True)
    (upload_base / "some-folder").mkdir()
    (upload_base / "some-folder" / "test.txt").write_bytes(b"hello")

    resp = client.get("/static/uploads/some-folder/test.txt")
    assert resp.status_code == 500
    assert b"misconfigured" in resp.data


def test_unicode_wrong_password_returns_401(client):
    assert upload_file(client, password='wrong-é🔒').status_code == 401


def test_unicode_master_password_is_supported(client, monkeypatch):
    monkeypatch.setitem(app.config, 'UPLOAD_MASTER_PASSWORD', 'sécret-🔒')
    assert upload_file(client, password='sécret-🔒').status_code == 200
    assert upload_file(client, password='secret').status_code == 401


def test_password_precheck_rejects_wrong_or_missing_password(client):
    for data in ({}, {'password': 'wrong'}, {'password': 'é'}):
        assert client.post('/upload/check-password', data=data).status_code == 401


def test_password_precheck_fails_closed(client, no_password):
    assert client.post('/upload/check-password', data={'password': PASSWORD}).status_code == 500
