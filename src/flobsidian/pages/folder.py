from flask import abort
from pathlib import Path
from flask import render_template, redirect, url_for
from flobsidian.pages.renderer import get_markdown
from flobsidian.pages.index_tree import render_tree
from flobsidian.singleton import Singleton
from flobsidian.utils import logger


def render_folder(vault, subpath):
    navtree = render_tree(Singleton.indices[vault], vault, True)
    abspath = Singleton.indices[vault].path.absolute().resolve()
    target = (abspath / subpath).resolve()
    if  abspath != target and not abspath in list(target.parents):
        return abort(402)

    files_folders = Path(abspath / subpath).absolute().glob('*')
    folders = []
    files = []
    for f in files_folders:
        if not f.is_dir():
            files.append((str(f.relative_to(abspath)), f.name))
        else:
            folders.append((str(f.relative_to(abspath)), f.name))
        
    return render_template('folder.html',
                           subpath=subpath,
                           navtree=navtree,
                           files=files,
                           folders=folders,
                           home=Singleton.config.vaults[vault].home_file,
                           vault=vault)
