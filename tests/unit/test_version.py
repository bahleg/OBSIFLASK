import importlib.util as util

from obsiflask.version import get_version, bump_version

import pytest
from unittest.mock import patch
from obsiflask.version import get_version, version_str


def fake_check_output_git_commit(*args, **kwargs):
    if args[0] == ["git", "rev-parse", "--short", "HEAD"]:
        return "abc123"
    if args[0] == ["git", "status", "--porcelain"]:
        return ""
    return ""


def fake_check_output_git_dirty(*args, **kwargs):
    if args[0] == ["git", "rev-parse", "--short", "HEAD"]:
        return "abc123"
    if args[0] == ["git", "status", "--porcelain"]:
        return " M some_file.py"
    return ""


def fake_check_output_git_fail(*args, **kwargs):
    raise Exception("git not found")


def test_version_short():
    ver = get_version(True, True)
    ver2 = get_version(False, True)
    assert ver == ver2
    parts = ver.split('.')
    assert len(parts) == 3
    for p in parts:
        int(p)


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
