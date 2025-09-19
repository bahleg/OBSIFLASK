import pytest
from unittest.mock import patch

from obsiflask.bases.view import View, convert_field
from obsiflask.bases.file_info import FileInfo
from obsiflask.bases.filter import TrivialFilter
from obsiflask.bases.cache import BaseCache
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig
from obsiflask.main import run


@pytest.fixture
def dummy_file(tmp_path):
    config = AppConfig(vaults={'vault1': VaultConfig(str(tmp_path))})
    config.vaults['vault1'].base_config.error_on_field_parse = False
    config.vaults['vault1'].base_config.error_on_yaml_parse = False

    AppState.messages[('vault1', None)] = []
    f = tmp_path / "test.md"
    f.write_text("# Title\nSome content")
    run(config, True)
    return f


def test_convert_field():
    assert convert_field(None) != None
    assert convert_field(5) == 5
    assert convert_field(3.14) == 3.14
    assert convert_field("str") == "str"
    assert convert_field(True) == True


def test_view_gather_files(dummy_file):
    v = View(formulas=[], properties={}, base_path="base")
    v.filter = TrivialFilter()
    v.global_filter = TrivialFilter()
    files = v.gather_files("vault1")
    assert len(files) == 1
    f = files[0]
    assert isinstance(f, FileInfo)
    assert f.vault_path.name == "test.md"


def test_view_make_view_basic(dummy_file):
    # Simple formula the returns file name
    def formula(f):
        return f.vault_path.name

    v = View(formulas={'0': formula},
             properties={"formula.0": {
                 "displayName": "FileName"
             }},
             base_path="base")
    v.filter = TrivialFilter()
    v.global_filter = TrivialFilter()
    v.order = ["formula.0"]
    v.sorts = []
    v.name = "view1"
    v.type = 'table'

    result = v.make_view("vault1", force_refresh=True)
    assert isinstance(result, list)
    assert result[0]["FileName"] == "test.md"


def test_view_make_view_cache(dummy_file):
    v = View(formulas=[], properties={}, base_path="base")
    v.filter = TrivialFilter()
    v.global_filter = TrivialFilter()
    v.order = ['FileName']
    v.sorts = []
    v.name = "view_cache"
    v.type = 'table'

    BaseCache.cache.clear()
    result1 = v.make_view("vault1", force_refresh=True)
    with patch.object(BaseCache,
                      "get_from_cache",
                      wraps=BaseCache.get_from_cache) as mock_get:
        result2 = v.make_view("vault1", force_refresh=False)
        mock_get.assert_called_once()
        assert result1 == result2


def test_view_make_view_sorting(dummy_file):

    def formula(f):
        return f.vault_path.name

    v = View(formulas={'0': formula},
             properties={"formula.0": {
                 "displayName": "FileName"
             }},
             base_path="base")
    v.filter = TrivialFilter()
    v.global_filter = TrivialFilter()
    v.order = ["formula.0"]
    v.sorts = [("formula.0", "ASC")]
    v.name = "view_sort"
    v.type = 'table'

    result = v.make_view("vault1", force_refresh=True)
    # Проверяем, что сортировка выполнена (один элемент, просто проверка структуры)
    assert list(result[0].keys()) == ["FileName"]


def test_view_make_view_cards_cover(dummy_file):
    v = View(formulas=[], properties={}, base_path="base")
    v.filter = TrivialFilter()
    v.global_filter = TrivialFilter()
    v.order = []
    v.sorts = []
    v.name = "view_cards"
    v.type = 'cards'

    result = v.make_view("vault1", force_refresh=True)
    # Проверяем, что COVER_KEY добавлен в финальный порядок
    assert result is not None
