"""
Rendering logic for graphs
"""
import re
from urllib import parse
import json
from copy import copy
from dataclasses import dataclass
from typing import Any

import numpy as np
from cmap import Colormap
from flask import render_template, request
import networkx as nx

from obsiflask.app_state import AppState
from obsiflask.utils import logger
from obsiflask.graph import GraphRepr
from networkx.algorithms.community import louvain_communities
from obsiflask.messages import add_message
from obsiflask.bases.filter import FieldFilter
from obsiflask.auth import get_user_config
from obsiflask.utils import get_traceback


def is_hex_color(s: str) -> bool:
    """
    Helper to check if string is hex color

    Args:
        s (str): string to check

    Returns:
        bool: flag for hex
    """
    return bool(
        re.fullmatch(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})", s))


@dataclass
class GraphRenderingRepresentation:
    """
    Rendering representation
    """
    node_labels: list[str]
    edges: list[tuple[int, int]]
    href: list[str]
    colors: list[str]
    sizes: list[int]


def make_default_filter(color_hex) -> list[dict[str, Any]]:
    """
    A default filter if filters not set
    """
    return [{'filter': None, 'label': 'Pages', 'color': color_hex}]


def select_color(cmap: Colormap, already: set):
    """
    Helper to get new color from colormap
    """
    for c in cmap.color_stops:
        if c.color.hex in already:
            continue
        already.add(c.color.hex)
        return c.color.hex
    return cmap.bad_color.hex


def get_graph_and_legend(
        vault: str, graph_data: GraphRepr, filters: list[dict[str, Any]],
        used_colors: set[str], include_tags: bool, cm: Colormap,
        backlinks: bool,
        tag_color: str) -> tuple[list, GraphRenderingRepresentation]:
    """
    Gets a graph and corresponding legend for it

    Args:
        vault (str): vault name
        graph_data (GraphRepr): graph data
        filters (list[dict[str, Any]]): filters for vertices
        used_colors (set[str]): already used colors
        include_tags (bool): if set, will also add tags
        cm (Colormap): used colormap
        backlinks (bool): if set, will build a back-edges
        tag_color (str): color for tags

    Returns:
        tuple[list, GraphRenderingRepresentation]: legend, graph
    """
    legend = []
    graph_data = copy(graph_data)
    out_ids = []
    out_colors = []
    used_ids = set()
    for filter_id, filter_ in enumerate(filters):
        filter_color = None
        if 'color' in filter_:
            if is_hex_color(filter_['color']):
                filter_color = filter_['color']
                used_colors.add(filter_color)
            else:
                add_message(
                    f'could not parse color during graph building: {filter_["color"]}',
                    1, vault)
        if filter_color is None:
            filter_color = select_color(cm, used_colors)

        filter_filter = filter_.get('filter')
        if filter_filter:
            try:
                field_filter = FieldFilter(filter_filter)
                ids = [
                    i for i in range(len(graph_data.files))
                    if i not in used_ids
                    and field_filter.check(graph_data.files[i])
                ]
            except Exception as e:
                add_message(f'problems during node filtering: {filter_filter}',
                            1,
                            vault,
                            details=get_traceback(e))
                ids = []
        else:
            ids = [
                i for i in range(len(graph_data.files)) if i not in used_ids
            ]
        if len(ids) > 0:
            used_ids = used_ids | set(ids)
            out_ids.extend(ids)
            out_colors.extend([filter_color] * len(ids))
            legend.append((filter_.get('label',
                                       f'filter_{filter_id}'), filter_color))
    if include_tags:
        tagset = set(graph_data.tags)
        if len(tagset) > 0:
            legend.append(('Tags', tag_color))
            for i in graph_data.tags:
                out_colors.append(tag_color)
                out_ids.append(i)
                used_ids.add(i)
    out_labels = []
    out_href = []
    for i in out_ids:
        out_labels.append(graph_data.node_labels[i])
        out_href.append(graph_data.href[i])

    out_ids = np.array(out_ids, dtype=np.uint16)

    # old ids to new
    id_map = -np.ones(len(graph_data.node_labels), dtype=np.int32)  # set -1
    id_map[out_ids] = np.arange(len(out_ids))  # new indices
    edges = np.asarray(graph_data.edges, dtype=np.uint32)

    # Mask: both vertices must be in out_ids (id_map != -1)
    mask = (id_map[edges[:, 0]] != -1) & (id_map[edges[:, 1]] != -1)

    # apply mask
    filtered_edges = np.column_stack(
        (id_map[edges[mask, 0]], id_map[edges[mask, 1]]))
    if backlinks:
        filtered_edges = filtered_edges[:, ::-1]
    deg = [0] * len(out_labels)
    for _, to_ in filtered_edges:
        deg[to_] += 1
    if len(deg) == 0:
        sizes = []
    else:
        deg_max = max(deg)
        deg_min = min(deg)
        if deg_max == deg_min:
            sizes = [50] * len(out_labels)
        else:
            denom = deg_max - deg_min
            sizes = [1 + (d - deg_min) / denom * 99 for d in deg]

    out_graph = GraphRenderingRepresentation(out_labels, filtered_edges,
                                             out_href, out_colors, sizes)
    return legend, out_graph


