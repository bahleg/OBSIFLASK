import pytest

from obsiflask.graph import Graph, GraphRepr
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig
from obsiflask.main import run


@pytest.fixture
def app(tmp_path):
    config = AppConfig(vaults={
        'vault1':
        VaultConfig(str(tmp_path), autocomplete_max_ratio_in_key=1.0)
    })

    config.vaults['vault1'].graph_config.cache_time = 100000
    AppState.messages[('vault1', None)] = []
    # create mock markdown
    file_paths = []
    for name in ["file1.md", "file2.md", "file3.md"]:
        f = tmp_path / name
        f.write_text(f"# {name}\nSome content")
        file_paths.append(f)
    (tmp_path / "tagged.md").write_text('this is #tag')
    (tmp_path / "link.md"
     ).write_text('this is a [[file1#head| link to a section if file1.md]]')
    app = run(config, True)

    return app


def test_graph_build_basic(app):
    with app.test_request_context():
        vault = 'vault1'
        graph = Graph(vault)
        result = graph.build(rebuild=True)

        assert isinstance(result, GraphRepr)
        assert len(result.node_labels) == 6  # files + 1 tag
        assert result.edges.shape[0] == 2  # link and tag
        assert all(isinstance(h, str) for h in result.href)


def test_graph_build_cache(app):
    with app.test_request_context():
        vault = 'vault1'
        graph = Graph(vault)
        first_result = graph.build(rebuild=True)
        cached_result = graph.build(rebuild=False)
        assert cached_result is first_result


def test_graph_hint_index_handling(app, tmp_path):
    with app.test_request_context():
        vault = 'vault1'
        graph = Graph(vault)
        AppState.hints['vault1'].default_files_per_user[None] = []
        AppState.hints['vault1'].default_tags = []
        dry_result = graph.build(dry=True,
                                 populate_hint_files=False,
                                 populate_hint_tags=False)
        assert AppState.hints['vault1'].default_files_per_user[None] == []
        assert AppState.hints['vault1'].default_tags == []
        assert graph.result is None
        dry_result = graph.build(dry=True,
                                 populate_hint_files=True,
                                 populate_hint_tags=False)
        assert AppState.hints['vault1'].default_files_per_user[None] != []
        assert AppState.hints['vault1'].default_tags == []

        AppState.hints['vault1'].default_files_per_user[None] = []
        dry_result = graph.build(dry=True,
                                 populate_hint_files=False,
                                 populate_hint_tags=True)
        assert AppState.hints['vault1'].default_files_per_user[None] == []
        assert AppState.hints['vault1'].default_tags != []
