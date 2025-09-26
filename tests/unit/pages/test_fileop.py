from flask import Flask
import pytest

from obsiflask.pages.fileop import FileOpForm, create_file_op, delete_file_op, copy_move_file, render_fastop
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig
from obsiflask.main import run

### FASTOP


@pytest.fixture
def fastop_app(monkeypatch):
    """
    Fixture only for renderfastop
    """
    app = Flask(__name__)
    app.testing = True

    monkeypatch.setattr(
        'obsiflask.pages.fileop.FileOpForm', lambda **kwargs: type(
            "F", (), {
                "target": type("T", (), {"data": kwargs.get("target")}),
                "destination": type("D",
                                    (), {"data": kwargs.get("destination")})
            }))
    monkeypatch.setattr('obsiflask.pages.fileop.create_file_op',
                        lambda vault, form: True)
    monkeypatch.setattr('obsiflask.pages.fileop.copy_move_file',
                        lambda vault, form, is_copy: True)
    monkeypatch.setattr('obsiflask.pages.fileop.delete_file_op',
                        lambda vault, form, flag: True)
    monkeypatch.setattr('obsiflask.pages.fileop.add_message',
                        lambda *a, **k: None)

    @app.route("/fastop")
    def fastop_route():
        return render_fastop("vault1")

    @app.route("/editor/vault/subpath")
    def editor(vault, subpath):
        return ''

    @app.route("/folder/vault/subpath")
    def get_folder(vault, subpath):
        return ''

    return app


@pytest.fixture
def client(fastop_app):
    return fastop_app.test_client()


def test_missing_curfile_and_curdir(client):
    resp = client.get("/fastop?op=copy")
    assert resp.status_code == 400


def test_invalid_operation(client):
    resp = client.get("/fastop?curfile=a.txt&op=invalid")
    assert resp.status_code == 400


def test_copy_success(client):
    resp = client.get("/fastop?curfile=a.txt&op=copy&dst=b.txt")
    assert resp.status_code == 302
    assert "/editor" in resp.location


def test_move_success(client):
    resp = client.get("/fastop?curfile=a.txt&op=move&dst=b.txt")
    assert resp.status_code == 302
    assert "/editor" in resp.location


def test_delete_success(client):
    resp = client.get("/fastop?curfile=a.txt&op=delete")
    assert resp.status_code == 200
    assert resp.data == b"ok"


def test_file_creation_success(client):
    resp = client.get("/fastop?curfile=dir&op=file&dst=new.txt")
    assert resp.status_code == 302
    assert "/editor" in resp.location


def test_folder_creation_success(client):
    resp = client.get("/fastop?curfile=dir&op=folder&dst=subdir")
    assert resp.status_code == 302
    assert "/folder" in resp.location


def test_template_success(client):
    resp = client.get(
        "/fastop?curfile=dir&op=template&dst=note.md&template=tpl.md")
    assert resp.status_code == 302
    assert "/editor" in resp.location


def _make_app(tmp_path):
    config = AppConfig(vaults={'vault1': VaultConfig(str(tmp_path))})
    app = run(config, True)
    app.config['WTF_CSRF_ENABLED'] = False
    AppState.messages[('vault1', None)] = []
    return app


### INTERNAL FUNCTIONS


def test_create_empty_file(tmp_path):
    app = _make_app(tmp_path)
    with app.app_context():
        form = FileOpForm('vault1',
                          data={
                              "target": "test.md",
                              "template": "0_no"
                          })
        assert create_file_op('vault1', form)
        assert (tmp_path / "test.md").exists()
        assert AppState.hints['vault1'].default_files_per_user[None][
            0] == "test.md"


def test_create_folder(tmp_path):
    app = _make_app(tmp_path)
    with app.app_context():
        form = FileOpForm('vault1',
                          data={
                              "target": "folder",
                              "template": "1_dir"
                          })
        assert create_file_op('vault1', form)
        assert (tmp_path / "folder").is_dir()


def test_delete_file(tmp_path):
    app = _make_app(tmp_path)
    with app.app_context():
        f = tmp_path / "delete.md"
        f.write_text("hi")
        form = FileOpForm('vault1', data={"target": "delete.md"})
        delete_file_op('vault1', form)
        assert not f.exists()


def test_copy_move_file_copy(tmp_path):
    app = _make_app(tmp_path)
    with app.app_context():
        f = tmp_path / "a.txt"
        f.write_text("data")
        form = FileOpForm('vault1',
                          data={
                              "target": "a.txt",
                              "destination": "b.txt"
                          })
        assert copy_move_file('vault1', form, copy=True)
        assert (tmp_path / "b.txt").exists()
        assert AppState.hints['vault1'].default_files_per_user[None][
            0] == "b.txt"


def test_copy_move_file_move(tmp_path):
    app = _make_app(tmp_path)
    with app.app_context():
        f = tmp_path / "c.txt"
        f.write_text("data")
        form = FileOpForm('vault1',
                          data={
                              "target": "c.txt",
                              "destination": "d.txt"
                          })
        assert copy_move_file('vault1', form, copy=False)
        assert not f.exists()
        assert (tmp_path / "d.txt").exists()
        assert AppState.hints['vault1'].default_files_per_user[None][
            0] == "d.txt"
