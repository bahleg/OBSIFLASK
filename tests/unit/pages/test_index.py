import pytest

from obsiflask.pages.index import render_index
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig
from obsiflask.main import run


@pytest.fixture
def flask_app(tmp_path):
    config = AppConfig(vaults={
        'vault1': VaultConfig(str(tmp_path)),
        'vault2': VaultConfig(str(tmp_path))
    })
    app = run(config, True)
    app.config['WTF_CSRF_ENABLED'] = False
    return app


def test_render_index(monkeypatch, flask_app):

    monkeypatch.setattr(
        "obsiflask.pages.index.render_template", lambda tpl, **ctx:
        f"TEMPLATE:{tpl}|vaults={list(ctx['vaults'].keys())}")

    result = render_index()
    assert "TEMPLATE:index.html" in result
    assert "vault1" in result
    assert "vault2" in result
