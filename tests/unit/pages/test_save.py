import pytest
from unittest.mock import patch

from obsiflask.pages.save import make_save
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig
from obsiflask.main import run


@pytest.fixture
def app(tmp_path):
    config = AppConfig(vaults={'vault1': VaultConfig(str(tmp_path))})
    app = run(config, True)
    AppState.messages[('vault1', None)] = []
    return app


def test_make_save_existing_file(tmp_path, app):
    file_path = tmp_path / "file.txt"
    file_path.write_text("old content")
    AppState.hints['vault1'].populate_default_files(None, []) # cleaning for test
    with app.app_context():
        resp, code = make_save(str(file_path), "new content",
                               AppState.indices['vault1'], "vault1")
    assert AppState.hints['vault1'].default_files_per_user[None][0] == str(file_path.relative_to(tmp_path))
    assert code == 200
    assert file_path.read_text() == "new content"


def test_make_save_new_file_triggers_refresh(tmp_path, app):
    file_path = tmp_path / "newfile.txt"
    AppState.hints['vault1'].populate_default_files(None, []) # cleaning for test
    with app.app_context():
        resp, code = make_save(str(file_path), "hello world", AppState.indices['vault1'], "vault1")
    assert AppState.hints['vault1'].default_files_per_user[None][0] == str(file_path.relative_to(tmp_path))
    assert code == 200
    assert file_path.read_text() == "hello world"


def test_make_save_failure(app):
    # path with incorrect chars
    bad_path = "/invalid_path/<>/file.txt"

    with patch("builtins.open", side_effect=OSError("mock error")):
        with app.app_context():
            resp, code = make_save(bad_path, "data", AppState.indices['vault1'], "vault1")

    assert code == 400
    assert "Cannot save" in resp
