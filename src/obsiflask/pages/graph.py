import numpy as np
from urllib import parse
import json
from copy import copy
from dataclasses import asdict, dataclass
from pathlib import Path
from cmap import Colormap
from flask import render_template, redirect, url_for, request
from obsiflask.pages.renderer import get_markdown
from obsiflask.pages.index_tree import render_tree
from obsiflask.singleton import Singleton
from obsiflask.utils import logger
from obsiflask.graph import Graph, GraphRepr
import networkx as nx
from networkx.algorithms.community import louvain_communities
from obsiflask.messages import add_message
import re
from obsiflask.bases.filter import FieldFilter


def is_hex_color(s: str) -> bool:
    return bool(
        re.fullmatch(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})", s))


@dataclass
class GraphRederingRepresentation:
    node_labels: list[str]
    edges: list[[int, int]]
    href: list[str]
    colors: list[str]
    sizes: list[int]


def make_default_filter(color_hex):
    return [{'filter': None, 'label': 'Pages', 'color': color_hex}]


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
    used_colors = set()

    filters = request.args.get('filters')
    if filters:
        try:
            filters = json.loads(parse.unquote(filters))
        except Exception as e:
            add_message(f'could not parse filters {filters}', 1, vault, repr(e))
            filters = None
        try:
            for f in filters:
                assert isinstance(f, dict)
        except Exception as e:
            add_message(f'could not parse filters {filters}', 1, vault, repr(e))
            filters = None

    if not filters:
        filters = make_default_filter(select_color(cm, used_colors))

    legend = []
    graph_data: GraphRepr = Singleton.graphs[vault].build(refresh)
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
                            1, vault, details=repr(e))
                ids = []
        else:
            ids = [i for i in range(len(graph_data.files)) if i not in used_ids]
        if len(ids) > 0:
            used_ids = used_ids | set(ids)
            out_ids.extend(ids)
            out_colors.extend([filter_color] * len(ids))
            legend.append((filter_.get('label', f'filter_{filter_id}'), filter_color))
    tag_color = select_color(cm, used_colors)
    if include_tags:

        if request.args.get('tag-color'):
            if is_hex_color(request.args['tag-color']):
                tag_color = request.args['tag-color']
            else:
                add_message(f'could not parse tag color: {tag_color}', 1,
                            vault)
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
    """
    filtered_edges = [(u, v) for u, v in graph_data.edges
                      if u in used_ids and v in used_ids]
    id_map = {old_id: new_id for new_id, old_id in enumerate(out_ids)}
    filtered_edges = [(id_map[u], id_map[v]) for u, v in graph_data.edges
                      if u in id_map and v in id_map]
    """


    out_ids = np.array(out_ids, dtype=np.uint16)
   
    # строим отображение старых id -> новых
    id_map = -np.ones(len(graph_data.node_labels), dtype=np.int64)  # заполняем -1
    id_map[out_ids] = np.arange(len(out_ids))  # новые индексы

    # edges как numpy массив формы (M, 2)
    edges = np.asarray(graph_data.edges, dtype=np.int64)

    # маска: обе вершины должны быть в out_ids (id_map != -1)
    mask = (id_map[edges[:, 0]] != -1) & (id_map[edges[:, 1]] != -1)

    # применяем маску и переиндексируем
    filtered_edges = np.column_stack((
        id_map[edges[mask, 0]],
        id_map[edges[mask, 1]]
    ))
    if backlinks:
        filtered_edges = filtered_edges[:, ::-1]
    deg = [0] * len(out_labels)
    for _, to_ in filtered_edges:
        deg[to_] += 1
    deg_max = max(deg)
    deg_min = min(deg)
    if deg_max == deg_min:
        sizes = [50] * len(graph_data.node_labels)
    else:
        denom = deg_max - deg_min
        sizes = [1 + (d - deg_min) / denom * 99 for d in deg]
    
    out_graph = GraphRederingRepresentation(out_labels, None,
                                            out_href, out_colors, sizes)

    fast = len(graph_data.node_labels) > Singleton.config.vaults[vault].graph_config.fast_graph_max_nodes\
             or len(filtered_edges) >  Singleton.config.vaults[vault].graph_config.fast_graph_max_edges
    try:
        force_clustering = int(request.args.get('clustering', 0))
    except:
        force_clustering = 0

    try:
        force_fast_disable = int(request.args.get('fast', 1)) == 0
    except:
        force_fast_disable = 0

    if fast and force_fast_disable:
        fast = False
    else:
        logger.warning('using fast options for faster computation')
    
    if fast or force_clustering:
        g = nx.digraph.DiGraph()
        for i in range(len(out_graph.node_labels)):
            g.add_node(i)
        for e in filtered_edges:
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
            if len(communities[i]) > 1:
                cluster_id += 1
                out_graph.node_labels.append(f'Cluster {cluster_id}')
                out_graph.sizes.append(200)
                out_graph.colors.append(cluster_color)
                id_to_cm[i] = len(out_graph.node_labels) - 1
        new_edges = []
        for i_id, cm in enumerate(communities):
            if len(cm) > 1:
                for i in cm:
                    new_edges.append((i, id_to_cm[i_id]))
        out_graph.edges = new_edges
    else:
        out_graph.edges = filtered_edges.tolist()
    return render_template(
        'graph.html',
        vault=vault,
        navtree=render_tree(Singleton.indices[vault], vault, True),
        page_editor=False,
        home=Singleton.config.vaults[vault].home_file,
        graph_data=out_graph,
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
        force_clustering=force_clustering,
        filters = json.dumps(filters),
        force_clustering_bool = int(force_clustering),
        fast_bool = int(not force_fast_disable),
        backlinks_bool = int(backlinks)
        
        )
