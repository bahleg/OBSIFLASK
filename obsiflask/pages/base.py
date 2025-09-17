"""
Base rendering logic
"""
from pathlib import Path

from flask import render_template, url_for, request

from obsiflask.app_state import AppState
from obsiflask.bases.base_parser import parse_base
from obsiflask.pages.index_tree import render_tree


def render_base_view(vault: str, subpath: str, real_path: str) -> str:
    """
    Rendering logic

    Args:
        vault (str): vault name
        subpath (str): path to base
        real_path (str): real path to base

    Returns:
        str: rendered html
    """
    base = parse_base(real_path, vault)
    view = request.args.get('view')
    if view is None:
        key = list(base.views.keys())[0]
    else:
        if view not in base.views.keys():
            return f'Bad view: {view}', 400
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
                           navtree=render_tree(AppState.indices[vault], vault,
                                               False),
                           is_editor=False,
                           home=AppState.config.vaults[vault].home_file,
                           curdir=Path(subpath).parent,
                           curfile=subpath,
                           vault=vault,
                           path=subpath,
                           current_view=current_view,
                           all_views=all_views)
