import pytest

from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig
import obsiflask.pages.folder as folder_module
from obsiflask.main import run


@pytest.fixture
def app(tmp_path):
    # Создаём временный "vault"
    root = tmp_path 
    (root / "file1.txt").write_text("hello")
    (root / "subdir").mkdir()
    (root / "subdir" / "file2.txt").write_text("world")

    config = AppConfig(vaults={'vault1': VaultConfig(str(tmp_path))})
    app = run(config, True)
    app.config['WTF_CSRF_ENABLED'] = False
    AppState.messages[('vault1', None)] = []
    return app


def test_render_folder_ok(monkeypatch, app):
    monkeypatch.setattr(folder_module, "render_tree", lambda *a, **kw: "TREE")
    monkeypatch.setattr(folder_module, "render_template",
                        lambda *a, **kw: {"rendered": kw})
    monkeypatch.setattr(folder_module, "url_for",
                        lambda endpoint, **kw: f"/fake/{endpoint}")

    with app.app_context():
        result = folder_module.render_folder("vault1", "subdir")
        assert isinstance(result, dict)
        rendered = result["rendered"]   

        assert rendered["vault"] == "vault1"
        assert ("subdir/file2.txt", "file2.txt") in rendered["files"]
        assert ("subdir", "subdir") not in rendered["files"]
        assert rendered["folders"] == []



def test_render_folder_abort(monkeypatch, app):
    monkeypatch.setattr(folder_module, "render_tree", lambda *a, **kw: "TREE")
    monkeypatch.setattr(folder_module, "render_template", lambda *a, **kw: "HTML")
    monkeypatch.setattr(folder_module, "url_for", lambda endpoint, **kw: f"/fake/{endpoint}")

    # out of the vault
    with pytest.raises(Exception) as excinfo:
        folder_module.render_folder("vault1", "../outside")
    assert "400" in str(excinfo.value)


def test_render_folder_parent_url_root(monkeypatch, app):
    monkeypatch.setattr(folder_module, "render_tree", lambda *a, **kw: "TREE")
    monkeypatch.setattr(folder_module, "render_template", lambda *a, **kw: {"parent_url": kw["parent_url"]})
    monkeypatch.setattr(folder_module, "url_for", lambda endpoint, **kw: f"/fake/{endpoint}")

    result = folder_module.render_folder("vault1", "")
    assert result["parent_url"] == "/fake/get_folder_root"


def test_render_folder_parent_url_subdir(monkeypatch, app):
    monkeypatch.setattr(folder_module, "render_tree", lambda *a, **kw: "TREE")
    monkeypatch.setattr(folder_module, "render_template", lambda *a, **kw: {"parent_url": kw["parent_url"]})
    monkeypatch.setattr(folder_module, "url_for", lambda endpoint, **kw: f"/fake/{endpoint}")

    result = folder_module.render_folder("vault1", "subdir")
    assert "/fake/get_folder" in result["parent_url"]
