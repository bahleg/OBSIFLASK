from pathlib import Path

from collections import defaultdict
from flobsidian.file_index import FileIndex
from flask import url_for
from flobsidian.singleton import Singleton


def render_tree(tree, vault, edit=False, level=0):
    rel_path = Singleton.indices[vault].path

    if isinstance(tree, FileIndex):
        tree = tree.get_tree()

    html = f"<ul class=\"list-unstyled\" style=\"padding-left:{level * 3}px;\">"
    root = True
    for name, child in tree.items():
        if child:  # папка
            if root:
                url = url_for('get_folder_root', vault=vault)
                root = False 
            else:
                url = url_for('get_folder',
                            vault=vault,
                            subpath=name.relative_to(rel_path))

            html += f"<li class=\"mb-1\"> <span class=\"fw-bold\"><a class=\"text-decoration-none\" href=\"{url}\">📁 {name.name}{render_tree(child, vault, edit, level=level+1)}</a></span></li>"
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
