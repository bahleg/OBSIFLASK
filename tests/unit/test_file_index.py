import pytest

from obsiflask.file_index import FileIndex
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig


@pytest.fixture
def sample_vault(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "note1.md").write_text("# note1")
    (vault / "note2.md").write_text("# note2")
    subdir = vault / "sub"
    subdir.mkdir()
    (subdir / "note3.md").write_text("# note3")
    config = AppConfig(vaults={'default': VaultConfig(str(tmp_path))})
    AppState.config = config
    return vault


def test_refresh_and_files(sample_vault):
    fi = FileIndex(str(sample_vault), template_dir=None, vault="default")
    fi.refresh()
    files = list(fi._files)
    assert (sample_vault / "note1.md") in files
    assert (sample_vault / "sub" / "note3.md") in files
    assert len(fi) == len(files)


def test_name_to_path(sample_vault):
    fi = FileIndex(str(sample_vault), template_dir=None, vault="default")
    fi.refresh()
    name_to_path = fi.get_name_to_path()

    assert "note1.md" in name_to_path
    assert sample_vault in name_to_path["note1.md"]


def test_get_tree(sample_vault):
    fi = FileIndex(str(sample_vault), template_dir=None, vault="default")
    fi.refresh()
    tree = fi.get_tree()

    assert any(isinstance(v, dict) for v in tree.values())


def test_resolve_wikilink_local(sample_vault):
    fi = FileIndex(str(sample_vault), template_dir=None, vault="default")
    fi.refresh()

    link = fi.resolve_wikilink("note1.md", sample_vault / "dummy.md")
    assert "note1.md" in link


def test_resolve_wikilink_md_without_ext(sample_vault):
    fi = FileIndex(str(sample_vault), template_dir=None, vault="default")
    fi.refresh()

    link = fi.resolve_wikilink("note1",
                               sample_vault / "dummy.md",
                               resolve_markdown_without_ext=True)
    assert "note1.md" in link
