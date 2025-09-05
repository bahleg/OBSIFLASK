from pathlib import Path 
from flask import render_template, redirect, url_for, abort
from flobsidian.pages.renderer import get_markdown
from flobsidian.pages.index_tree import render_tree
from flobsidian.singleton import Singleton
from flobsidian.utils import logger


def render_excalidraw(vault, path, real_path):
    text = None
    try:
        with open(real_path) as inp:
            text = inp.read()
    except:
        logger.warning(f'attempt to load non-text file: {real_path}')
        text = None
    if text is None:
        return abort(500)
    
    return render_template('excalidraw_editor.html',
                           excalidraw_json=text,
                           path=path,
                           vault=vault,
                           navtree=render_tree(Singleton.indices[vault], vault,
                                               True),
                           page_editor=True,
                           home=Singleton.config.vaults[vault].home_file, curdir = Path(path).parent, curfile=path)
