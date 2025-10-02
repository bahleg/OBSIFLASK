from flask import Flask
import pytest

from obsiflask.pages.fileop import render_fastop

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


