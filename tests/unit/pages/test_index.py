from obsiflask.pages.index import render_index
from obsiflask.app_state import AppState


def test_render_index(monkeypatch):

    class DummyConfig:
        vaults = {"vault1": {}, "vault2": {}}

    monkeypatch.setattr(AppState, "config", DummyConfig)

    monkeypatch.setattr(
        "obsiflask.pages.index.render_template", lambda tpl, **ctx:
        f"TEMPLATE:{tpl}|vaults={list(ctx['vaults'].keys())}")

    result = render_index()
    assert "TEMPLATE:index.html" in result
    assert "vault1" in result
    assert "vault2" in result
