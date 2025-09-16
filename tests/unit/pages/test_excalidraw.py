from unittest.mock import patch, mock_open

import pytest
from werkzeug.exceptions import BadRequest

from obsiflask.pages.excalidraw import render_excalidraw, default_excalidraw
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig
from obsiflask.main import run


@pytest.fixture
def flask_app(tmp_path):
    config = AppConfig(vaults={'vault1': VaultConfig(str(tmp_path))})
    app = run(config, True)
    AppState.messages[('vault1', None)] = []
    return app


def test_render_excalidraw_success(flask_app):
    vault = "vault1"
    path = "file.excalidraw"
    real_path = "/fake/path/file.excalidraw"
    fake_content = '{"type": "excalidraw"}'

    with flask_app.app_context():
        with patch("builtins.open", mock_open(read_data=fake_content)), \
            patch("obsiflask.pages.excalidraw.render_template") as mock_render, \
            patch("obsiflask.pages.excalidraw.render_tree", return_value="<ul></ul>"):

            render_excalidraw(vault, path, real_path)
            mock_render.assert_called_once()
            args, kwargs = mock_render.call_args
            assert kwargs["vault"] == vault
            assert 'excalidraw_json' in kwargs
            assert kwargs['excalidraw_json'] == fake_content


def test_render_excalidraw_empty(flask_app):
    vault = "vault1"
    path = "file.excalidraw"
    real_path = "/fake/path/file.excalidraw"

    with flask_app.app_context():
        with patch("builtins.open", mock_open(read_data='')), \
            patch("obsiflask.pages.excalidraw.render_template") as mock_render, \
            patch("obsiflask.pages.excalidraw.render_tree", return_value="<ul></ul>"):

            render_excalidraw(vault, path, real_path)
            mock_render.assert_called_once()
            args, kwargs = mock_render.call_args
            assert kwargs["vault"] == vault
            assert 'excalidraw_json' in kwargs
            assert kwargs['excalidraw_json'] == default_excalidraw


def test_render_editor_file_error(flask_app):
    vault = "vault1"
    path = "file.md"
    real_path = "/fake/path/file.md"

    # eror simmulation
    with flask_app.app_context():
        with patch("builtins.open", side_effect=IOError("cannot read")), \
            patch("obsiflask.pages.editor.url_for", return_value="/renderer"):
            with pytest.raises(BadRequest):
                render_excalidraw(vault, path, real_path)
