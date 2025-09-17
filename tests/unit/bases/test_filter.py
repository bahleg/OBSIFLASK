import pytest
from unittest.mock import MagicMock

from obsiflask.bases.filter import TrivialFilter, FilterAnd, FilterOr, FieldFilter
from obsiflask.bases.file_info import FileInfo
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig
from obsiflask.main import run


@pytest.fixture
def dummy_file(tmp_path):
    config = AppConfig(vaults={'vault1': VaultConfig(str(tmp_path))})
    AppState.messages[('vault1', None)] = []
    run(config, True)
    file_path = tmp_path / "test.md"
    file_path.write_text("Some content")
    file = FileInfo(file_path, vault="vault1")
    file.get_prop = MagicMock(return_value="value")
    file.vault = "vault1"

    return file


def test_trivial_filter_accepts_all(dummy_file):
    f = TrivialFilter()
    assert f.check(dummy_file) is True


def test_filter_and_all_true(dummy_file):
    f1 = TrivialFilter()
    f2 = TrivialFilter()
    f_and = FilterAnd([f1, f2])
    assert f_and.check(dummy_file) is True


def test_filter_and_one_false(dummy_file):
    f1 = TrivialFilter()
    f2 = MagicMock()
    f2.check.return_value = False
    f_and = FilterAnd([f1, f2])
    assert f_and.check(dummy_file) is False


def test_filter_or_one_true(dummy_file):
    f1 = MagicMock()
    f1.check.return_value = False
    f2 = TrivialFilter()
    f_or = FilterOr([f1, f2])
    assert f_or.check(dummy_file) is True


def test_filter_or_all_false(dummy_file):
    f1 = MagicMock()
    f1.check.return_value = False
    f2 = MagicMock()
    f2.check.return_value = False
    f_or = FilterOr([f1, f2])
    assert f_or.check(dummy_file) is False


def test_field_filter_simple(dummy_file):
    ff = FieldFilter('file.name == "test.md"')
    dummy_file.get_prop = MagicMock(return_value="test.md")
    assert ff.check(dummy_file) is True


def test_field_filter_method_contains(dummy_file):
    ff = FieldFilter('file.name.contains("test")')
    dummy_file.get_prop = MagicMock(return_value="my_test_file.md")
    assert ff.check(dummy_file) is True


def test_field_filter_method_startswith(dummy_file):
    ff = FieldFilter('file.name.startsWith("my_")')
    dummy_file.get_prop = MagicMock(return_value="my_test_file.md")
    assert ff.check(dummy_file) is True


def test_field_filter_error_handling(dummy_file, monkeypatch):
    ff = FieldFilter("bad")
    dummy_file.vault = "vault1"
    AppState.config.vaults["vault1"].base_config.error_on_field_parse = False
    # should not fail
    ff.check(dummy_file)


def test_field_filter_error_raises(dummy_file, monkeypatch):
    monkeypatch.setattr(
        FieldFilter, "__init__",
        lambda self, expr: setattr(self, "exception", Exception("bad")))
    ff = FieldFilter("bad")
    dummy_file.vault = "vault1"
    AppState.config.vaults["vault1"].base_config.error_on_field_parse = True
    with pytest.raises(Exception):
        ff.check(dummy_file)
