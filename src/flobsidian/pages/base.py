from flask import render_template, redirect, url_for, render_template_string
import mistune
import re
from flobsidian.singleton import Singleton
from flobsidian.file_index import FileIndex
from pathlib import Path
from urllib import parse
from flobsidian.utils import logger
import frontmatter
from markupsafe import Markup
from flobsidian.bases.base_parser import parse_base
from flobsidian.pages.index_tree import render_tree


def render_base(vault, subpath, real_path):
    return render_base_view(vault, subpath, real_path)


def render_base_view(vault, subpath, real_path, view=None):
    base = parse_base(real_path, vault)
    if view is None:
        key = list(base.views.keys())[0]
    result = base.views[key].make_view(vault)

    return render_template('base_table_view.html',
                           table=result,
                           navtree=render_tree(Singleton.indices[vault], vault,
                                               False),
                           is_editor=False,
                           home=Singleton.config.vaults[vault].home_file,
                           curdir=Path(subpath).parent,
                           curfile=subpath, vault=vault, path=subpath)