def get_filters(vault: str, cm: Colormap,
                used_colors: set[str]) -> list[dict[str, Any]]:
    """
    Filter parsing 

    Args:
        vault (str): vault name
        cm (Colormap): used colormap
        used_colors (set[str]): colors for using

    Returns:
        list[dict[str, Any]]: list of parsed filters
    """
    filters = request.args.get('filters')
    if filters:
        try:
            filters = json.loads(parse.unquote(filters))
        except Exception as e:
            add_message(f'could not parse filters {filters}', 1, vault,
                        get_traceback(e))
            filters = None

        try:
            for f in filters:
                assert isinstance(f, dict)
        except Exception as e:
            add_message(f'could not parse filters {filters}', 1, vault,
                        get_traceback(e))
            filters = None

    if not filters:
        filters = make_default_filter(select_color(cm, used_colors))
    return filters


def add_clusters(out_graph: GraphRenderingRepresentation, vault: str,
                 used_colors: set[str], legend: list, cm: Colormap):
    """
    Adds clusters to graph

    Args:
        out_graph (GraphRenderingRepresentation): graph representation
        vault (str): vault name
        used_colors (set[str]): set of already used colors
        legend (list): legend
        cm (Colormap): color map
    """
    g = nx.digraph.DiGraph()
    filtered_edges = out_graph.edges

    for i in range(len(out_graph.node_labels)):
        g.add_node(i)
    for e in filtered_edges:
        g.add_edge(e[0], e[1])
    communities = louvain_communities(g,
                                      seed=42,
                                      resolution=AppState.config.vaults[vault].
                                      graph_config.louvain_communities_res)
    id_to_cm = {}
    cluster_color = select_color(cm, used_colors)
    legend.append(('Clusters', cluster_color))

    cluster_id = 0
    for i in range(len(communities)):
        if len(communities[i]) > 1:
            cluster_id += 1
            out_graph.node_labels.append(f'Cluster {cluster_id}')
            out_graph.sizes.append(200)
            out_graph.colors.append(cluster_color)
            id_to_cm[i] = len(out_graph.node_labels) - 1
    new_edges = []
    for i_id, comm in enumerate(communities):
        if len(comm) > 1:
            for i in comm:
                new_edges.append((i, id_to_cm[i_id]))

    out_graph.edges = new_edges


def render_graph(vault: str) -> str:
    """
    Logic for graph rendering
    """

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

    nodespacing = request.args.get('nodespacing') or AppState.config.vaults[
        vault].graph_config.default_graph_node_spacing
    stiffness = request.args.get('stiffness') or AppState.config.vaults[
        vault].graph_config.default_graph_edge_stiffness
    edgelength = request.args.get('edgelength') or AppState.config.vaults[
        vault].graph_config.default_graph_edge_length
    compression = request.args.get('compression') or AppState.config.vaults[
        vault].graph_config.default_graph_compression

    cm = Colormap(get_user_config().graph_cmap)
    used_colors = set()

    filters = get_filters(vault, cm, used_colors)

    tag_color = None
    if include_tags:
        if request.args.get('tag-color'):
            if is_hex_color(request.args['tag-color']):
                tag_color = request.args['tag-color']
                used_colors.add(tag_color)
            else:
                add_message(f'could not parse tag color: {tag_color}', 1,
                            vault)
    if tag_color is None:
        tag_color = select_color(cm, used_colors)

    graph_data = AppState.graphs[vault].build(refresh)
    legend, out_graph = get_graph_and_legend(vault, graph_data, filters,
                                             used_colors, include_tags, cm,
                                             backlinks, tag_color)
    filtered_edges = out_graph.edges

    fast = len(out_graph.node_labels) > AppState.config.vaults[vault].graph_config.fast_graph_max_nodes\
        or len(filtered_edges) > AppState.config.vaults[vault].graph_config.fast_graph_max_edges
    try:
        force_clustering = int(request.args.get('clustering', 0))
    except Exception:
        force_clustering = 0

    try:
        force_fast_disable = int(request.args.get('fast', 1)) == 0
    except Exception:
        force_fast_disable = 0

    if fast and force_fast_disable:
        fast = False
    else:
        logger.warning('using fast options for faster computation')

    if fast or force_clustering:
        add_clusters(out_graph, vault, used_colors, legend, cm)
    else:
        out_graph.edges = filtered_edges.tolist()
    return render_template(
        'graph.html',
        vault=vault,
        page_editor=False,
        home=AppState.config.vaults[vault].home_file,
        graph_data=out_graph,
        use_webgl=str(get_user_config().use_webgl).lower(),
        debug_graph=str(
            AppState.config.vaults[vault].graph_config.debug_graph).lower(),
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
        force_clustering=force_clustering,
        filters=json.dumps(filters),
        force_clustering_bool=int(force_clustering),
        fast_bool=int(not force_fast_disable),
        backlinks_bool=int(backlinks))
