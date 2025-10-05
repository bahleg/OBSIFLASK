from flask import Flask
import pytest
from unittest.mock import MagicMock

from obsiflask.app_state import AppState
from obsiflask.main import run
from obsiflask.config import AppConfig, VaultConfig
from obsiflask.pages.fileop import render_fastop, upload_files, FileOpForm
from obsiflask.encrypt.obfuscate import obf_open

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


# UPLOAD
@pytest.fixture
def app(tmp_path):
    root = tmp_path
    (root / "subdir").mkdir()

    config = AppConfig(vaults={'vault1': VaultConfig(str(tmp_path))})
    app = run(config, True)
    app.config['WTF_CSRF_ENABLED'] = False
    AppState.messages[('vault1', None)] = []
    return app


def test_upload(tmp_path, app):

    class FileMock:

        def __init__(self, fname, content):
            self.filename = fname
            self.content = content

        def save(self, dst):
            with open(dst, 'wb') as out:
                out.write(self.content)

        def read(self):
            return self.content

    with app.test_request_context():
        # simple loading
        form = FileOpForm('vault1')
        form.operation.data = 'upload'
        form.target.data = 'subdir'
        form.files.data = [
            FileMock('fname1.md', b'test1'),
            FileMock('fname2.md', b'test2')
        ]

        assert upload_files('vault1', form=form)
        with open(tmp_path / 'subdir' / 'fname1.md') as inp:
            assert inp.read() == 'test1'
        with open(tmp_path / 'subdir' / 'fname2.md') as inp:
            assert inp.read() == 'test2'

        # obfuscation loading
        form.obfuscate.data = True
        form.files.data[1].filename = 'fname2.bin'
        assert upload_files('vault1', form=form)
        with obf_open(tmp_path / 'subdir' / 'fname1.obf.md', 'vault1') as inp:
            assert inp.read() == 'test1'
        with obf_open(tmp_path / 'subdir' / 'fname2.obf.bin',
                      'vault1',
                      method='rb') as inp:
            assert inp.read() == b'test2'
        # test with obfuscation files skipping
        form.files.data = [FileMock('fname.obf.md', b'test1')]
        assert not upload_files('vault1', form=form)
        assert not (tmp_path / 'subdir' / 'fname.obf.md').exists()
