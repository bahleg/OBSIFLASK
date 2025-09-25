"""
The module describes rendering logic for Excalidraw editor page
"""

from pathlib import Path
from threading import Lock

from flask import render_template, abort

from obsiflask.pages.index_tree import render_tree
from obsiflask.app_state import AppState
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

lock = Lock()


def render_excalidraw(vault: str, path: str, real_path: str) -> str:
    """
  Rendering logic

  Args:
      vault (str): vault name
      path (str): path w.r.t. vault
      real_path (str): filesystem path

  Returns:
      str: html rendered code
  """
    text = None
    try:
        with lock:
            with open(real_path) as inp:
                text = inp.read()
                if len(text.strip()) == 0:
                    text = default_excalidraw

    except Exception as e:
        logger.warning(f'attempt to load non-text file: {real_path}: {e}')
    if text is None:
        return abort(400)
    return render_template('excalidraw_editor.html',
                           excalidraw_json=text,
                           path=path,
                           vault=vault,
                           page_editor=True,
                           home=AppState.config.vaults[vault].home_file,
                           curdir=Path(path).parent,
                           curfile=path)
