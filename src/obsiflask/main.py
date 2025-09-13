from pathlib import Path
import datetime
import logging
from os.path import abspath

from flask import Flask, request, jsonify, redirect, url_for
from flask_bootstrap import Bootstrap5
from flask_favicon import FlaskFavicon

from obsiflask.config import AppConfig
from obsiflask.minihydra import load_entrypoint_config
from obsiflask.utils import init_logger
from obsiflask.pages.editor import render_editor
from obsiflask.pages.file import get_file as page_get_file
from obsiflask.pages.index import render_index
from obsiflask.pages.renderer import render_renderer, get_markdown
from obsiflask.pages.save import make_save
from obsiflask.tasks import run_tasks
from obsiflask.app_state import AppState
from obsiflask.file_index import FileIndex
from obsiflask.pages.index_tree import render_tree
from obsiflask.pages.messages import render_messages
from obsiflask.pages.excalidraw import render_excalidraw
from obsiflask.pages.folder import render_folder
from obsiflask.pages.fileop import render_fileop
from obsiflask.pages.base import render_base
from obsiflask.graph import Graph
from obsiflask.pages.graph import render_graph
from obsiflask.pages.search import render_search


def check_vault(vault: str) -> tuple[str, int] | None:
    """
    Checks if the vault exists    

    Args:
        vault (str): vault name

    Returns:
        tuple[str, int] | None: flask-formatted return or None
    """
    cfg = AppState.config
    if vault not in cfg.vaults:
        return "Bad vault", 400
    return None


def resolve_path(vault: str, subpath: str) -> Path | tuple[str, int]:
    """
    Resolves path w.r.t. to application

    Args:
        vault (str): vault name
        subpath (str): path relative to vault

    Returns:
        Path | tuple[str, int]: flask-formatted return or absolute path 
    """
    vault_resolution_result = check_vault(vault)
    if vault_resolution_result is not None:
        return vault_resolution_result

    cfg = AppState.config
    real_path = (Path(cfg.vaults[vault].full_path) / subpath).resolve()
    if not real_path.exists():
        return f"Bad path: {subpath}", 400
    return real_path


