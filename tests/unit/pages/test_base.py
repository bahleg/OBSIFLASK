import pytest
from unittest.mock import patch, MagicMock

from obsiflask.pages.base import render_base_view
from obsiflask.bases.base_parser import Base, View
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig
from obsiflask.main import run


@pytest.fixture
def app(tmp_path):
    config = AppConfig(vaults={'vault1': VaultConfig(str(tmp_path))})
    config.vaults['vault1'].base_config.error_on_field_parse = False
    config.vaults['vault1'].base_config.error_on_yaml_parse = False
    AppState.messages[('vault1', None)] = []
    return run(config, True)


@pytest.fixture
def dummy_base(tmp_path):
    base_path = tmp_path / "base.yaml"
    base_path.write_text("""
views:
  test_view:
    type: table
    name: test_view
    order: []
filters: {}
formulas: {}
properties: {}
""")
    return str(base_path)


def test_render_base_view_table(dummy_base, app):
    vault = "vault1"
    subpath = "some/path"
    with app.test_request_context('/'):
        with patch("obsiflask.pages.base.parse_base") as mock_parse_base, \
            patch("obsiflask.pages.base.render_template") as mock_render_template, \
            patch("obsiflask.pages.base.request") as mock_request:

            view = View([], {}, "base_path")
            view.type = "table"
            view.name = "test_view"
            view.make_view = MagicMock(return_value=[{"col1": 1}])
            base = Base(dummy_base)
            base.views = {"test_view": view}

            mock_parse_base.return_value = base
            # Без параметров запроса
            mock_request.args.get = MagicMock(return_value=None)
            mock_render_template.return_value = "HTML_OUTPUT"

            result = render_base_view(vault, subpath, dummy_base)
            assert result == "HTML_OUTPUT"
            mock_render_template.assert_called_once()
            view.make_view.assert_called_once_with(vault, force_refresh=False)


def test_render_base_view_bad_view(dummy_base, app):
    vault = "vault1"
    subpath = "some/path"
    with app.test_request_context('/'):
        with patch("obsiflask.pages.base.parse_base") as mock_parse_base, \
            patch("obsiflask.pages.base.request") as mock_request:

            base = Base(dummy_base)
            base.views = {"test_view": MagicMock()}
            mock_parse_base.return_value = base
            mock_request.args.get = MagicMock(
                side_effect=lambda k: "wrong_view" if k == "view" else None)

            result = render_base_view(vault, subpath, dummy_base)
            assert result[1] == 400
