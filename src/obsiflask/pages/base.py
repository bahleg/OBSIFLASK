from flask import render_template, redirect, url_for, render_template_string, request, abort
import mistune
import re
from obsiflask.singleton import Singleton
from obsiflask.file_index import FileIndex
from pathlib import Path
from urllib import parse
from obsiflask.utils import logger
import frontmatter
from markupsafe import Markup
from obsiflask.bases.base_parser import parse_base
from obsiflask.pages.index_tree import render_tree


def render_base(vault, subpath, real_path):
    return render_base_view(vault, subpath, real_path)


def render_base_view(vault, subpath, real_path):
    base = parse_base(real_path, vault)
    view = request.args.get('view')
    if view is None:
        key = list(base.views.keys())[0]
    else:
        if view not in base.views.keys():
            return f'Bad view: {view}', 402
        key = view

    if request.args.get('refresh'):
        refresh = True
    else:
        refresh = False
    current_view = key
    base_url = url_for('base', subpath=subpath, vault=vault)
    all_views = []
    if request.args.get('raw'):
        raw = True
    else:
        raw = False
    for view in base.views:
        url = base_url + '?view=' + view
        if raw:
            url = url + '&raw=1'
        all_views.append((view, url))

    result = base.views[key].make_view(vault, force_refresh=refresh)
    if base.views[key].type == 'cards':
        template_path = 'bases/card_view.html'
        if raw:
            template_path = 'bases/card_view_raw.html'
    elif base.views[key].type == 'table':
        template_path = 'bases/table_view.html'
        if raw:
            template_path = 'bases/table_view_raw.html'
    else:
        raise NotImplementedError(f'Unsupported type: {base.views[key].type}')
    return render_template(template_path,
                           table=result,
                           navtree=render_tree(Singleton.indices[vault], vault,
                                               False),
                           is_editor=False,
                           home=Singleton.config.vaults[vault].home_file,
                           curdir=Path(subpath).parent,
                           curfile=subpath,
                           vault=vault,
                           path=subpath,
                           current_view=current_view,
                           all_views=all_views)