def run(cfg: AppConfig | None, return_app: bool = False) -> Flask:
    """
    Main application entrypoint
    

    Args:
        cfg (AppConfig, optional): application config. If not set, will use arguments to load config from system
        return_app (bool, optional): returns application without running. Defaults to False.

    Returns:
        Flask: flask application
    """
    # Config and logger initialization
    if cfg is None:
        cfg: AppConfig = load_entrypoint_config(AppConfig)
    AppState.config = cfg
    for vault in cfg.vaults:
        AppState.messages[(vault, None)] = []
    logger = init_logger(cfg.log_path, log_level=cfg.log_level)
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    logger.debug('initialization')

    # app resources
    run_tasks({vault: cfg.vaults[vault].tasks for vault in cfg.vaults})
    for vault in cfg.vaults:
        AppState.indices[vault] = FileIndex(cfg.vaults[vault].full_path,
                                            cfg.vaults[vault].template_dir,
                                            vault)
        AppState.graphs[vault] = Graph(vault)
    AppState.inject_vars()

    # Flask confguration
    logger.debug('starting app')
    app = Flask(__name__,
                template_folder=abspath(Path(__file__).parent / "templates"),
                root_path=Path(__file__).parent)
    flaskFavicon = FlaskFavicon()
    flaskFavicon.init_app(app)
    flaskFavicon.register_favicon(
        str(Path(__file__).resolve().parent / 'static/logo.png'), 'default')

    Bootstrap5(app)

    app.config['WTF_CSRF_ENABLED'] = False
    app.config[
        "BOOTSTRAP_BOOTSWATCH_THEME"] = cfg.default_user_config.bootstrap_theme

    @app.context_processor
    def inject_service_vars():
        return {'injected_vars': AppState.injected_vars_jinja}

    @app.template_filter('datetimeformat')
    def datetimeformat(value):
        return datetime.datetime.fromtimestamp(value).strftime(
            '%Y-%m-%d %H:%M:%S')

    @app.route('/edit/<vault>/<path:subpath>')
    def editor(vault, subpath):
        real_path = resolve_path(vault, subpath)
        if isinstance(real_path, tuple):
            return real_path
        return render_editor(vault, subpath, real_path)

    @app.route('/editor/<vault>')
    def editor_root(vault):
        vault_resolution_result = check_vault(vault)
        if vault_resolution_result:
            return vault_resolution_result
        if cfg.vaults[vault].home_file:
            return redirect(
                url_for('editor',
                        vault=vault,
                        subpath=cfg.vaults[vault].home_file))
        else:
            return redirect(url_for('get_folder_root', vault=vault))

    @app.route('/excalidraw/<vault>/<path:subpath>')
    def excalidraw(vault, subpath):
        real_path = resolve_path(vault, subpath)
        if isinstance(real_path, tuple):
            return real_path
        return render_excalidraw(vault, subpath, real_path)

    @app.route('/renderer/<vault>/<path:subpath>')
    def renderer(vault, subpath):
        real_path = resolve_path(vault, subpath)
        if isinstance(real_path, tuple):
            return real_path
        return render_renderer(vault, subpath, real_path)

    @app.route('/base/<vault>/<path:subpath>')
    def base(vault, subpath):
        real_path = resolve_path(vault, subpath)
        if isinstance(real_path, tuple):
            return real_path
        return render_base(vault, subpath, real_path)

    @app.route('/renderer/<vault>')
    def renderer_root(vault):
        vault_resolution_result = check_vault(vault)
        if vault_resolution_result:
            return vault_resolution_result
        if cfg.vaults[vault].home_file:
            return redirect(
                url_for('renderer',
                        vault=vault,
                        subpath=cfg.vaults[vault].home_file))
        else:
            return redirect(url_for('get_folder_root', vault=vault))

    @app.route('/preview/<vault>/<path:subpath>')
    def preview(vault, subpath):
        real_path = resolve_path(vault, subpath)
        if isinstance(real_path, tuple):
            return real_path
        markdown = get_markdown(real_path, AppState.indices[vault], vault)
        return jsonify({'content': markdown})

    @app.route('/save/<vault>/<path:subpath>', methods=['PUT'])
    def save_file(vault, subpath):
        real_path = resolve_path(vault, subpath)
        if isinstance(real_path, tuple):
            return real_path
        data = request.get_json()
        content = data.get('content', '')
        return make_save(real_path, content, AppState.indices[vault], vault)

    @app.route('/file/<vault>/<path:subpath>')
    def get_file(vault, subpath):
        real_path = resolve_path(vault, subpath)
        if isinstance(real_path, tuple):
            return real_path
        return page_get_file(real_path)

    @app.route('/folder/<vault>/<path:subpath>')
    def get_folder(vault, subpath):
        real_path = resolve_path(vault, subpath)
        if isinstance(real_path, tuple):
            return real_path
        return render_folder(vault, subpath)

    @app.route('/renderer/<vault>/')
    @app.route('/folder/<vault>')
    @app.route('/folder/<vault>/')
    def get_folder_root(vault):
        vault_resolution_result = check_vault(vault)
        if vault_resolution_result:
            return vault_resolution_result
        return render_folder(vault, '.')

    @app.route('/static/<path:subpath>')
    def get_static(vault, subpath):
        real_path = resolve_path(vault, subpath)
        if isinstance(real_path, tuple):
            return real_path
        return page_get_file(real_path)

    @app.route('/')
    def index():
        return render_index()

    @app.route('/tree/<vault>')
    def tree(vault):
        AppState.indices[vault].refresh()
        return render_tree(AppState.indices[vault], vault)

    @app.route('/graph/<vault>')
    def graph(vault):
        return render_graph(vault)

    @app.route('/search/<vault>')
    def search(vault):
        return render_search(vault)

    @app.route('/messages/<vault>')
    def messages(vault):
        unread = request.args.get('unread', default='1')
        raw = request.args.get('raw', default='0')
        try:
            unread = int(unread)
        except Exception as e:
            logger.warning(f'could not parse unread parameter: {unread}: {e}')
            unread = 1

        try:
            raw = int(raw)
        except Exception as e:
            logger.warning(f'could not parse raw parameter: {raw}: {e}')
            raw = 0
        return render_messages(vault, unread, raw=raw)

    @app.route('/fileop/<vault>', methods=['GET', 'POST'])
    def fileop(vault):
        return render_fileop(vault)

    if return_app:
        return app
    # Run
    app.run(**cfg.flask_params)


if __name__ == "__main__":
    run()
