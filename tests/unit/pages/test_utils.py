from pathlib import Path

import pytest

from obsiflask.config import AppConfig, VaultConfig
from obsiflask.app_state import AppState
from obsiflask.main import run
from obsiflask.pages.utils import resolve_redirect_page, resolve_path, check_vault


@pytest.fixture
def app(tmp_path):
    config = AppConfig(vaults={'vault1': VaultConfig(str(tmp_path))}, )
    app = run(config, True, True)
    return app


def test_check_vault(app):
    assert check_vault('vault2')[0] == "Bad vault", 400
    assert check_vault('vault1') is None


def test_resolve_path(app):
    test_file = Path(AppState.config.vaults['vault1'].full_path) / "test"
    (test_file).write_text('test')
    assert resolve_path('vault2', 'test') == ("Bad vault", 400)
    assert resolve_path('vault1', 'test2')[1] == 400
    assert resolve_path('vault1', '../test2')[1] == 400
    assert resolve_path('vault1', 'test') == test_file


def test_resolve_redirect_page(app):
    (Path(AppState.config.vaults['vault1'].full_path) /
     "test").write_text('test')
    (Path(AppState.config.vaults['vault1'].full_path) /
     "test.md").write_text('test')
    assert resolve_redirect_page('test', 'vault1') == 'renderer'
    assert resolve_redirect_page('test.md', 'vault1') == 'editor'
    assert resolve_redirect_page('', 'vault1') == 'renderer'
    assert resolve_redirect_page('asd', 'vault1') is None
