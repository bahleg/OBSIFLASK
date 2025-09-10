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
import networkx as nx
from networkx.algorithms.community import louvain_communities


def select_color(cmap: Colormap, already: set):
    for c in cmap.color_stops:
        if c.color.hex in already:
            continue
        already.add(c.color.hex)
        return c.color.hex
    return cmap.bad_color.hex


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
        'nodespacing'
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
    legend = []
    graph_data: GraphRepr = Singleton.graphs[vault].build(refresh)
    graph_data = copy(graph_data)
    used_colors = set()
    colors = [select_color(cm, used_colors)] * len(graph_data.node_labels)
    legend.append(('Pages', colors[-1]))
    tag_color = select_color(cm, used_colors)
    if include_tags:
        for i in graph_data.tags:
            colors[i] = tag_color
        legend.append(('Tags', tag_color))
    graph_data.colors = colors
    tagset = set(graph_data.tags)
    if not include_tags:
        nodes = [
            graph_data.node_labels[i]
            for i in range(len(graph_data.node_labels)) if i not in tagset
        ]

        colors = [
            graph_data.colors[i] for i in range(len(graph_data.node_labels))
            if i not in tagset
        ]
        links = [
            i for i in graph_data.forward_edges
            if i[0] not in tagset and i[1] not in tagset
        ]
        graph_data.colors = colors
        graph_data.node_labels = nodes
        graph_data.forward_edges = links

    if backlinks:
        links = [(i[1], i[0]) for i in graph_data.forward_edges]
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

    fast = len(graph_data.node_labels) > Singleton.config.vaults[vault].graph_config.fast_graph_max_nodes\
             or len(graph_data.forward_edges) >  Singleton.config.vaults[vault].graph_config.fast_graph_max_edges
    force_clustering = int(request.args.get('clustering', 0))
    force_fast_disable = int(request.args.get('fast', 1)) == 0
    if fast and force_fast_disable:
        fast = False
    else:
        logger.warning('using fast options for faster computation')

    if fast or force_clustering:
        g = nx.digraph.DiGraph()
        for i in range(len(graph_data.node_labels)):
            g.add_node(i)
        for e in graph_data.forward_edges:
            g.add_edge(e[0], e[1])
        communities = louvain_communities(
            g,
            seed=42,
            resolution=Singleton.config.vaults[vault].graph_config.
            louvain_communities_res)
        id_to_cm = {}
        cluster_color = select_color(cm, used_colors)
        legend.append(('Clusters', cluster_color))
        cluster_id = 0
        for i in range(len(communities)):
            if len(communities[i])>1:
                cluster_id+=1
                graph_data.node_labels.append(f'Cluster {cluster_id}')
                graph_data.node_sizes.append(200)
                graph_data.colors.append(cluster_color)
                id_to_cm[i] = len(graph_data.node_labels) - 1
        new_edges = []
        for i_id, cm in enumerate(communities):
            if len(cm)>1:
                for i in cm:
                    new_edges.append((i, id_to_cm[i_id]))
        graph_data.forward_edges = new_edges
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
        include_tags=include_tags,
        compression=compression,
        fast=fast,
        tag_color=tag_color,
        backlinks=backlinks,
        force_fast_disable=force_fast_disable,
        legend=legend,
        force_clustering=force_clustering)
