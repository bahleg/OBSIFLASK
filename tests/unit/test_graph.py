import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from obsiflask.graph import Graph, GraphRepr
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig
from obsiflask.main import run


@pytest.fixture
def app(tmp_path):
    config = AppConfig(vaults={'vault1': VaultConfig(str(tmp_path))})
    config.vaults['vault1'].graph_config.cache_time = 100000
    AppState.messages[('vault1', None)] = []
    # создаём фиктивные markdown файлы
    file_paths = []
    for name in ["file1.md", "file2.md", "file3.md"]:
        f = tmp_path / name
        f.write_text(f"# {name}\nSome content")
        file_paths.append(f)
    app = run(config, True)

    return app


def test_graph_build_basic(app):
    with app.test_request_context():
        vault = 'vault1'
        graph = Graph(vault)
        result = graph.build(rebuild=True)

        assert isinstance(result, GraphRepr)
        assert len(result.node_labels) == 3
        assert result.edges.shape[0] == 0  # no links
        assert all(isinstance(h, str) for h in result.href)
        assert result.files[0].vault_path.name == "file1.md"


def test_graph_build_cache(app):
    with app.test_request_context():
        vault = 'vault1'
        graph = Graph(vault)
        first_result = graph.build(rebuild=True)
        cached_result = graph.build(rebuild=False)
        assert cached_result is first_result
