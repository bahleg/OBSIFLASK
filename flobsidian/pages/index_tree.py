from pathlib import Path 

from collections import defaultdict
from flobsidian.file_index import FileIndex
from flask import url_for
from flobsidian.singleton import Singleton

def build_tree(file_paths):
    tree = {}
    for path in file_paths:
        node = tree
        for parent in path.parents[::-1]:
            if parent not in node:
                node[parent] = {}
            node = node[parent]
        if not path.is_dir():
            node[path] = None
        else:
            node[path] = {}
    return tree


def render_tree(
    tree,
    vault,
    edit=False,
):
    rel_path = Singleton.indices[vault].path
    
    if isinstance(tree, FileIndex):
        tree = build_tree(tree)
    html = "<ul>"
    for name, child in tree.items():
        if child:  # папка
            html += f"<li>📁 {name.name}{render_tree(child, vault, edit)}</li>"
        else:  # файл

            if edit:
                url = url_for('editor', vault=vault, subpath=str(name.name))
            else:
                url = url_for('renderer', vault=vault, subpath=name.relative_to(rel_path))
            html += f"<li><a href=\"{url}\">📄 {name.name}</a></li>"
    html += "</ul>"
    return html
