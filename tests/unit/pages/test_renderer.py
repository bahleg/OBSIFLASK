import re
import pytest
from pathlib import Path

from flask import Flask
import obsiflask.pages.renderer as md
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig
from obsiflask.main import run


class DummyIndex:

    def __init__(self, path="/vault"):
        self.path = Path(path)
        self.vault = 'vault'

    def resolve_wikilink(self, name, file_path, create=False, **kwargs):
        # very simplified fake resolver
        if name == "Exists":
            return "resolved/exists.md"
        if name == "Exists#header":
            return "resolved/exists.md#header"
        if name == "Image":
            return "image.png"
        if name == "Remote":
            return "http://example.com"
        if name == "doc.base":
            return "resolved/doc.base"
        if name == "Image.png":
            return "resolved/Image.png"

        return None


@pytest.fixture
def app(tmp_path):
    config = AppConfig(vaults={'vault': VaultConfig(str(tmp_path))})
    AppState.indices['vault'] = DummyIndex()
    app = run(config, True)

    return app


def test_url_for_tag():
    assert md.url_for_tag('example',
                          'tag') == '/search/example?q=tag&mode=tags'


def test_parse_frontmatter_ok(tmp_path):
    text = """---
title: Test
key: demo
tags: [demo]
---

# Header
"""
    file = tmp_path / "note.md"
    file.write_text(text)
    out = md.parse_frontmatter(text, "note.md", 'example')
    assert "### Properties" in out
    assert "**title**: Test" in out
    assert "# Header" in out
    assert "['[==#demo==](/search/example?q=demo&mode=tags)']" in out
    text = """---
title: Test
key: demo
tags: [demo1, demo2]
---

    # Header
    """
    file.write_text(text)
    out = md.parse_frontmatter(text, "note.md", 'example')

    assert "['[==#demo1==](/search/example?q=demo1&mode=tags)', '[==#demo2==](/search/example?q=demo2&mode=tags)']" in out


def test_parse_frontmatter_broken(monkeypatch):
    monkeypatch.setattr(md.frontmatter, "parse",
                        lambda _: 1 / 0)  # force error
    out = md.parse_frontmatter("text", "bad.md", 'example')
    assert "text" in out  # returns original


def test_make_link_found():
    regex = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
    m = regex.search("[[Exists|Alias]]")
    out = md.make_link(m, Path("dummy.md"), DummyIndex())
    assert "[Alias](resolved/exists.md)" == out


def test_make_link_anchor_found():
    regex = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
    m = regex.search("[[Exists#header|Alias]]")
    out = md.make_link(m, Path("dummy.md"), DummyIndex())
    assert "[Alias](resolved/exists.md#header)" == out


def test_make_link_not_found(app, capsys):
    regex = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
    m = regex.search("[[Missing]]")
    with app.test_request_context():
        out = md.make_link(m, Path("dummy.md"), DummyIndex())
    assert out == '[*NOT FOUND* **Missing** *NOT FOUND*](/fastfileop/vault?op=file&curfile=dummy.md&dst=Missing.md)'


def test_parse_embedding_image(monkeypatch):
    text = "![[Image.png]]"
    idx = DummyIndex()
    monkeypatch.setattr(md, "url_for", lambda *a, **k: "/file/url")
    out = md.parse_embedding(text, Path("f.md"), idx, "vault1")
    assert "<img" in out
    assert "src=" in out


def test_parse_embedding_base(monkeypatch):
    text = "![[doc.base]]"
    idx = DummyIndex()
    monkeypatch.setattr(md, "url_for", lambda *a, **k: "/base/url")
    out = md.parse_embedding(text, Path("f.md"), idx, "vault1")
    assert "<iframe" in out


def test_parse_embedding_remote(monkeypatch):
    text = "![[Remote]]"
    idx = DummyIndex()
    monkeypatch.setattr(md, "url_for", lambda *a, **k: "/f/url")
    out = md.parse_embedding(text, Path("f.md"), idx, "vault1")
    assert "[Remote]" in out  # fallback link


def test_parse_embedding_missing():
    text = "![[NotFound]]"
    idx = DummyIndex()
    out = md.parse_embedding(text, Path("f.md"), idx, "vault1")
    assert "???NotFound???" in out


def test_preprocess_with_frontmatter(tmp_path):
    file = tmp_path / "note.md"
    file.write_text("---\ntitle: demo\n---\n\n[[Exists]] text")
    idx = DummyIndex()
    html = md.preprocess(file, idx, "vault")
    assert "<html" not in html  # mistune doesn’t wrap in full html
    assert "Properties" in html
    assert "<a" in html


@pytest.mark.parametrize("ext", [".base", ".excalidraw", ".txt"])
def test_render_renderer_redirect(monkeypatch, ext):
    monkeypatch.setattr(md, "redirect", lambda url: f"redirect:{url}")
    monkeypatch.setattr(md, "url_for", lambda *a, **k: f"/{a[0]}")
    out = md.render_renderer("v1", "f" + ext, Path("f" + ext))
    assert "redirect" in out
