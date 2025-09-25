"""
A rendering nav tree logic
"""
from pathlib import Path

from flask import url_for, jsonify, request

from obsiflask.file_index import FileIndex
from obsiflask.app_state import AppState


def get_menu(key: str, vault: str, is_dir: bool):
    menu = []
    if is_dir:
        menu.append({
            'title': '📂 Open folder',
            'url': url_for('get_folder', vault=vault, subpath=key)
        })
    else:
        if key.endswith(('.md', '.excalidraw')):
            menu.append({
                'title': '👁️ Show',
                'url': url_for('renderer', vault=vault, subpath=key)
            })
            menu.append({
                'title': '✏️ Edit',
                'url': url_for('editor', vault=vault, subpath=key)
            })
        menu.append({
            'title': '📥 Download',
            'url': url_for('get_file', vault=vault, subpath=key)
        })

    if is_dir:
        menu.append({
            'title': '🗃️ File operations',
            'url': url_for('fileop', vault=vault, curdir=key)
        })
    else:
        if key.count('/') == 0:
            curdir = '.'
        else:
            curdir = key.rsplit('/', 1)[0]
        menu.append({
            'title':
            '🗃️ File operations',
            'url':
            url_for('fileop', vault=vault, curfile=key, curdir=curdir)
        })
    return menu


def render_tree(tree: dict[str, dict | str], vault: str, subpath: str) -> str:
    """
    A recursive function for rendering tree

    Args:
        tree (dict[str, dict|str]): tree object
        vault (str): vault name
        subpath (str): str 
        edit (bool, optional): flag if we're in editor state. Defaults to False.
        level (int, optional): nesting level. Defaults to 0.

    Returns:
        str: returned html
    """
    edit = request.args.get('edit', '0')
    if edit not in [0, '0', '', False, 'false', 'False']:
        edit = True
    else:
        edit = False
    items = []
    if isinstance(tree, FileIndex):
        tree = tree.get_tree()
    is_root = subpath == ''
    subpath = Path(AppState.indices[vault].path / subpath).resolve()
    subpath_rel = subpath.relative_to(AppState.indices[vault].path)
    if not is_root:
        tree = tree[AppState.indices[vault].path]
        for part in list(subpath_rel.parents)[::-1][1:]:
            tree = tree[AppState.indices[vault].path / part]
    tree = tree[AppState.indices[vault].path / subpath_rel]
    if tree is not None:
        for name, child in sorted(tree.items(),
                                  key=lambda x: (x[1] is None, x[0])):
            key = str(subpath_rel / name.name)
            is_dir = child is not None
            if is_dir:
                items.append({
                    "title": f"{name.name}",
                    "folder": True,
                    "lazy": name.is_dir(),
                    "key": key,
                    "data": {
                        'menu': get_menu(key, vault, True)
                    }
                })
            else:
                if edit:
                    url = url_for('editor', vault=vault, subpath=key)
                else:
                    url = url_for('renderer', vault=vault, subpath=key)
                menu = get_menu(key, vault, False)
                items.append({
                    "title": f"{name.name}",
                    "key": key,
                    "data": {
                        'url': url,
                        'menu': menu
                    }
                })

    return jsonify(items)
