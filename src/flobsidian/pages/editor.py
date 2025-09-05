from pathlib import Path
from flask import render_template, redirect, url_for
from flobsidian.pages.renderer import get_markdown
from flobsidian.pages.index_tree import render_tree
from flobsidian.singleton import Singleton
from flobsidian.utils import logger


def render_editor(vault, path, real_path):
    text = None
    try:
        with open(real_path) as inp:
            text = inp.read()
    except:
        logger.warning(f'attempt to load non-text file: {real_path}')
        text = None
    if text is None:
        return redirect(url_for('renderer', vault=vault, subpath=path))
    markdown = get_markdown(real_path, Singleton.indices[vault])
    return render_template('editor.html',
                           markdown_text=text,
                           path=path,
                           vault=vault,
                           markdown_html=markdown,
                           navtree=render_tree(Singleton.indices[vault], vault,
                                               True),
                           page_editor=True,
                           home=Singleton.config.vaults[vault].home_file,
                           curdir=Path(path).parent,
                           curfile=path)
