from pathlib import Path
import datetime
import logging
from flask import Flask
from flask import redirect, url_for
from os.path import abspath
from flask_bootstrap import Bootstrap5
from flask import request, redirect
from flask import Flask, request, jsonify
from flask_wtf.csrf import CSRFProtect
import uuid
from flask_bootstrap import Bootstrap5

# from toolbox.front_flask.download import download, download_shared as download_shared_back
from flobsidian.config import AppConfig
from flobsidian.minihydra import load_entrypoint_config
from flobsidian.utils import init_logger
from flobsidian.pages.editor import render_editor
from flobsidian.pages.file import get_file as page_get_file
from flobsidian.pages.index import render_index
from flobsidian.pages.renderer import render_renderer, get_markdown
from flobsidian.pages.save import make_save
from flobsidian.tasks import run_tasks
from flobsidian.singleton import Singleton
from flobsidian.file_index import FileIndex
from flobsidian.pages.index_tree import render_tree
from flobsidian.pages.messages import render_messages
from flobsidian.pages.excalidraw import render_excalidraw
from flobsidian.pages.folder import render_folder
from flobsidian.pages.fileop import render_fileop

def run():
    cfg: AppConfig = load_entrypoint_config(AppConfig)
    Singleton.config = cfg
    for vault in cfg.vaults:
        Singleton.messages[(vault, None)] = []
    run_tasks(cfg.tasks)
    logger = init_logger(cfg.log_path, log_level=cfg.log_level)
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    logger.debug('initialization')
    for vault in cfg.vaults:
        Singleton.indices[vault] = FileIndex(cfg.vaults[vault].full_path)

    logger.debug('starting app')
    app = Flask(__name__,
                template_folder=abspath(Path(__file__).parent / "templates"),
                root_path=Path(__file__).parent)
    Bootstrap5(app)

    app.config['SECRET_KEY'] = uuid.uuid4().hex
    CSRFProtect(app)
    app.config["BOOTSTRAP_BOOTSWATCH_THEME"] = cfg.bootstrap_theme

    @app.context_processor
    def inject_service_vars():
        return {'injected_vars': Singleton.injected_vars_jinja}

    @app.template_filter('datetimeformat')
    def datetimeformat(value):
        return datetime.datetime.fromtimestamp(value).strftime(
            '%Y-%m-%d %H:%M:%S')

    @app.route('/edit/<vault>/<path:subpath>')
    def editor(vault, subpath):
        if vault not in cfg.vaults:
            return 'Bad vault', 404
        real_path = (Path(cfg.vaults[vault].full_path) / subpath).resolve()
        if not (real_path).exists():
            return 'Bad path', 404
        return render_editor(vault, subpath, real_path)

    @app.route('/editor/<vault>')
    def editor_root(vault):
        if vault not in cfg.vaults:
            return 'Bad vault', 404
        if cfg.vaults[vault].home_file:
            return redirect(
                url_for('editor',
                        vault=vault,
                        subpath=cfg.vaults[vault].home_file))
        else:
            first_file = Singleton.indices[vault][0]
            return redirect(
                url_for('editor',
                        vault=vault,
                        subpath=str(
                            Path(first_file).relative_to(
                                Singleton.indices[vault].path))))

    @app.route('/excalidraw/<vault>/<path:subpath>')
    def excalidraw(vault, subpath):
        if vault not in cfg.vaults:
            return 'Bad vault', 404
        real_path = (Path(cfg.vaults[vault].full_path) / subpath).resolve()
        if not (real_path).exists():
            return 'Bad path', 404
        return render_excalidraw(vault, subpath, real_path)


    @app.route('/render/<vault>/<path:subpath>')
    def renderer(vault, subpath):
        if vault not in cfg.vaults:
            return 'Bad vault', 404
        real_path = (Path(cfg.vaults[vault].full_path) / subpath).resolve()
        if not (real_path).exists():
            return 'Bad path', 404
        return render_renderer(vault, subpath, real_path)

    @app.route('/render/<vault>')
    def renderer_root(vault):
        if vault not in cfg.vaults:
            return 'Bad vault', 404
        if cfg.vaults[vault].home_file:
            return redirect(
                url_for('renderer',
                        vault=vault,
                        subpath=cfg.vaults[vault].home_file))
        else:
            first_file = Singleton.indices[vault][0]
            return redirect(
                url_for('renderer',
                        vault=vault,
                        subpath=str(
                            Path(first_file).relative_to(
                                Singleton.indices[vault].path))))

    @app.route('/preview/<vault>/<path:subpath>')
    def preview(vault, subpath):
        if vault not in cfg.vaults:
            return 'Bad vault', 404
        real_path = (Path(cfg.vaults[vault].full_path) / subpath).resolve()
        if not (real_path).exists():
            return 'Bad path', 404
        markdown = get_markdown(real_path, Singleton.indices[vault])
        return jsonify({'content': markdown})

    @app.route('/save/<vault>/<path:subpath>', methods=['PUT'])
    def save_file(vault, subpath):
        if vault not in cfg.vaults:
            return 'Bad vault', 404
        real_path = (Path(cfg.vaults[vault].full_path) / subpath).resolve()
        data = request.get_json()
        content = data.get('content', '')
        return make_save(real_path, content, Singleton.indices[vault], vault)

    @app.route('/file/<vault>/<path:subpath>')
    def get_file(vault, subpath):
        if vault not in cfg.vaults:
            return 'Bad vault', 404
        real_path = Path(cfg.vaults[vault].full_path).absolute() / subpath
        return page_get_file(real_path)

    @app.route('/folder/<vault>/<path:subpath>')
    def get_folder(vault, subpath):
        if vault not in cfg.vaults:
            return 'Bad vault', 404
        return render_folder(vault, subpath)



    @app.route('/folder/<vault>')
    def get_folder_root(vault):
        if vault not in cfg.vaults:
            return 'Bad vault', 404
        return render_folder(vault, '.')


    @app.route('/static/<path:subpath>')
    def get_static(vault, subpath):
        if vault not in cfg.vaults:
            return 'Bad vault', 404
        real_path = (Path(__name__).parent/'static').absolute() / subpath
        return page_get_file(real_path)

    @app.route('/')
    def index():
        return render_index()

    @app.route('/tree/<vault>')
    def tree(vault):
        Singleton.indices[vault].refresh()
        return render_tree(Singleton.indices[vault], vault)

    @app.route('/messages/<vault>')
    def messages(vault):
        unread = request.args.get('unread', default='1')
        raw = request.args.get('raw', default='0')
        try:
            unread = int(unread)
        except:
            logger.warning(f'could not parse unread parameter: {unread}')
            unread = 1

        try:
            raw = int(raw)
        except:
            logger.warning(f'could not parse raw parameter: {raw}')
            raw = 0
        return render_messages(vault, unread, raw=raw)
    

    @app.route('/fileop/<vault>')
    def fileop(vault):
        return render_fileop(vault)
    
    app.run(**cfg.flask_params)

if __name__ == "__main__":
    run()
