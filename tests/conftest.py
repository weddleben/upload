import pytest

from app import app
from app.upload import views


@pytest.fixture(autouse=True)
def master_password():
    """every test runs with a known master password configured."""
    original = app.config.get("UPLOAD_MASTER_PASSWORD")
    app.config["UPLOAD_MASTER_PASSWORD"] = "test-password"
    yield
    app.config["UPLOAD_MASTER_PASSWORD"] = original


@pytest.fixture(autouse=True)
def upload_base(tmp_path, monkeypatch):
    """Keep both uploaded files and public downloads in temporary storage."""
    static_dir = tmp_path / "static"
    upload_dir = static_dir / "uploads"
    monkeypatch.setattr(app, "static_folder", str(static_dir))
    monkeypatch.setattr(views, "UPLOAD_DIR", upload_dir)
    return upload_dir


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setitem(app.config, "TESTING", True)
    with app.test_client() as c:
        yield c
