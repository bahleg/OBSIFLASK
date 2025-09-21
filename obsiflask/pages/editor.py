"""
This module represents editor page logic
"""
from pathlib import Path

from flask import render_template, redirect, url_for, Response, request

from obsiflask.pages.renderer import preprocess
from obsiflask.pages.index_tree import render_tree
from obsiflask.app_state import AppState
from obsiflask.messages import add_message, type_to_int
from obsiflask.auth import get_user, get_user_config

def render_editor(vault: str, path: str, real_path: str) -> str | Response:
    """
    Render editor function

    Args:
        vault (str): vault name
        path (str): path w.r.t. vault root
        real_path (str): filesystem path

    Returns:
        str| Response: html page or redirect
    """
    text = None
    try:
        with open(real_path) as inp:
            text = inp.read()
    except Exception as e:
        add_message(f'attempt to load non-text file: {path}',
                    type_to_int['error'], vault, repr(e), user=get_user())
        text = None
    if text is None:
        return redirect(url_for('renderer', vault=vault, subpath=path))
    markdown = preprocess(real_path, AppState.indices[vault], vault)

    preview = request.args.get('preview')
    try:
        preview = int(preview) != 0
    except Exception:
        preview = get_user_config().editor_preview

    return render_template('editor.html',
                           markdown_text=text,
                           path=path,
                           vault=vault,
                           markdown_html=markdown,
                           navtree=render_tree(AppState.indices[vault], vault,
                                               True),
                           page_editor=True,
                           home=AppState.config.vaults[vault].home_file,
                           curdir=Path(path).parent,
                           curfile=path,
                           preview=preview)
