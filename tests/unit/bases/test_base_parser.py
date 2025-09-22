import pytest

from obsiflask.bases.base_parser import parse_filter, parse_view, parse_base, Base
from obsiflask.bases.filter import FieldFilter, TrivialFilter, FilterAnd, FilterOr
from obsiflask.bases.view import View
from obsiflask.bases.file_info import FileInfo
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig
from obsiflask.main import run


@pytest.fixture
def dummy_file(tmp_path):

    config = AppConfig(vaults={'vault1': VaultConfig(str(tmp_path))})
    config.vaults['vault1'].base_config.error_on_field_parse = False
    config.vaults['vault1'].base_config.error_on_yaml_parse = False

    AppState.messages[('vault1', None)] = []
    run(config, True)

    f = tmp_path / "test.md"
    f.write_text("# Title\nSome content")
    return f


# -------------------------
# Tests parse_filter
# -------------------------
def test_parse_filter_string(dummy_file):
    f = parse_filter("field == 1", 'vault1')
    assert isinstance(f, FieldFilter)
    assert callable(f.check)


def test_parse_filter_and_or(dummy_file):
    f_and = parse_filter({"and": ["field == 1", "field == 2"]}, 'vault1')
    assert isinstance(f_and, FilterAnd)
    f_or = parse_filter({"or": ["field == 1", "field == 2"]}, 'vault1')
    assert isinstance(f_or, FilterOr)


def test_parse_filter_trivial_for_unknown_key(dummy_file):
    f = parse_filter({"unknown": []}, 'vault1')
    assert isinstance(f, TrivialFilter)


# -------------------------
# Tests parse_view
# -------------------------
def test_parse_view_basic(dummy_file):
    formulas = []
    properties = {}
    view_dict = {
        "type": "table",
        "name": "myview",
        "order": ["field1"],
        "sort": [{
            "property": "field1",
            "direction": "ASC"
        }],
    }
    view = parse_view(view_dict, 'vault1', formulas, properties,
                      str(dummy_file.parent))
    assert isinstance(view, View)
    assert view.name == "myview"
    assert view.type == "table"
    assert isinstance(view.filter, TrivialFilter)
    assert view.order == ["field1"]
    assert view.sorts == [("field1", "ASC")]


def test_parse_view_invalid_type_changes_to_table(dummy_file):
    view_dict = {"type": "unknown", "name": "v", "order": []}
    view = parse_view(view_dict, 'vault1', [], {}, str(dummy_file.parent))
    assert view.type == "table"


# -------------------------
# Tests parse_base
# -------------------------
def test_parse_base_simple(tmp_path):
    from omegaconf import OmegaConf

    yaml_file = tmp_path / "base.yaml"
    yaml_file.write_text("""
filters: "field == 1"
properties:
  f1: {}
formulas:
  f1: "field == 2"
views:
  - type: table
    name: myview
    order: ["f1"]
""")
    base = parse_base(str(yaml_file), 'vault1')
    assert isinstance(base, Base)
    assert isinstance(base.global_filter, FieldFilter)
    assert "f1" in base.formulas
    assert "myview" in base.views
    assert isinstance(base.views["myview"], View)


def test_parse_base_no_filters(tmp_path):
    from omegaconf import OmegaConf

    yaml_file = tmp_path / "base.yaml"
    yaml_file.write_text("""
properties:
  f1: {}
formulas:
  f1: "field == 2"
views:
  - type: table
    name: myview
    order: ["f1"]
""")
    base = parse_base(str(yaml_file), 'vault1')
    assert isinstance(base.global_filter, TrivialFilter)


def test_parse_base_bad_formula(tmp_path, dummy_file):
    yaml_file = tmp_path / "base.yaml"
    yaml_file.write_text("""
properties:
  f1: {}
formulas:
  f1: "!!! invalid formula !!!"
views: []
""")
    base = parse_base(str(yaml_file), 'vault1')
    # should create a dummy function instead of raising
    result = base.formulas["f1"](FileInfo(tmp_path / "test.md", "vault1"))
    assert result == ""
