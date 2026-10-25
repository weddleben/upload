from io import BytesIO

from app import app


def test_admin_requires_password_without_exposing_files(client, upload_base):
    upload_base.mkdir(parents=True)
    (upload_base / 'private-list-name.txt').write_bytes(b'hello')
    for response in (
        client.get('/admin'),
        client.post('/admin', data={}),
        client.post('/admin', data={'password': 'wrong'}),
        client.post('/admin', data={'password': 'é'}),
    ):
        assert b'private-list-name.txt' not in response.data
        assert b'type="password"' in response.data
        assert response.headers['Cache-Control'] == 'no-store'
    assert client.post('/admin', data={'password': 'wrong'}).status_code == 401


def test_admin_lists_uploads_with_working_links(client):
    upload = client.put('/upload/newfile', data={
        'password': 'test-password', 'file': (BytesIO(b'hello'), 'example.txt'),
    })
    response = client.post('/admin', data={'password': 'test-password'})
    assert response.status_code == 200
    assert b'example.txt' in response.data
    assert b'5 Bytes' in response.data
    assert b'UTC' in response.data
    from urllib.parse import urlsplit
    path = urlsplit(upload.json['url']).path
    assert path.encode() in response.data
    assert client.get(path).data == b'hello'
    assert b'example.txt' not in client.get('/admin').data
    assert b'test-password' not in response.data
    assert 'Set-Cookie' not in response.headers


def test_admin_empty_list(client):
    response = client.post('/admin', data={'password': 'test-password'})
    assert response.status_code == 200
    assert b'No files uploaded yet.' in response.data


def test_admin_fails_closed_when_unconfigured(client, monkeypatch):
    monkeypatch.setitem(app.config, 'UPLOAD_MASTER_PASSWORD', '')
    assert client.get('/admin').status_code == 500
    assert client.post('/admin', data={'password': 'test-password'}).status_code == 500


def test_admin_escapes_filenames_and_ignores_external_symlinks(client, upload_base, tmp_path):
    upload_base.mkdir(parents=True)
    (upload_base / '<script>alert(1)</script>'.replace('/', '')).write_bytes(b'x')
    outside = tmp_path / 'outside-secret.txt'
    outside.write_bytes(b'secret')
    (upload_base / 'outside-secret.txt').symlink_to(outside)
    response = client.post('/admin', data={'password': 'test-password'})
    assert b'<script>' not in response.data
    assert b'&lt;script&gt;' in response.data
    assert b'outside-secret.txt' not in response.data


def test_delete_requires_password(client, upload_base):
    upload_base.mkdir(parents=True)
    target = upload_base / 'keep.txt'
    target.write_bytes(b'keep')
    for password in ('', 'wrong', 'é'):
        response = client.delete('/admin/file', data={'path': 'keep.txt', 'password': password})
        assert response.status_code == 401
        assert target.read_bytes() == b'keep'
    assert client.get('/admin/file').status_code == 405


def test_delete_removes_only_selected_file_and_download(client, upload_base):
    folder = upload_base / 'folder'
    folder.mkdir(parents=True)
    target = folder / 'delete.txt'
    target.write_bytes(b'delete')
    keep = folder / 'keep.txt'
    keep.write_bytes(b'keep')
    response = client.delete('/admin/file', data={'path': 'folder/delete.txt', 'password': 'test-password'})
    assert response.status_code == 200
    assert not target.exists()
    assert keep.read_bytes() == b'keep'
    assert client.get('/static/uploads/folder/delete.txt').status_code == 404
    assert client.delete('/admin/file', data={'path': 'folder/keep.txt', 'password': 'test-password'}).status_code == 200
    assert not folder.exists()
    assert upload_base.exists()


def test_delete_rejects_unsafe_paths_and_missing_files(client, upload_base, tmp_path):
    upload_base.mkdir(parents=True)
    outside = tmp_path / 'outside.txt'
    outside.write_bytes(b'keep')
    (upload_base / 'link.txt').symlink_to(outside)
    for path in ('../outside.txt', str(outside), 'link.txt', '', '.'):
        response = client.delete('/admin/file', data={'path': path, 'password': 'test-password'})
        assert response.status_code == 400
        assert outside.read_bytes() == b'keep'
    assert client.delete('/admin/file', data={'path': 'missing.txt', 'password': 'test-password'}).status_code == 404


def test_delete_fails_closed(client, monkeypatch):
    monkeypatch.setitem(app.config, 'UPLOAD_MASTER_PASSWORD', '')
    assert client.delete('/admin/file', data={'path': 'file.txt', 'password': 'test-password'}).status_code == 500
