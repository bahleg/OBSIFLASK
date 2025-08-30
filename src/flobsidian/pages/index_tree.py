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


def render_tree(tree, vault, edit=False, level=0):
    rel_path = Singleton.indices[vault].path

    if isinstance(tree, FileIndex):
        tree = build_tree(tree)
    html = f"<ul class=\"list-unstyled\" style=\"padding-left:{level * 3}px;\">"
    for name, child in tree.items():
        if child:  # папка
            html += f"<li class=\"mb-1\"> <span class=\"fw-bold\">📁 {name.name}{render_tree(child, vault, edit, level=level+1)}</span></li>"
        else:  # файл

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
