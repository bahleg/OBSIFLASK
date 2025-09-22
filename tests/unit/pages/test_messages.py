import pytest

import obsiflask.pages.messages as messages_module
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig
from obsiflask.main import run


@pytest.fixture
def flask_app(tmp_path):
    config = AppConfig(vaults={'vault1': VaultConfig(str(tmp_path))})
    app = run(config, True)
    app.config['WTF_CSRF_ENABLED'] = False
    AppState.messages[('vault1', None)] = []
    return app


"""
@pytest.fixture(autouse=True)
def mock_appstate(monkeypatch, tmp_path):

    class DummyConfig:
        vaults = {"vault1": type("Cfg", (), {"home_file": "home.md"})()}

    monkeypatch.setattr(messages_module.AppState, "config", DummyConfig)
    monkeypatch.setitem(messages_module.AppState.indices, "vault1",
                        {"dummy": "tree"})
    yield
"""


def test_render_messages_raw(flask_app, monkeypatch):
    monkeypatch.setattr(messages_module, "get_messages",
                        lambda v, unread, user: [{
                            "msg": "hello"
                        }])

    with flask_app.test_request_context():
        resp = messages_module.render_messages("vault1", unread=True, raw=True)
        data = resp.get_json()
        assert data == [{"msg": "hello"}]


def test_render_messages_html(monkeypatch):
    monkeypatch.setattr(messages_module, "get_messages",
                        lambda v, unread, user: [{
                            "msg": "ok"
                        }])
    monkeypatch.setattr(messages_module, "render_tree",
                        lambda *a, **k: "<ul></ul>")
    monkeypatch.setattr(
        messages_module, "render_template",
        lambda tpl, **ctx: f"TEMPLATE:{tpl}|msgs={ctx['messages']}")

    html = messages_module.render_messages("vault1", unread=False, raw=False)
    assert "TEMPLATE:messages.html" in html
    assert "{'msg': 'ok'}" in html
