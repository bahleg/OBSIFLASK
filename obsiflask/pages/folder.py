"""
The module represents a rendering page for fodlers
"""
from pathlib import Path

from flask import render_template, url_for, abort

from obsiflask.pages.index_tree import render_tree
from obsiflask.app_state import AppState


def render_folder(vault: str, subpath: str) -> None | str:
    """
    A rendering logic for folders

    Args:
        vault (str): vault name
        subpath (str): path (wrt vault)

    Returns:
        None | str: error code or resulting rendered page
    """
    abspath = AppState.indices[vault].path.resolve()
    target = (abspath / subpath).resolve()
    if abspath != target and abspath not in target.parents:
        return abort(400)

    files_folders = Path(abspath / subpath).resolve().glob('*')
    folders = []
    files = []
    for f in sorted(files_folders, key=lambda x: x.name):
        if not f.is_dir():
            files.append((str(f.relative_to(abspath)), f.name))
        else:
            folders.append((str(f.relative_to(abspath)), f.name))
    parent = Path(abspath / subpath).parent
    if Path(abspath / subpath).resolve() == abspath:
        parent_url = url_for('get_folder_root', vault=vault)
    elif abspath in list(target.parents):
        parent_url = url_for('get_folder',
                             subpath=parent.relative_to(abspath),
                             vault=vault)
    else:
        parent_url = None

    return render_template('folder.html',
                           subpath=subpath,
                           files=files,
                           folders=folders,
                           home=AppState.config.vaults[vault].home_file,
                           page_editor=False,
                           vault=vault,
                           parent_url=parent_url,
                           curdir=subpath)
