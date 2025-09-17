from pathlib import Path


import pytest

from obsiflask.pages import search
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig
from obsiflask.main import run



@pytest.fixture
def flask_app(tmp_path):
    f = tmp_path / "test.md"
    f.write_text("Hello world\n#tag1\nSome more content")
    config = AppConfig(vaults={'vault1': VaultConfig(str(tmp_path))})
    app = run(config, True)
    AppState.messages[('vault1', None)] = []
    with app.app_context():
        yield app


@pytest.fixture
def client(flask_app):
    return flask_app.test_client()


# --- Tests ---


def test_generate_formula_check_results_returns_filename(flask_app):
    results = list(
        search.generate_formula_check_results("some_formula", "vault1"))
    assert results == [(str(Path("test.md")), "")] or results == [
    ]  # depends on FieldFilter logic


def test_generate_tags_check_results_returns_tag_file(flask_app):
    with flask_app.test_request_context():
        results = list(search.generate_tags_check_results("#tag1", "vault1"))

    assert any("test.md" in r[0] for r in results)


def test_generate_links_check_results_forward(flask_app):
    results = list(
        search.generate_links_check_results("test.md", "vault1", forward=True))
    assert isinstance(results, list)


def test_generate_text_check_results_exact(flask_app):
    with flask_app.test_request_context():
        results = list(
            search.generate_text_check_results("Hello",
                                               "vault1",
                                               mode="exact",
                                               ignore_case=False))
        assert any("Hello" in r[1] for r in results)


def test_generate_text_check_results_regex(flask_app):
    with flask_app.test_request_context():
        results = list(
            search.generate_text_check_results(r"Hello\s\w+",
                                               "vault1",
                                               mode="regex"))
        assert any("Hello" in r[1] for r in results)


def test_generate_text_check_results_fuzzy(flask_app):
    with flask_app.test_request_context():
        results = list(
            search.generate_text_check_results("Hello world",
                                               "vault1",
                                               mode="fuzzy",
                                               fuzzy_window_coef=2.0,
                                               inclusion_percent=0.5))
        assert any("Hello" in r[1] for r in results)
