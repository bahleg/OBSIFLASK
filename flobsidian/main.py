import sys
from pathlib import Path
import datetime
import time

import flask
from flask import Flask
from flask import redirect, url_for, send_file
from os.path import abspath
from flask_bootstrap import Bootstrap5
from flask import request, session, redirect
from flask_wtf.csrf import CSRFProtect
import requests
from flask import Flask, request, Response, jsonify

from werkzeug.exceptions import default_exceptions
from flask_bootstrap import Bootstrap5

# from toolbox.front_flask.download import download, download_shared as download_shared_back
from flask import stream_with_context
from flobsidian.config import AppConfig
from flobsidian.consts import APP_NAME
from flobsidian.minihydra import load_entrypoint_config
from flobsidian.utils import init_logger
from flobsidian.pages.editor import render_editor
from flobsidian.pages.renderer import render_renderer, get_markdown
from flobsidian.pages.save import make_save
from flobsidian.tasks import run_tasks
import secrets
from flobsidian.singleton import Singleton
from flobsidian.file_index import FileIndex
from flobsidian.pages.index_tree import render_tree
from flobsidian.pages.messages import render_messages


def run():
    cfg: AppConfig = load_entrypoint_config(AppConfig)
    Singleton.config = cfg
    for vault in cfg.vaults:
        Singleton.messages[(vault, None)] = []
    run_tasks(cfg.tasks)
    logger = init_logger(cfg.log_path, log_level=cfg.log_level)
    logger.debug('initialization')
    for vault in cfg.vaults:
        Singleton.indices[vault] = FileIndex(cfg.vaults[vault].full_path)

    logger.debug('starting app')
    app = Flask(__name__,
                template_folder=abspath(Path(__file__).parent / "templates"),
                root_path=Path(__file__).parent)
    Bootstrap5(app)
    app.config["BOOTSTRAP_BOOTSWATCH_THEME"] = cfg.bootstrap_theme


    @app.template_filter('datetimeformat')
    def datetimeformat(value):
        return datetime.datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')


    @app.route('/edit/<vault>/<path:subpath>')
    def editor(vault, subpath):
        if vault not in cfg.vaults:
            return 'Bad vault', 404
        real_path = Path(cfg.vaults[vault].full_path) / subpath
        if not (real_path).exists():
            return 'Bad path', 404
        return render_editor(vault, subpath, real_path)

    @app.route('/render/<vault>/<path:subpath>')
    def renderer(vault, subpath):
        if vault not in cfg.vaults:
            return 'Bad vault', 404
        real_path = Path(cfg.vaults[vault].full_path) / subpath
        if not (real_path).exists():
            return 'Bad path', 404
        return render_renderer(vault, subpath, real_path)

    @app.route('/preview/<vault>/<path:subpath>')
    def preview(vault, subpath):
        if vault not in cfg.vaults:
            return 'Bad vault', 404
        real_path = Path(cfg.vaults[vault].full_path) / subpath
        if not (real_path).exists():
            return 'Bad path', 404
        markdown = get_markdown(real_path, Singleton.indices[vault])
        return jsonify({'content': markdown})

    @app.route('/save/<vault>/<path:subpath>', methods=['PUT'])
    def save_file(vault, subpath):
        if vault not in cfg.vaults:
            return 'Bad vault', 404
        real_path = Path(cfg.vaults[vault].full_path) / subpath
        data = request.get_json()
        content = data.get('content', '')
        return make_save(real_path, content, Singleton.indices[vault])

    @app.route('/tree/<vault>')
    def tree(vault):
        Singleton.indices[vault].refresh()
        return render_tree(Singleton.indices[vault], vault)

    @app.route('/messages/<vault>')
    def messages(vault):
        unread = request.args.get('unread', default='1')
        try:
            unread = int(unread)

        except:
            logger.warning(f'could not parse unread parameter: {unread}')
            unread = 1
        return render_messages(vault, unread)

    app.run(**cfg.flask_params)


if __name__ == "__main__":
    run()
