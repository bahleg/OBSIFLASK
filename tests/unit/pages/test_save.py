import pytest
from unittest.mock import MagicMock, patch

from obsiflask.pages.save import make_save
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig
from obsiflask.main import run


@pytest.fixture
def app():
    config = AppConfig(vaults={'vault1': VaultConfig('/tmp')})
    app = run(config, True)
    AppState.messages[('vault1', None)] = []
    return app


@pytest.fixture
def fake_index():
    return MagicMock()


def test_make_save_existing_file(tmp_path, fake_index, app):
    file_path = tmp_path / "file.txt"
    file_path.write_text("old content")

    with app.app_context():
        resp, code = make_save(str(file_path), "new content", fake_index,
                               "vault1")

    assert code == 200
    assert file_path.read_text() == "new content"


def test_make_save_new_file_triggers_refresh(tmp_path, fake_index, app):
    file_path = tmp_path / "newfile.txt"

    with app.app_context():
        resp, code = make_save(str(file_path), "hello world", fake_index,
                               "vault1")

    assert code == 200
    assert file_path.read_text() == "hello world"


def test_make_save_failure(fake_index, app):
    # path with incorrect chars
    bad_path = "/invalid_path/<>/file.txt"

    with app.app_context():
        resp, code = make_save(bad_path, "data", fake_index, "vault1")

    assert code == 400
    assert "Cannot save" in resp
