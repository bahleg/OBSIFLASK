"""
This module represents editor page logic
"""
from pathlib import Path
from threading import Lock

from flask import render_template, redirect, url_for, Response, request

from obsiflask.pages.renderer import preprocess
from obsiflask.app_state import AppState
from obsiflask.messages import add_message, type_to_int
from obsiflask.auth import get_user, get_user_config
from obsiflask.obfuscate import obf_open

lock = Lock()


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
        with lock:
            with obf_open(real_path, vault, 'r') as inp:
                text = inp.read()

    except Exception as e:
        add_message(f'attempt to load non-text file: {path}',
                    type_to_int['error'],
                    vault,
                    repr(e),
                    user=get_user())
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
                           page_editor=True,
                           home=AppState.config.vaults[vault].home_file,
                           curdir=Path(path).parent,
                           curfile=path,
                           preview=preview)
