import pytest

import numpy as np

from obsiflask.pages.graph import (is_hex_color, make_default_filter,
                                   select_color, get_graph_and_legend,
                                   add_clusters, GraphRenderingRepresentation,
                                   get_filters)
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig
from obsiflask.main import run


@pytest.fixture
def app(tmp_path):
    config = AppConfig(vaults={'vault': VaultConfig(str(tmp_path))})
    AppState.messages[('vault', None)] = []
    app = run(config, True)
    return app


class DummyGraphRepr:

    def __init__(self):
        self.files = ["a", "b", "c"]
        self.node_labels = ["A", "B", "C"]
        self.href = ["hA", "hB", "hC"]
        self.edges = np.zeros((2, 2))
        self.edges[0] = np.array([0, 1])
        self.edges[1] = np.array([1, 2])
        self.tags = [2]  # only "C" as tag


@pytest.mark.parametrize("val,expected", [
    ("#fff", True),
    ("#FFFFFF", True),
    ("#123456", True),
    ("#12345678", True),
    ("#12", False),
    ("red", False),
    ("#GGG", False),
])
def test_is_hex_color(val, expected):
    assert is_hex_color(val) == expected


def test_make_default_filter():
    f = make_default_filter("#ff0000")
    assert isinstance(f, list)
    assert f[0]["label"] == "Pages"
    assert f[0]["color"] == "#ff0000"


def test_select_color():

    class DummyColor:

        def __init__(self, hexval):
            self.hex = hexval

    class DummyStop:

        def __init__(self, hexval):
            self.color = DummyColor(hexval)

    class DummyCmap:

        def __init__(self):
            self.color_stops = [DummyStop("#111111"), DummyStop("#222222")]
            self.bad_color = DummyColor("#000000")

    cmap = DummyCmap()
    used = set()
    c1 = select_color(cmap, used)
    assert c1 in {"#111111", "#222222"}
    assert c1 in used

    # второй вызов — другой цвет
    c2 = select_color(cmap, used)
    assert c2 != c1
    assert c2 in used


def test_get_graph_and_legend_basic(app, monkeypatch):
    from obsiflask.bases import filter
    monkeypatch.setattr(filter, "FieldFilter", lambda f: lambda x: True)

    cm = type("Cmap", (), {
        "color_stops": [],
        "bad_color": type("C", (), {"hex": "#000"})
    })()
    legend, graph = get_graph_and_legend(vault="vault",
                                         graph_data=DummyGraphRepr(),
                                         filters=[{
                                             "filter": None,
                                             "label": "All",
                                             "color": "#111111"
                                         }],
                                         used_colors=set(),
                                         include_tags=True,
                                         cm=cm,
                                         backlinks=False,
                                         tag_color="#ff00ff")

    assert isinstance(graph, GraphRenderingRepresentation)
    assert len(graph.node_labels) >= 3
    assert any("Tags" in l for l, _ in legend)


def test_add_clusters_merges_nodes():
    #  3 vertices and an edge
    g = GraphRenderingRepresentation(node_labels=["A", "B", "C"],
                                     edges=[(0, 1), (1, 2)],
                                     href=["hA", "hB", "hC"],
                                     colors=["#111", "#222", "#333"],
                                     sizes=[10, 20, 30])
    cm = type("Cmap", (), {
        "color_stops": [],
        "bad_color": type("C", (), {"hex": "#000"})()
    })()
    legend = []
    add_clusters(g, "vault", set(), legend, cm)

    assert any("Cluster" in lbl for lbl in g.node_labels)
    assert ("Clusters", ) == tuple(l[0] for l in legend)


def test_get_filters_with_default(monkeypatch, app):
    cm = type("Cmap", (), {
        "color_stops": [],
        "bad_color": type("C", (), {"hex": "#000"})()
    })()
    with app.test_request_context("/graph"):
        filters = get_filters("vault", cm, set())
        assert isinstance(filters, list)
        assert "color" in filters[0]
