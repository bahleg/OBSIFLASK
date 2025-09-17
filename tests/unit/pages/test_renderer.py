import io
import re
import pytest
from pathlib import Path
from types import SimpleNamespace
from markupsafe import Markup

import obsiflask.pages.renderer as md


class DummyIndex:
    def __init__(self, path="/vault"):
        self.path = Path(path)

    def resolve_wikilink(self, name, file_path, create=False, **kwargs):
        # very simplified fake resolver
        if name == "Exists":
            return "resolved/exists.md"
        if name == "Image":
            return "image.png"
        if name == "Remote":
            return "http://example.com"
        if name == "doc.base":
            return "resolved/doc.base"
        if name == "Image.png":
            return "resolved/Image.png"
        
        return None


def test_parse_frontmatter_ok(tmp_path):
    text = """---
title: Test
tag: demo
---

# Header
"""
    file = tmp_path / "note.md"
    file.write_text(text)
    out = md.parse_frontmatter(text, "note.md")
    assert "### Properties" in out
    assert "**title**: Test" in out
    assert "# Header" in out


def test_parse_frontmatter_broken(monkeypatch):
    monkeypatch.setattr(md.frontmatter, "parse", lambda _: 1/0)  # force error
    out = md.parse_frontmatter("text", "bad.md")
    assert "text" in out  # returns original


def test_make_link_found():
    regex = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
    m = regex.search("[[Exists|Alias]]")
    out = md.make_link(m, Path("dummy.md"), DummyIndex())
    assert "[Alias](resolved/exists.md)" == out


def test_make_link_not_found(capsys):
    regex = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
    m = regex.search("[[Missing]]")
    out = md.make_link(m, Path("dummy.md"), DummyIndex())
    assert "???Missing???" in out
    

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
    html = md.preprocess(file, idx, "vault1")
    assert "<html" not in html  # mistune doesn’t wrap in full html
    assert "Properties" in html
    assert "<a" in html


@pytest.mark.parametrize("ext", [".base", ".excalidraw", ".txt"])
def test_render_renderer_redirect(monkeypatch, ext):
    monkeypatch.setattr(md, "redirect", lambda url: f"redirect:{url}")
    monkeypatch.setattr(md, "url_for", lambda *a, **k: f"/{a[0]}")
    out = md.render_renderer("v1", "f"+ext, Path("f"+ext))
    assert "redirect" in out
