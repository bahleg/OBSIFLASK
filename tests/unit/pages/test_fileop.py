import pytest
import shutil

from obsiflask.pages.fileop import FileOpForm, create_file_op, delete_file_op, copy_move_file
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig
from obsiflask.main import run


def _make_app(tmp_path):
    config = AppConfig(vaults={'vault1': VaultConfig(str(tmp_path))})
    app = run(config, True)
    app.config['WTF_CSRF_ENABLED'] = False
    AppState.messages[('vault1', None)] = []
    return app


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
