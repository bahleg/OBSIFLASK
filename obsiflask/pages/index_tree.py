"""
A rendering nav tree logic
"""
from pathlib import Path

from flask import url_for, jsonify, request

from obsiflask.file_index import FileIndex
from obsiflask.app_state import AppState


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
            is_dir = child is not None
            if is_dir:
                items.append({
                    "title": f"{name.name}",
                    "folder": True,
                    "lazy": name.is_dir(),
                    "key": str(subpath_rel / name.name),
                })
            else:
                if edit:
                    url = url_for('editor',
                                  vault=vault,
                                  subpath=subpath_rel / name.name)
                else:
                    url = url_for('renderer',
                                  vault=vault,
                                  subpath=subpath_rel / name.name)

                items.append({
                    "title": f"{name.name}",
                    "key": str(subpath_rel / name.name),
                    "data": {
                        'url': url
                    }
                })
    return jsonify(items)
