import pytest
import json
import re

from obsiflask.pages.bookmarks import load_links, change_and_save_links, render_links
from obsiflask.config import AppConfig, VaultConfig
from obsiflask.main import run
from obsiflask.app_state import AppState


@pytest.fixture
def app(tmp_path):
    config = AppConfig(vaults={
        'vault':
        VaultConfig(str(tmp_path),
                    template_dir=(tmp_path / "templates"),
                    short_alias='v')
    }, )

    app = run(config, True)
    return app


def test_load_change_and_save_links_links(app):
    AppState.shortlinks = {}
    load_links()
    assert AppState.shortlinks == {'vault': {}}
    change_and_save_links('vault', 'key', 'http://127.0.0.1')
    AppState.shortlinks = {}
    load_links()
    assert AppState.shortlinks == {'vault': {'key': 'http://127.0.0.1'}}
    change_and_save_links('vault', 'key')
    assert AppState.shortlinks == {'vault': {}}
    

def test_render_links(app, monkeypatch):
    monkeypatch.setattr("obsiflask.pages.bookmarks.render_template",
                        lambda *a, **kw: {"rendered": kw})

    # checking only get
    with app.test_request_context():
        render_links('vault')

    # creating a link and delete it via GET request
    change_and_save_links('vault', 'key', 'http://127.0.0.1')
    assert AppState.shortlinks == {'vault': {'key': 'http://127.0.0.1'}}
    with app.test_request_context('?link=key'):
        render_links('vault')
    assert AppState.shortlinks == {'vault': {}}
