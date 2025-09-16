import pytest

import obsiflask.pages.index_tree as index_tree
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig
from obsiflask.main import run


@pytest.fixture(autouse=True)
def mock_appstate(tmp_path):
    (tmp_path / "folder").mkdir()
    (tmp_path / "folder" / "file.txt").touch()
    (tmp_path / "folder" / "file.md").touch()

    config = AppConfig(vaults={'vault1': VaultConfig(str(tmp_path))})
    app = run(config, True)
    app.config['WTF_CSRF_ENABLED'] = False
    AppState.messages[('vault1', None)] = []
    return app


@pytest.fixture(autouse=True)
def mock_url_for(monkeypatch):

    def fake_url_for(endpoint, **kwargs):
        return f"/{endpoint}/{kwargs.get('subpath', '')}".rstrip("/")

    monkeypatch.setattr(index_tree, "url_for", fake_url_for)


def test_render_tree_with_fileindex():
    html = index_tree.render_tree(index_tree.AppState.indices["vault1"],
                                  "vault1")
    assert "📁 folder" in html
    assert "📄 file.txt" in html
    assert "📄 file.md" in html
    assert "/renderer/folder/file.md" in html
    assert "/get_folder" in html


def test_render_tree_edit_mode():
    html = index_tree.render_tree(index_tree.AppState.indices["vault1"],
                                  "vault1",
                                  edit=True)
    assert "/editor/folder/file.md" in html
