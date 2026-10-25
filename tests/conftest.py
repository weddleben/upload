import pytest

from app import app


@pytest.fixture(autouse=True)
def master_password():
    """every test runs with a known master password configured."""
    original = app.config.get("UPLOAD_MASTER_PASSWORD")
    app.config["UPLOAD_MASTER_PASSWORD"] = "test-password"
    yield
    app.config["UPLOAD_MASTER_PASSWORD"] = original


@pytest.fixture(autouse=True)
def upload_base(tmp_path, monkeypatch):
    """Exercise storage outside the static folder without touching real uploads."""
    upload_dir = tmp_path / "file-storage"
    monkeypatch.setitem(app.config, "UPLOAD_DIRECTORY", str(upload_dir))
    return upload_dir


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setitem(app.config, "TESTING", True)
    with app.test_client() as c:
        yield c
