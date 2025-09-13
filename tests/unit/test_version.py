import importlib.util as util

from obsiflask.version import get_version, bump_version


def test_get_version(monkeypatch):
    monkeypatch.setenv("GIT_BRANCH", "main")
    monkeypatch.setenv("GIT_COMMIT", "abcdef")
    ver = get_version()
    assert ver.endswith("+abcdef")

    monkeypatch.setenv("GIT_BRANCH", "local")
    ver = get_version()
    assert ver.endswith("+local")

    monkeypatch.setenv("GIT_BRANCH", "feature/test")
    monkeypatch.setenv("GIT_COMMIT", "123456")
    ver = get_version()
    assert ver.endswith("+feature/test.123456")

    monkeypatch.setenv("GIT_BRANCH", "main")
    monkeypatch.setenv("GIT_COMMIT", "abcdef")
    ver = get_version(pep_version=False)
    assert ver.endswith("-abcdef")


def test_bump_version(tmp_path):
    path = tmp_path / "version.py"
    bump_version(path)
    module_name = 'version2'

    spec = util.spec_from_file_location(module_name, str(path))
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)

    cur_ver = get_version().split('+')[0].split('.')
    new_ver = module.get_version().split('+')[0].split('.')
    assert cur_ver[0] == new_ver[0]
    assert cur_ver[1] == new_ver[1]
    assert int(new_ver[2]) == int(cur_ver[2]) + 1
