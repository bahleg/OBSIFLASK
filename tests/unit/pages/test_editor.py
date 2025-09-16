from unittest.mock import patch, mock_open
import pytest

from obsiflask.pages.editor import render_editor
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig
from obsiflask.main import run


@pytest.fixture
def flask_app(tmp_path):
    config = AppConfig(vaults={'vault1': VaultConfig(str(tmp_path))})
    app = run(config, True)
    AppState.messages[('vault1', None)] = []
    return app


def test_render_editor_success(flask_app):
    vault = "vault1"
    path = "file.md"
    real_path = "/fake/path/file.md"
    fake_content = "# Hello World"

    with patch("builtins.open", mock_open(read_data=fake_content)), \
         patch("obsiflask.pages.editor.preprocess", return_value="<h1>Hello World</h1>") as mock_md, \
         patch("obsiflask.pages.editor.render_template") as mock_render, \
         patch("obsiflask.pages.editor.render_tree", return_value="<ul></ul>"):

        render_editor(vault, path, real_path)
        mock_md.assert_called_once()
        mock_render.assert_called_once()
        args, kwargs = mock_render.call_args
        assert "markdown_text" in kwargs
        assert kwargs["markdown_text"] == fake_content
        assert kwargs["vault"] == vault
        assert kwargs["markdown_html"] == "<h1>Hello World</h1>"


def test_render_editor_file_error(flask_app):
    vault = "vault1"
    path = "file.md"
    real_path = "/fake/path/file.md"

    # eror simmulation
    with patch("builtins.open", side_effect=IOError("cannot read")), \
         patch("obsiflask.pages.editor.add_message") as mock_msg, \
         patch("obsiflask.pages.editor.redirect") as mock_redirect, \
         patch("obsiflask.pages.editor.url_for", return_value="/renderer"):

        result = render_editor(vault, path, real_path)
        mock_msg.assert_called_once()
        mock_redirect.assert_called_once()
        assert result == mock_redirect.return_value
