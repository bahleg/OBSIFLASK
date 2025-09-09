from copy import copy
from dataclasses import asdict
from pathlib import Path
from cmap import Colormap
from flask import render_template, redirect, url_for, request
from flobsidian.pages.renderer import get_markdown
from flobsidian.pages.index_tree import render_tree
from flobsidian.singleton import Singleton
from flobsidian.utils import logger
from flobsidian.graph import Graph, GraphRepr


def render_graph(vault):
    if request.args.get('refresh'):
        refresh = True
    else:
        refresh = False

    if request.args.get('tags') and int(request.args.get('tags')):
        include_tags = True
    else:
        include_tags = False

    if request.args.get('backlinks') and int(request.args.get('backlinks')):
        backlinks = True
    else:
        backlinks = False

    nodespacing = request.args.get(
        'nodespacong'
    ) or Singleton.config.default_user_config.default_graph_node_spacing
    stiffness = request.args.get(
        'stiffness'
    ) or Singleton.config.default_user_config.default_graph_edge_stiffness
    edgelength = request.args.get(
        'edgelength'
    ) or Singleton.config.default_user_config.default_graph_edge_length
    compression = request.args.get(
        'compression'
    ) or Singleton.config.default_user_config.default_graph_compression
    cm = Colormap(Singleton.config.default_user_config.graph_cmap)

    graph_data: GraphRepr = Singleton.graphs[vault].build(refresh)
    graph_data = copy(graph_data)
    colors = [cm.color_stops[0].color.hex] * len(graph_data.node_labels)
    for i in graph_data.tags:
        colors[i] = cm.color_stops[1].color.hex
    graph_data.colors = colors
    tagset = set(graph_data.tags)
    if not include_tags:
        nodes = [
            graph_data.node_labels[i]
            for i in range(len(graph_data.node_labels)) if i not in tagset
        ]
        links = [
            i for i in graph_data.forward_edges
            if i[0] not in tagset and i[1] not in tagset
        ]
        graph_data.node_labels = nodes
        graph_data.forward_edges = links

    if backlinks:
        links = [(i[1],i[0]) for i in graph_data.forward_edges]
        graph_data.forward_edges = links

    deg = [0] * len(graph_data.node_labels)
    for _, to_ in graph_data.forward_edges:
            deg[to_] += 1
    deg_max = max(deg)
    deg_min = min(deg)
    if deg_max == deg_min:
        sizes = [50] * len(graph_data.node_labels)
    else:
        denom = deg_max - deg_min
        sizes = [1 + (d - deg_min) / denom * 99 for d in deg]

    graph_data.node_sizes = sizes

    return render_template(
        'graph.html',
        vault=vault,
        navtree=render_tree(Singleton.indices[vault], vault, True),
        page_editor=False,
        home=Singleton.config.vaults[vault].home_file,
        graph_data=graph_data,
        use_webgl=str(Singleton.config.default_user_config.use_webgl).lower(),
        debug_graph=str(
            Singleton.config.vaults[vault].graph_config.debug_graph).lower(),
        nodespacing=nodespacing,
        stiffness=stiffness,
        edgelength=edgelength,
        compression=compression)
