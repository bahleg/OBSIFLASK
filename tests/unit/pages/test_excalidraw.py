from unittest.mock import patch, mock_open
import json
import re

from lzstring import LZString
import pytest
from werkzeug.exceptions import BadRequest

from obsiflask.pages.excalidraw import render_excalidraw, default_excalidraw, handle_open, prepare_content_to_write
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

    with flask_app.test_request_context():
        with patch("builtins.open", mock_open(read_data=fake_content)), \
            patch("obsiflask.pages.excalidraw.render_template") as mock_render:
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

    with flask_app.test_request_context():
        with patch("builtins.open", mock_open(read_data='')), \
            patch("obsiflask.pages.excalidraw.render_template") as mock_render:

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
    with flask_app.test_request_context():
        with patch("builtins.open", side_effect=IOError("cannot read")), \
            patch("obsiflask.pages.editor.url_for", return_value="/renderer"):
            with pytest.raises(BadRequest):
                render_excalidraw(vault, path, real_path)


def test_handle_open(flask_app, tmp_path):
    # bad json
    (tmp_path / "test.excalidraw").write_text('bad json')
    assert handle_open('vault1', tmp_path / "test.excalidraw",
                       False) == default_excalidraw
    # empty
    (tmp_path / "empty.excalidraw").touch()
    assert handle_open('vault1', tmp_path / "empty.excalidraw",
                       False) == default_excalidraw
    # some json from excalidraw
    (tmp_path / "test.excalidraw").write_text(json.dumps({'some': 'json'}))
    assert json.loads(
        handle_open('vault1', tmp_path / "test.excalidraw", False)) == {
            'some': 'json'
        }
    # json from plugin
    (tmp_path / "test.excalidraw.md").write_text("""
Hello world
```json
{"some": "json"}
``` some text""")
    assert json.loads(
        handle_open('vault1', tmp_path / "test.excalidraw.md", True)) == {
            'some': 'json'
        }
    # compressed-json from plugin
    (tmp_path / "test.excalidraw.md").write_text("""
Hello world
```compressed-json
N4Igzg9gtgpiBcACEArSA7EBfIA=
``` some text""")
    assert json.loads(
        handle_open('vault1', tmp_path / "test.excalidraw.md", True)) == {
            'some': 'json'
        }


def test_prepare_content_to_write(flask_app, tmp_path):
    # we don't check text if it goes to .excalidraw
    assert prepare_content_to_write('vault1', 'test.excalidraw',
                                    'any text') == 'any text'
    (tmp_path / "empty.excalidraw.md").touch()
    # saving to plugin format. By default uncompressed
    result = prepare_content_to_write('vault1',
                                      tmp_path / "empty.excalidraw.md",
                                      json.dumps({'some': 'json'}))
    result = re.search('```json(.*?)```', result, re.MULTILINE | re.DOTALL)
    result = json.loads(result.group(1))
    assert result['some'] == 'json'
    assert 'appState' in result
    # the same, but for already saved file
    (tmp_path / "uncompressed.excalidraw.md"
     ).write_text("""Hello world\n```json\n{"hello": "world"}\n```Some text""")
    result = prepare_content_to_write('vault1',
                                      tmp_path / "uncompressed.excalidraw.md",
                                      json.dumps({'some': 'json'}))
    assert "Hello world" in result
    assert "Some text" in result
    result = re.search('```json(.*?)```', result, re.MULTILINE | re.DOTALL)
    result = json.loads(result.group(1))
    assert result['some'] == 'json'
    assert 'appState' in result
    # the same, but for compressed file
    (tmp_path / "compressed.excalidraw.md").write_text(
        """Hello world\n```compressed-json\nbinarystring\n```Some text""")
    result = prepare_content_to_write('vault1',
                                      tmp_path / "compressed.excalidraw.md",
                                      json.dumps({'some': 'json'}))
    assert "Hello world" in result
    assert "Some text" in result
    result = re.search('```compressed-json(.*?)```', result,
                       re.MULTILINE | re.DOTALL)
    result = json.loads(LZString().decompressFromBase64(
        result.group(1).strip()))
    assert result['some'] == 'json'
    assert 'appState' in result
