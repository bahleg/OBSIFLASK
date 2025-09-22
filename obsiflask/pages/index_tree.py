"""
A rendering nav tree logic
"""
from obsiflask.file_index import FileIndex
from flask import url_for
from obsiflask.app_state import AppState


def render_tree(tree: dict[str, dict | str],
                vault: str,
                edit: bool = False,
                level: int = 0) -> str:
    """
    A recursive function for rendering tree

    Args:
        tree (dict[str, dict|str]): tree object
        vault (str): vault name
        edit (bool, optional): flag if we're in editor state. Defaults to False.
        level (int, optional): nesting level. Defaults to 0.

    Returns:
        str: returned html
    """
    rel_path = AppState.indices[vault].path

    if isinstance(tree, FileIndex):
        tree = tree.get_tree()
        root = True
    else:
        root = False

    html = f"<ul class=\"list-unstyled\" style=\"padding-left:{level * 3}px;\">"

    for name, child in tree.items():
        if child:  # folder
            if root:
                url = url_for('get_folder_root', vault=vault)
                root = False
            else:
                url = url_for('get_folder',
                              vault=vault,
                              subpath=name.relative_to(rel_path))

            html += f"<li class=\"mb-1\"> <span class=\"fw-bold\"><a class=\"text-decoration-none\" href=\"{url}\">📁 {name.name}{render_tree(child, vault, edit, level=level+1)}</a></span></li>"
        else:  # file

            if edit:
                url = url_for('editor',
                              vault=vault,
                              subpath=name.relative_to(rel_path))
            else:
                url = url_for('renderer',
                              vault=vault,
                              subpath=name.relative_to(rel_path))
            html += f"<li><a href=\"{url}\" class=\"text-decoration-none\">📄 {name.name}</a></li>"
    html += "</ul>"
    return html
