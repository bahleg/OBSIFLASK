from obsiflask.fileop import FileOpForm, create_file_op, delete_file_op, copy_move_file, copy_move_file_op
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig
from obsiflask.main import run
from obsiflask.encrypt.obfuscate import obf_open


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


def test_copy_move_file_op(tmp_path):
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()
    out_dir.mkdir()
    app = _make_app(tmp_path)

    for in_type in [
            'obf',
            'obf-bin',
            'no-obf',
    ]:
        for out_type in ['obf', 'no-obf', 'obf-bin']:
            for copy in [True, False]:
                if in_type == 'obf':
                    method = 'w'
                    suffix = '.obf.md'
                    content = 'test'
                elif in_type == 'obf-bin':
                    method = 'wb'
                    suffix = '.obf.bin'
                    content = b'test'
                else:
                    method = 'w'
                    suffix = '.md'
                    content = 'test'

                with obf_open(in_dir / f"out{suffix}", 'vault1',
                              method) as out:
                    out.write(content)
                with open(in_dir / f"out{suffix}", 'rb') as inp:
                    readed_match = inp.read() == b'test'
                    assert readed_match == (in_type == 'no-obf')

                if out_type == 'obf':
                    out_suffix = '.obf.md'
                elif out_type == 'obf-bin':
                    out_suffix = '.obf.bin'
                else:
                    out_suffix = '.md'

                copy_move_file_op(in_dir / f"out{suffix}",
                                  out_dir / f"out{out_suffix}", 'vault1', copy)
                assert (in_dir / f"out{suffix}").exists() == copy
                with open(out_dir / f"out{out_suffix}", 'rb') as inp:
                    content = inp.read()
                    readed_match = content == b'test'
                    assert readed_match == (out_type == 'no-obf')
                if (in_dir / f"out{suffix}").exists():
                    (in_dir / f"out{suffix}").unlink()
                (out_dir / f"out{out_suffix}").unlink()
