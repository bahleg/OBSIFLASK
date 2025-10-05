import pytest
from flask import Flask

from obsiflask.pages.file import get_file
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig
from obsiflask.encrypt.obfuscate import obf_open


@pytest.fixture
def app(tmp_path):
    AppState.config = AppConfig({'vault': VaultConfig(str(tmp_path))})
    return Flask(__name__)


def test_get_file_returns_file(tmp_path, app):

    file_path = tmp_path / "hello.txt"
    content = "hello world"
    file_path.write_text(content)

    with app.test_request_context():
        response = get_file(str(file_path), 'vault')

    assert response.status_code == 200
    content_disposition = response.headers.get("Content-Disposition")
    assert "attachment" in content_disposition
    assert "hello.txt" in content_disposition
    data = b"".join(response.response)
    assert data.decode() == content


def test_get_file_nonexistent_file(app):
    fake_path = "/nonexistent/path.txt"

    with app.test_request_context():
        with pytest.raises(FileNotFoundError):
            get_file(fake_path, 'vault')


def test_get_file_obfuscate(app, tmp_path):
    with obf_open(tmp_path / 'test.obf.md', 'vault', 'w') as out:
        out.write('test')
    with app.test_request_context():
        response = get_file(tmp_path / str('test.obf.md'), 'vault')

        data = b"".join(response.response)
        assert data != b'test'

    with app.test_request_context('?deobfuscate=1'):
        response = get_file(str(tmp_path / 'test.obf.md'), 'vault')

        data = b"".join(response.response)
        assert data == b'test'
