from pathlib import Path 
from flask import render_template, redirect, url_for, abort
from obsiflask.pages.renderer import get_markdown
from obsiflask.pages.index_tree import render_tree
from obsiflask.singleton import Singleton
from obsiflask.utils import logger

default_excalidraw = """{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [],
  "appState": {
    "gridSize": 20,
    "gridStep": 5,
    "gridModeEnabled": false,
    "viewBackgroundColor": "#ffffff",
    "lockedMultiSelections": {}
  },
  "files": {}
}"""

def render_excalidraw(vault, path, real_path):
    text = None
    try:
        with open(real_path) as inp:
            text = inp.read()
            if len(text.strip()) == 0:
                text = default_excalidraw

    except:
        logger.warning(f'attempt to load non-text file: {real_path}')
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
