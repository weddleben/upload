from io import BytesIO

from app import app


# matches the master password set by the autouse fixture in conftest.py
PASSWORD = "test-password"

def test_home_returns_200(client):
    resp = client.get("/")
    assert resp.status_code == 200

def test_upload_newfile_returns_url_and_saves_file(client, upload_base):
    data = {"file": (BytesIO(b"hello"), "test.txt"), "password": PASSWORD}
    resp = client.put("/upload/newfile", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200

    import json
    body = json.loads(resp.data)
    assert "url" in body
    assert body["url"].endswith("/test.txt")

    saved_path = next(upload_base.iterdir()) / "test.txt"
    assert saved_path.exists()
    assert saved_path.read_bytes() == b"hello"

def test_upload_newfile_no_file_returns_400(client):
    resp = client.put("/upload/newfile", data={"password": PASSWORD}, content_type="multipart/form-data")
    assert resp.status_code == 400

def test_upload_over_max_content_length_returns_413(client):
    with app.app_context():
        original = app.config["MAX_CONTENT_LENGTH"]
        app.config["MAX_CONTENT_LENGTH"] = 1
    try:
        data = {"file": (BytesIO(b"ab"), "small.txt"), "password": PASSWORD}
        resp = client.put("/upload/newfile", data=data, content_type="multipart/form-data")
    finally:
        with app.app_context():
            app.config["MAX_CONTENT_LENGTH"] = original
    assert resp.status_code == 413


def test_absolute_filename_stays_in_upload_directory(client, upload_base, tmp_path):
    outside = tmp_path / 'outside.txt'
    resp = client.put('/upload/newfile', data={
        'password': PASSWORD,
        'file': (BytesIO(b'safe'), str(outside)),
    })
    assert resp.status_code == 200
    assert not outside.exists()
    saved = list(upload_base.rglob('*'))
    files = [path for path in saved if path.is_file()]
    assert len(files) == 1
    assert files[0].resolve().is_relative_to(upload_base.resolve())
    assert files[0].read_bytes() == b'safe'


def test_traversal_filename_cannot_overwrite_existing_file(client, upload_base):
    upload_base.mkdir(parents=True)
    existing = upload_base / 'existing.txt'
    existing.write_bytes(b'original')
    resp = client.put('/upload/newfile', data={
        'password': PASSWORD,
        'file': (BytesIO(b'replacement'), '../existing.txt'),
    })
    assert resp.status_code == 200
    assert existing.read_bytes() == b'original'


def test_special_filename_returns_working_download_url(client):
    from urllib.parse import urlsplit

    resp = client.put('/upload/newfile', data={
        'password': PASSWORD,
        'file': (BytesIO(b'contents'), 'a #b?.txt'),
    })
    assert resp.status_code == 200
    url = urlsplit(resp.json['url'])
    assert not url.fragment
    assert not url.query
    download = client.get(url.path)
    assert download.status_code == 200
    assert download.data == b'contents'


def test_unusable_filename_returns_400_without_creating_files(client, upload_base):
    resp = client.put('/upload/newfile', data={
        'password': PASSWORD,
        'file': (BytesIO(b'contents'), '../..'),
    })
    assert resp.status_code == 400
    assert not upload_base.exists()


def test_uploaded_active_content_is_downloaded_as_attachment(client):
    from urllib.parse import urlsplit

    for filename in ('page.html', 'image.svg', 'script.js'):
        response = client.put('/upload/newfile', data={
            'password': PASSWORD,
            'file': (BytesIO(b'<script>alert(1)</script>'), filename),
        })
        url = urlsplit(response.json['url']).path
        for download in (client.get(url), client.head(url)):
            assert download.status_code == 200
            assert download.headers['Content-Disposition'].startswith('attachment;')
            assert download.headers['Content-Type'] == 'application/octet-stream'
            assert download.headers['X-Content-Type-Options'] == 'nosniff'
            assert "sandbox" in download.headers['Content-Security-Policy']


def test_password_precheck_does_not_authorize_later_uploads(client, upload_base):
    response = client.post('/upload/check-password', data={'password': PASSWORD})
    assert response.status_code == 200
    assert response.json == {'ok': True}
    assert response.headers['Cache-Control'] == 'no-store'
    assert 'Set-Cookie' not in response.headers
    assert not upload_base.exists()
    for password in (None, 'wrong'):
        data = {'file': (BytesIO(b'no'), 'file.txt')}
        if password is not None:
            data['password'] = password
        assert client.put('/upload/newfile', data=data).status_code == 401
    assert not upload_base.exists()


def test_external_directory_is_used_for_upload_admin_and_delete(client, upload_base):
    from pathlib import Path
    from urllib.parse import urlsplit

    assert not upload_base.is_relative_to(Path(app.static_folder))
    response = client.put('/upload/newfile', data={
        'password': PASSWORD, 'file': (BytesIO(b'external'), 'external.txt'),
    })
    path = urlsplit(response.json['url']).path
    assert path.startswith('/static/uploads/')
    relative = path.removeprefix('/static/uploads/')
    assert (upload_base / relative).read_bytes() == b'external'
    assert client.get(path).data == b'external'
    listing = client.post('/admin', data={'password': PASSWORD})
    assert path.encode() in listing.data
    assert client.delete('/admin/file', data={'password': PASSWORD, 'path': relative}).status_code == 200
    assert client.get(path).status_code == 404


def test_download_rejects_traversal_and_external_symlinks(client, upload_base, tmp_path):
    upload_base.mkdir()
    outside = tmp_path / 'outside.txt'
    outside.write_bytes(b'not public')
    (upload_base / 'link.txt').symlink_to(outside)
    for path in ('../outside.txt', '%2e%2e/outside.txt', 'link.txt', 'missing.txt'):
        response = client.get('/static/uploads/' + path)
        assert response.status_code == 404
        assert b'not public' not in response.data
