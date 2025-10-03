import pytest
from flask import Flask

from obsiflask.pages.file import get_file
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig


@pytest.fixture
def app():
    raise NotImplementedError()
    AppState.config = AppConfig({'vault': VaultConfig('/tmp')})
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
