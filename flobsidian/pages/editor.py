from flask import render_template
from flobsidian.pages.renderer import get_markdown
from flobsidian.pages.index_tree import render_tree
from flobsidian.singleton import Singleton

def render_editor(vault, path, real_path):
    with open(real_path) as inp:
        text = inp.read()
    markdown = get_markdown(real_path, Singleton.indices[vault])
    return render_template('editor.html',
                           markdown_text=text,
                           path=path,
                           vault=vault,
                           markdown_html = markdown,  
                            navtree = render_tree(Singleton.indices[vault], vault, False))
