from dataclasses import asdict
from pathlib import Path
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
        
    nodespacing = request.args.get('nodespacong') or Singleton.config.default_user_config.default_graph_node_spacing
    stiffness = request.args.get('stiffness') or Singleton.config.default_user_config.default_graph_edge_stiffness
    edgelength = request.args.get('edgelength') or Singleton.config.default_user_config.default_graph_edge_length
    compression = request.args.get('compression') or Singleton.config.default_user_config.default_graph_compression
    
    
    
    graph_data: GraphRepr = asdict(Singleton.graphs[vault].build(refresh))
    return render_template(
        'graph.html',
        vault=vault,
        navtree=render_tree(Singleton.indices[vault], vault, True),
        page_editor=False,
        home=Singleton.config.vaults[vault].home_file,
        graph_data=graph_data,
        use_webgl=str(Singleton.config.default_user_config.use_webgl).lower(),
        debug_graph=str(Singleton.config.vaults[vault].graph_config.debug_graph).lower(),
        nodespacing = nodespacing, stiffness = stiffness, edgelength=edgelength, compression=compression)
