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
    
    graph_data: GraphRepr = asdict(Singleton.graphs[vault].build(refresh))
    return render_template('graph.html',
                           vault=vault,
                           navtree=render_tree(Singleton.indices[vault], vault,
                                               True),
                           page_editor=True,
                           home=Singleton.config.vaults[vault].home_file,
                           graph_data=graph_data)
