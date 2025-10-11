"""
A rendering nav tree logic
"""
from pathlib import Path

from flask import url_for, jsonify, request

from obsiflask.app_state import AppState


def get_menu(key: str, vault: str, is_dir: bool, tree_curfile: list[str],
             templates: list[str]) -> list[dict]:
    """
    Returns a context menu for the target file

    Args:
        key (str): file key in fancyTree
        vault (str): vault name
        is_dir (bool): directory of file
        tree_curfile ( list[str]): current file and directory from the point of view of tree
            For the tree_curfile == key we don't show rename and delete operations
            as they will require redirect
        templates (list[str]): list of templates

    Returns:
        list[dict]: list of menu elements.
        Each element has:
            - title
            - url
            - (optionally) mode: 'fastop' if we want to use service file operation api
            - (optionally) get_dst: true if we want to prompt the user for destination
            - (optionally) reload: true if we want to just reload tree and not go to the url
            - (optionally) check: if we want to ask the user the confirmation of the operation     
    """
    if is_dir:
        curdir_curfile = {'curdir': key}
    else:
        curfile = key
        if key.count('/') == 0:
            curdir = '.'
        else:
            curdir = key.rsplit('/', 1)[0]
        curdir_curfile = {'curdir': curdir, 'curfile': curfile}

    menu = []
    if is_dir:
        menu.append({
            'title': '📂 Open folder',
            'url': url_for('get_folder', vault=vault, subpath=key)
        })
        menu.append({
            'title':
            '📄 Create empty file',
            'url':
            url_for('fastfileop', vault=vault, op='file', **curdir_curfile),
            'mode':
            'fastop',
            'get_dst':
            True,
        })
        menu.append({
            'title':
            '🗁 Create new folder',
            'url':
            url_for('fastfileop', vault=vault, op='folder', **curdir_curfile),
            'mode':
            'fastop',
            'get_dst':
            True,
        })
        for t in templates:
            menu.append({
                'title':
                f'📃 New file from {t.name}',
                'url':
                url_for('fastfileop',
                        vault=vault,
                        op='template',
                        **curdir_curfile,
                        template=str(t)),
                'mode':
                'fastop',
                'get_dst':
                True
            })

    else:
        if key.endswith(('.md', '.excalidraw')):
            menu.append({
                'title': '👁️ Show',
                'url': url_for('renderer', vault=vault, subpath=key)
            })
            menu.append({
                'title': '✏️ Edit',
                'url': url_for('editor', vault=vault, subpath=key)
            })
        menu.append({
            'title': '📥 Download',
            'url': url_for('get_file', vault=vault, subpath=key)
        })
        if AppState.config.vaults[vault].obfuscation_suffix in Path(
                key).suffixes:
            menu.append({
                'title':
                '🥸 Download w.r.t. obfuscation',
                'url':
                url_for('get_file', vault=vault, subpath=key, obfuscate=1)
            })

    menu.append({
        'title':
        '🗐 Duplicate',
        'url':
        url_for('fastfileop', vault=vault, op='copy', **curdir_curfile),
        'mode':
        'fastop',
        'get_dst':
        True
    })
    if key not in tree_curfile:
        menu.append({
            'title':
            '→ Rename',
            'url':
            url_for('fastfileop', vault=vault, op='move', **curdir_curfile),
            'mode':
            'fastop',
            'get_dst':
            True
        })

        menu.append({
            'title':
            '🗑️ Delete',
            'url':
            url_for('fastfileop', vault=vault, op='delete', **curdir_curfile),
            'mode':
            'fastop',
            'check':
            True,
            'reload':
            True
        })

    menu.append({
        'title': '🗃️ File operations...',
        'url': url_for('fileop', vault=vault, **curdir_curfile)
    })

    return menu


def get_tree_items(tree: dict, items: list, subpath_rel: Path, vault: str,
                   tree_curfile: set[str], templates: str, edit: bool,
                   request_subpath: Path) -> list | None:
    """
    Helper to build an index tree

    Args:
        tree (dict): tree from FileIndex
        items (list): item buffer to populate
        subpath_rel (Path): relative subpath, w.r.t. tree
        vault (str): vault name
        tree_curfile (set[str]): current file in the tree
        templates (str): path to templates
        edit (bool): bool flag if we are in editor mode
        request_subpath (Path): original subpath (w.r.t. real filesystem)

    returns list of children or None (it couldn't find element to add children)
    """
    result = None
    if tree is not None:
        for name, child in sorted(tree.items(),
                                  key=lambda x: (x[1] is None, x[0])):
            key = str(subpath_rel / name.name)
            is_dir = child is not None
            if is_dir:
                lazy = not (request_subpath.is_relative_to(name))
                items.append({
                    "title": f"{name.name}",
                    "folder": True,
                    "lazy": name.is_dir() and lazy,
                    "key": key,
                    "data": {
                        'menu': get_menu(key, vault, True, tree_curfile,
                                         templates)
                    }
                })
                if not lazy:
                    items[-1]['expanded'] = True
                    items[-1]['children'] = []
                    result = items[-1]['children']
            else:
                if edit:
                    url = url_for('editor', vault=vault, subpath=key)
                else:
                    url = url_for('renderer', vault=vault, subpath=key)
                menu = get_menu(key, vault, False, tree_curfile, templates)
                items.append({
                    "title": f"{name.name}",
                    "key": key,
                    "data": {
                        'url': url,
                        'menu': menu
                    }
                })
    return result


def render_tree(vault: str, subpath: str) -> str:
    """
    A function for rendering part of the tree

    Args:
        vault (str): vault name
        subpath (str): subpath to analyze 

    Returns:
        str: json with tree elements for FancyTree
    """
    is_global = request.args.get('global')
    templates = AppState.indices[vault].get_templates()
    edit = str(request.args.get('edit', '0')).lower() not in ['0', '', 'false']
    curfile = request.args.get('curfile')
    curdir = request.args.get('curdir')
    items = []
    tree = AppState.indices[vault].get_tree()
    is_root = subpath == ''
    subpath = Path(AppState.indices[vault].path / subpath).resolve()
    request_path = Path(subpath)
    subpath_rel = subpath.relative_to(AppState.indices[vault].path)
    tree = tree[AppState.indices[vault].path]
    tree_curfile = set([curfile, curdir])

    if is_root or is_global:
        key = '.'
        # adding root node
        items.append({
            "title": '<ROOT>',
            "folder": True,
            "lazy": False,
            "key": key,
            "data": {
                'menu': get_menu(key, vault, True, tree_curfile, templates)
            }
        })
    children = None
    if is_global:
        children = get_tree_items(tree, items, Path(''), vault, tree_curfile,
                                  templates, edit, request_path)
        if children is None:
            children = items
    # go to the the subpath element
    global_subpath = Path('')

    for part in list(subpath_rel.parents)[::-1][1:]:
        global_subpath = part
        tree = tree[AppState.indices[vault].path / part]
        if is_global:
            children = get_tree_items(tree, children, global_subpath, vault,
                                      tree_curfile, templates, edit,
                                      request_path)
            if children is None:
                children = items
    if not is_root:
        tree = tree[subpath]
    if children is None:
        children = items
    if (is_root and not is_global) or not is_root:
        get_tree_items(tree, children, subpath_rel, vault, tree_curfile,
                       templates, edit, request_path)
    return jsonify(items)
