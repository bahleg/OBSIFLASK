from pathlib import Path
import types

import pytest

from obsiflask.app_state import AppState
from obsiflask.bases.file_info import FileInfo


class DummyIndex:

    def __init__(self, path: Path):
        self.path = path

    def resolve_wikilink(self, link, real_path, *a, **kw):
        return f"resolved:{link}"


class DummyBaseConfig:

    def __init__(self, error_on_field_parse=False, cache_time=1000):
        self.error_on_field_parse = error_on_field_parse
        self.cache_time = cache_time


class DummyConfig:

    def __init__(self):
        self.vaults = {}


@pytest.fixture(autouse=True)
def setup_appstate(tmp_path, monkeypatch):
    vault = "v1"
    vault_path = tmp_path
    AppState.indices = {vault: DummyIndex(vault_path)}
    AppState.config = DummyConfig()
    AppState.config.vaults[vault] = types.SimpleNamespace(
        base_config=DummyBaseConfig())
    yield


def make_file(tmp_path, content, name="note.md"):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_get_internal_data_reads_links_and_tags(tmp_path):
    file = make_file(tmp_path, "hello [[page]] #tag1 #tag2")
    fi = FileInfo(file, "v1")
    fi.get_internal_data()
    assert "tag1" in fi._tags
    assert "tag2" in fi._tags
    assert "resolved:page" in fi._links
    assert fi.read is True


def test_get_internal_data_non_md_sets_read(tmp_path):
    file = make_file(tmp_path, "binarydata", "bin.txt")
    fi = FileInfo(file, "v1")
    fi.get_internal_data()
    assert fi.read is True
    assert fi._tags == set()
    assert fi._links == set()


def test_handle_cover_resolves_relative(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    cover = sub / "cover.png"
    cover.write_text("x")
    fi = FileInfo(cover, "v1")
    result = fi.handle_cover("cover.png")
    assert result.endswith("cover.png")
    # must be relative w.r.t. vault index
    assert not result.startswith("/")


def test_get_prop_file_variants(tmp_path):
    file = make_file(tmp_path, "# fm\n", "note.md")
    fi = FileInfo(file, "v1")
    # name without render
    assert fi.get_prop(("file", "name")) == "note.md"
    # name with render → ht
